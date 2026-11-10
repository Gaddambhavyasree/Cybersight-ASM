import asyncio
import logging
from datetime import datetime
from bson import ObjectId

from app.models.scan import ScanStage
from app.services.httpx_runner.runner import _find_httpx, run_httpx_technology_single
from app.services.scanEngine.executors.base import BaseStageExecutor
from app.services.scanEngine.logger import log_event

logger = logging.getLogger(__name__)


class TechnologyDetectionExecutor(BaseStageExecutor):
    def __init__(self):
        super().__init__(stage=ScanStage.TECHNOLOGY_DETECTION, simulated_delay=0)

    async def execute(self, scan_id: str, target: str, db) -> dict:
        logger.info("[%s] Starting Technology Detection", scan_id)
        try:
            httpx_path = _find_httpx()
            if not httpx_path:
                message = "httpx executable not found for technology detection"
                await self._log(db, scan_id, message, "error")
                return self._error(message)

            scan = await db.scans.find_one({"_id": ObjectId(scan_id)})
            if not scan:
                return self._error("Scan record not found for Technology Detection")
            project_id = scan.get("project_id", "")
            assets = await db.assets.find({"project_id": project_id, "is_live": True}).to_list(length=1000)
            await self._log_many(db, scan_id, [
                log_event("Technology Detection started"),
                log_event(f"Scanning {len(assets)} live assets"),
            ])
            saved = 0
            for asset in assets:
                saved += await self._scan_asset(db, scan_id, project_id, asset, httpx_path)
            await self._log_many(db, scan_id, [log_event(f"Saved {saved} technologies"), log_event("Technology Detection completed")])
            logger.info("[%s] Technology Detection finished", scan_id)
            return {"status": "success", "stage": self.stage.value, "message": f"Detected {saved} technologies", "data": {"total": saved, "assets_scanned": len(assets)}}
        except Exception as exc:
            message = f"Technology Detection failed: {type(exc).__name__}: {exc}"
            logger.exception("[%s] %s", scan_id, message)
            try: await self._log(db, scan_id, message, "error")
            except Exception: logger.exception("[%s] Could not save technology failure log", scan_id)
            return self._error(message)

    async def _scan_asset(self, db, scan_id, project_id, asset, httpx_path) -> int:
        hostname = asset.get("hostname", "")
        try:
            results = await asyncio.to_thread(run_httpx_technology_single, hostname, httpx_path, 60)
        except FileNotFoundError:
            await self._log(db, scan_id, "httpx executable disappeared during technology detection", "error")
            return 0
        except Exception as exc:
            await self._log(db, scan_id, f"HTTPX failed for {hostname}: {exc}", "error")
            return 0
        now = datetime.utcnow()
        unique = {(str(item.get("name")).strip(), item.get("category", "Technology"), item.get("version")): item for item in results if item.get("name")}
        technologies = []
        for (name, category, version), item in unique.items():
            await db.technologies.update_one(
                {"project_id": project_id, "asset_id": str(asset["_id"]), "technology_name": name, "category": category},
                {"$setOnInsert": {"first_seen": now, "created_at": now}, "$set": {
                    "scan_id": scan_id, "hostname": hostname, "ip": item.get("ip") or asset.get("ip"),
                    "version": version, "source": "httpx", "confidence": item.get("confidence", 1.0),
                    "last_seen": now, "updated_at": now,
                }}, upsert=True,
            )
            technologies.append({"name": name, "category": category, "version": version})
        if technologies:
            await self._log(db, scan_id, f"{hostname} -> {', '.join(t['name'] for t in technologies)}")
        all_tech = await db.technologies.find({"project_id": project_id, "asset_id": str(asset["_id"])}, {"technology_name": 1, "category": 1, "version": 1}).to_list(length=500)
        await db.assets.update_one({"_id": asset["_id"]}, {"$set": {"technology_count": len(all_tech), "technologies": [{"name": t["technology_name"], "category": t.get("category", "Technology"), "version": t.get("version")} for t in all_tech], "last_technology_scan": now, "updated_at": now}})
        return len(technologies)

    @staticmethod
    async def _log(db, scan_id, message, level="info"):
        await db.scans.update_one({"_id": ObjectId(scan_id)}, {"$push": {"logs": log_event(message, level)}})

    @staticmethod
    async def _log_many(db, scan_id, entries):
        await db.scans.update_one({"_id": ObjectId(scan_id)}, {"$push": {"logs": {"$each": entries}}})

    def _error(self, message):
        return {"status": "error", "stage": self.stage.value, "message": message}
