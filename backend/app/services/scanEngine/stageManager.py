from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from app.models.scan import ScanStage, ScanStatus
from app.services.scanEngine.progressCalculator import calculate_progress
from app.services.scanEngine.logger import (
    log_entering_stage, log_stage_completed, log_stage_failed,
)
from app.services.scanEngine.workflow import get_next_stage, STAGE_LABELS


class StageManager:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def transition_to(self, scan_id: str, stage: ScanStage) -> None:
        now = datetime.utcnow()
        logs = [log_entering_stage(stage)]
        progress = calculate_progress(stage)

        await self.db.scans.update_one(
            {"_id": ObjectId(scan_id)},
            {
                "$set": {
                    "current_stage": stage.value,
                    "progress": progress,
                    "updated_at": now,
                },
                "$push": {"logs": {"$each": logs}},
            },
        )

    async def mark_stage_completed(self, scan_id: str, stage: ScanStage) -> None:
        now = datetime.utcnow()
        logs = [log_stage_completed(stage)]

        await self.db.scans.update_one(
            {"_id": ObjectId(scan_id)},
            {
                "$set": {"updated_at": now},
                "$push": {"logs": {"$each": logs}},
            },
        )
    async def mark_stage_failed(self, scan_id: str, stage: ScanStage, error: str) -> None:
        now = datetime.utcnow()
        logs = [log_stage_failed(stage, error)]

        await self.db.scans.update_one(
            {"_id": ObjectId(scan_id)},
            {
                "$set": {
                    "status": ScanStatus.FAILED.value,
                    "failure_stage": stage.value,
                    "failure_message": error,
                    "completed_at": now,
                    "updated_at": now,
                },
                "$push": {"logs": {"$each": logs}},
            },
        )

    async def mark_scan_completed(self, scan_id: str) -> None:
        now = datetime.utcnow()
        from app.services.scanEngine.logger import log_workflow_completed
        logs = [log_workflow_completed()]

        await self.db.scans.update_one(
            {"_id": ObjectId(scan_id)},
            {
                "$set": {
                    "status": ScanStatus.COMPLETED.value,
                    "current_stage": ScanStage.COMPLETED.value,
                    "progress": 100,
                    "completed_at": now,
                    "updated_at": now,
                },
                "$push": {"logs": {"$each": logs}},
            },
        )

        from app.services.history_service import create_snapshot
        try:
            await create_snapshot(self.db, scan_id)
        except Exception:
            import logging
            logging.getLogger(__name__).exception("Historical snapshot failed after scan completion")
        from app.services.notification_service import generate_notifications
        try:
            await generate_notifications(self.db, scan_id)
        except Exception:
            import logging
            logging.getLogger(__name__).exception("Notification generation failed after scan completion")

    async def mark_scan_cancelled(self, scan_id: str) -> None:
        now = datetime.utcnow()
        from app.services.scanEngine.logger import log_scan_cancelled
        logs = [log_scan_cancelled()]

        await self.db.scans.update_one(
            {"_id": ObjectId(scan_id)},
            {
                "$set": {
                    "status": ScanStatus.CANCELLED.value,
                    "cancelled_at": now,
                    "completed_at": now,
                    "updated_at": now,
                },
                "$push": {"logs": {"$each": logs}},
            },
        )

    async def get_scan_state(self, scan_id: str) -> dict | None:
        return await self.db.scans.find_one({"_id": ObjectId(scan_id)})
