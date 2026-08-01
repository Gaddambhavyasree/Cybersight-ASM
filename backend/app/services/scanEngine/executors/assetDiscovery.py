import logging
from app.models.scan import ScanStage
from app.services.scanEngine.executors.base import BaseStageExecutor
from app.services.subfinder.subfinderRunner import run_subfinder
from app.services.subfinder.subfinderParser import parse_subfinder_output, clean_domains
from app.services.asset_service import save_assets
from app.services.scanEngine.logger import log_event

logger = logging.getLogger(__name__)


class AssetDiscoveryExecutor(BaseStageExecutor):
    def __init__(self):
        super().__init__(stage=ScanStage.ASSET_DISCOVERY, simulated_delay=0)

    async def execute(self, scan_id: str, target: str, db) -> dict:
        logger.info(f"[{scan_id}] Asset Discovery started against: {target}")

        log_entries = [
            log_event("Asset Discovery started", "info"),
            log_event(f"Running Subfinder against: {target}", "info"),
        ]
        await db.scans.update_one(
            {"_id": __import__("bson").ObjectId(scan_id)},
            {"$push": {"logs": {"$each": log_entries}}},
        )

        result = await run_subfinder(target)

        if result["status"] == "error":
            error_msg = result.get("message", "Subfinder execution failed")
            logger.error(f"[{scan_id}] Subfinder failed: {error_msg}")

            fail_log = log_event(f"Subfinder failed: {error_msg}", "error")
            await db.scans.update_one(
                {"_id": __import__("bson").ObjectId(scan_id)},
                {"$push": {"logs": fail_log}},
            )

            return {
                "status": "error",
                "stage": self.stage.value,
                "message": error_msg,
            }

        raw_domains = parse_subfinder_output(result["output"])
        domains = clean_domains(raw_domains)

        count_log = log_event(f"Discovered {len(domains)} subdomains", "info")
        await db.scans.update_one(
            {"_id": __import__("bson").ObjectId(scan_id)},
            {"$push": {"logs": count_log}},
        )

        scan = await db.scans.find_one({"_id": __import__("bson").ObjectId(scan_id)})
        project_id = scan.get("project_id", "") if scan else ""

        if domains and project_id:
            save_result = await save_assets(
                db=db,
                project_id=project_id,
                scan_id=scan_id,
                hostnames=domains,
                source="Subfinder",
            )

            save_log = log_event(
                f"Saved {save_result['new_count']} new assets, updated {save_result['updated_count']} existing",
                "info",
            )
            await db.scans.update_one(
                {"_id": __import__("bson").ObjectId(scan_id)},
                {
                    "$push": {"logs": save_log},
                    "$set": {"assets_count": save_result["new_count"]},
                },
            )
        else:
            no_assets_log = log_event("No new subdomains discovered", "info")
            await db.scans.update_one(
                {"_id": __import__("bson").ObjectId(scan_id)},
                {
                    "$push": {"logs": no_assets_log},
                    "$set": {"assets_count": 0},
                },
            )

        logger.info(f"[{scan_id}] Asset Discovery completed: {len(domains)} subdomains")
        return {
            "status": "success",
            "stage": self.stage.value,
            "message": f"Discovered {len(domains)} subdomains",
            "data": {"domains": domains, "count": len(domains)},
        }
