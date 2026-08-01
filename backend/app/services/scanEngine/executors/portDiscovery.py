import logging
from datetime import datetime

from bson import ObjectId

from app.models.scan import ScanStage
from app.services.naabu_runner.runner import _find_naabu, run_naabu_single
from app.services.scanEngine.executors.base import BaseStageExecutor
from app.services.scanEngine.logger import log_event

logger = logging.getLogger(__name__)


class PortDiscoveryExecutor(BaseStageExecutor):
    def __init__(self):
        super().__init__(stage=ScanStage.PORT_SCANNING, simulated_delay=0)

    async def execute(self, scan_id: str, target: str, db) -> dict:
        """Scan only verified live assets and always return a terminal result."""
        logger.info("[%s] Starting Port Discovery for %s", scan_id, target)
        try:
            naabu_path = _find_naabu()
            if not naabu_path:
                message = "naabu executable not found. Install: go install github.com/projectdiscovery/naabu/v2/cmd/naabu@latest"
                logger.error("[%s] %s", scan_id, message)
                await self._append_logs(db, scan_id, [log_event(message, "error")])
                return self._error(message)

            logger.info("[%s] Naabu detected at %s", scan_id, naabu_path)
            scan = await db.scans.find_one({"_id": ObjectId(scan_id)})
            if not scan:
                return self._error("Scan record not found for Port Discovery")

            project_id = scan["project_id"]
            logger.info("[%s] Reading live assets", scan_id)
            assets = await db.assets.find({
                "project_id": project_id,
                "is_live": True,
            }).to_list(length=1000)
            logger.info("[%s] Scanning %s live assets", scan_id, len(assets))

            if not assets:
                await self._append_logs(db, scan_id, [
                    log_event("Port Discovery started", "info"),
                    log_event("No live assets to scan", "info"),
                    log_event("Port Discovery completed", "info"),
                ])
                logger.info("[%s] Port Discovery Finished; Returning Success", scan_id)
                return self._success("No live assets to scan", 0, 0)

            await self._append_logs(db, scan_id, [
                log_event("Port Discovery started", "info"),
                log_event(f"Scanning {len(assets)} live assets", "info"),
            ])

            saved_ports = 0
            for asset in assets:
                saved_ports += await self._scan_asset(
                    db, scan_id, project_id, asset, naabu_path
                )

            logger.info("[%s] Saving Port Discovery completion logs", scan_id)
            await self._append_logs(db, scan_id, [
                log_event("Naabu completed", "info"),
                log_event(f"Saved {saved_ports} open ports", "info"),
                log_event("Port Discovery completed", "info"),
            ])
            logger.info("[%s] Port Discovery Finished; Returning Success", scan_id)
            return self._success(
                f"Scanned {len(assets)} assets, saved {saved_ports} open ports",
                saved_ports,
                len(assets),
            )
        except Exception as exc:
            message = f"Port Discovery failed: {type(exc).__name__}: {exc}"
            logger.exception("[%s] %s", scan_id, message)
            try:
                await self._append_logs(db, scan_id, [log_event(message, "error")])
            except Exception:
                logger.exception("[%s] Could not save Port Discovery failure log", scan_id)
            logger.info("[%s] Returning Error", scan_id)
            return self._error(message)

    async def _scan_asset(self, db, scan_id: str, project_id: str, asset: dict, naabu_path: str) -> int:
        """Keep one host failure from affecting the rest of the stage."""
        hostname = asset.get("hostname", "<unknown>")
        asset_id = str(asset.get("_id", ""))
        logger.info("[%s] Running Naabu for %s", scan_id, hostname)
        await self._append_logs(db, scan_id, [log_event(f"Running Naabu for {hostname}", "info")])
        try:
            results = await run_naabu_single(hostname, naabu_path, timeout=60)
        except FileNotFoundError:
            # A missing binary cannot be recovered for the remaining hosts.
            message = "naabu executable disappeared during scan"
            logger.error("[%s] %s", scan_id, message)
            await self._append_logs(db, scan_id, [log_event(message, "error")])
            raise FileNotFoundError(message)
        except Exception as exc:
            logger.exception("[%s] Naabu failed for %s", scan_id, hostname)
            await self._append_logs(db, scan_id, [log_event(f"Naabu failed for {hostname}: {exc}", "error")])
            results = []

        # Normalize and de-duplicate output before logging and storage. Invalid
        # lines are ignored here so one malformed result cannot stop the stage.
        normalized = []
        seen = set()
        for item in results or []:
            try:
                port = int(item.get("port"))
                if not 1 <= port <= 65535:
                    continue
                protocol = str(item.get("protocol") or "tcp").lower()
                key = (port, protocol)
                if key not in seen:
                    seen.add(key)
                    normalized.append({**item, "port": port, "protocol": protocol})
            except (AttributeError, TypeError, ValueError):
                logger.warning("[%s] Invalid Naabu result for %s: %r", scan_id, hostname, item)
        results = sorted(normalized, key=lambda item: item["port"])
        port_list = ",".join(str(item["port"]) for item in results)
        await self._append_logs(db, scan_id, [log_event(
            f"{hostname} -> {port_list}" if port_list else f"{hostname} -> No open ports",
            "info",
        )])

        now = datetime.utcnow()
        saved = 0
        for result in results:
            try:
                port = int(result["port"])
                protocol = str(result.get("protocol") or "tcp").lower()
                logger.info("[%s] Saving port %s/%s for %s", scan_id, port, protocol, hostname)
                await db.ports.update_one(
                    {"project_id": project_id, "asset_id": asset_id, "port": port, "protocol": protocol},
                    {"$setOnInsert": {"first_seen": now, "created_at": now}, "$set": {
                        "scan_id": scan_id,
                        "hostname": hostname,
                        "ip": result.get("ip") or asset.get("ip"),
                        "state": "open",
                        "service": result.get("service"),
                        "last_seen": now,
                        "updated_at": now,
                    }},
                    upsert=True,
                )
                saved += 1
            except (KeyError, TypeError, ValueError) as exc:
                logger.warning("[%s] Invalid Naabu result for %s: %s", scan_id, hostname, exc)
                await self._append_logs(db, scan_id, [log_event(f"Invalid port result for {hostname}: {exc}", "error")])
            except Exception as exc:
                logger.exception("[%s] Failed saving port for %s", scan_id, hostname)
                await self._append_logs(db, scan_id, [log_event(f"Failed to save port for {hostname}: {exc}", "error")])

        logger.info("[%s] Updating asset port summary for %s", scan_id, hostname)
        try:
            count = await db.ports.count_documents({"project_id": project_id, "asset_id": asset_id})
            await db.assets.update_one({"_id": asset["_id"]}, {"$set": {
                "open_ports_count": count,
                "last_port_scan": now,
                "updated_at": now,
            }})
        except Exception as exc:
            logger.exception("[%s] Failed updating asset %s", scan_id, hostname)
            await self._append_logs(db, scan_id, [log_event(f"Failed to update {hostname} port count: {exc}", "error")])
        return saved

    def _success(self, message: str, total_ports: int, assets_scanned: int) -> dict:
        return {"status": "success", "stage": self.stage.value, "message": message,
                "data": {"total_ports": total_ports, "assets_scanned": assets_scanned}}

    def _error(self, message: str) -> dict:
        return {"status": "error", "stage": self.stage.value, "message": message}

    @staticmethod
    async def _append_logs(db, scan_id: str, entries: list[dict]) -> None:
        """Await log persistence so no operation runs ahead of its database write."""
        await db.scans.update_one(
            {"_id": ObjectId(scan_id)}, {"$push": {"logs": {"$each": entries}}}
        )
