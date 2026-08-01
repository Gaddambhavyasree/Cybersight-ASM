import logging
from datetime import datetime
from bson import ObjectId
from app.models.scan import ScanStage
from app.services.scanEngine.executors.base import BaseStageExecutor
from app.services.httpx_runner.runner import _find_httpx, run_httpx_single, _offline_result
from app.services.scanEngine.logger import log_event

logger = logging.getLogger(__name__)


class LiveHostVerificationExecutor(BaseStageExecutor):
    def __init__(self):
        super().__init__(stage=ScanStage.LIVE_HOST_DETECTION, simulated_delay=0)

    async def execute(self, scan_id: str, target: str, db) -> dict:
        logger.info(f"[{scan_id}] Live Host Verification started for: {target}")

        httpx_path = _find_httpx()
        if not httpx_path:
            error_msg = "httpx executable not found. Install: go install github.com/projectdiscovery/httpx/cmd/httpx@latest"
            logger.error(f"[{scan_id}] {error_msg}")
            fail_log = log_event(error_msg, "error")
            await db.scans.update_one(
                {"_id": ObjectId(scan_id)},
                {"$push": {"logs": fail_log}},
            )
            return {"status": "error", "stage": self.stage.value, "message": error_msg}

        scan = await db.scans.find_one({"_id": ObjectId(scan_id)})
        project_id = scan.get("project_id", "") if scan else ""

        cursor = db.assets.find({"project_id": project_id, "scan_id": scan_id})
        assets = await cursor.to_list(length=1000)

        if not assets:
            log_entries = [
                log_event("Live Host Verification started", "info"),
                log_event("No assets to verify", "info"),
            ]
            await db.scans.update_one(
                {"_id": ObjectId(scan_id)},
                {"$push": {"logs": {"$each": log_entries}}},
            )
            return {
                "status": "success",
                "stage": self.stage.value,
                "message": "No assets to verify",
                "data": {"live": 0, "offline": 0},
            }

        hostnames = [a["hostname"] for a in assets]
        total = len(hostnames)

        start_logs = [
            log_event("Live Host Verification started", "info"),
            log_event(f"Running HTTPX against {total} assets", "info"),
        ]
        await db.scans.update_one(
            {"_id": ObjectId(scan_id)},
            {"$push": {"logs": {"$each": start_logs}}},
        )

        live_count = 0
        offline_count = 0

        for hostname in hostnames:
            try:
                result = run_httpx_single(hostname, httpx_path, timeout=15)
            except FileNotFoundError:
                error_msg = "httpx executable disappeared during scan"
                logger.error(f"[{scan_id}] {error_msg}")
                fail_log = log_event(error_msg, "error")
                await db.scans.update_one(
                    {"_id": ObjectId(scan_id)},
                    {"$push": {"logs": fail_log}},
                )
                return {"status": "error", "stage": self.stage.value, "message": error_msg}
            except Exception as e:
                logger.warning(f"[{scan_id}] httpx failed for {hostname}: {e}")
                result = _offline_result(hostname)

            is_live = result.get("is_live", False)
            status_label = "Live" if is_live else "Offline"
            status_code = result.get("http_status", "")
            status_str = f" ({status_code})" if status_code else ""
            log_msg = f"{hostname} -> {status_label}{status_str}"

            log_entries = [
                log_event(log_msg, "info" if is_live else "warning"),
            ]

            update_fields = {
                "is_live": is_live,
                "last_http_check": result.get("last_http_check"),
                "updated_at": datetime.utcnow(),
            }

            if is_live:
                for field in ["ip", "http_status", "https_enabled", "final_url",
                              "page_title", "web_server", "content_length",
                              "response_time", "redirect_location"]:
                    if result.get(field) is not None:
                        update_fields[field] = result[field]
                live_count += 1
            else:
                update_fields["http_status"] = None
                update_fields["is_live"] = False
                offline_count += 1

            await db.assets.update_one(
                {"project_id": project_id, "hostname": hostname},
                {"$set": update_fields},
            )

            await db.scans.update_one(
                {"_id": ObjectId(scan_id)},
                {"$push": {"logs": {"$each": log_entries}}},
            )

        summary_logs = [
            log_event("HTTPX completed", "info"),
            log_event(f"Updated {live_count} live assets, {offline_count} offline assets", "info"),
        ]
        await db.scans.update_one(
            {"_id": ObjectId(scan_id)},
            {"$push": {"logs": {"$each": summary_logs}}},
        )

        logger.info(f"[{scan_id}] Live Host Verification completed: {live_count} live, {offline_count} offline")
        return {
            "status": "success",
            "stage": self.stage.value,
            "message": f"Verified {total} assets: {live_count} live, {offline_count} offline",
            "data": {"live": live_count, "offline": offline_count, "total": total},
        }
