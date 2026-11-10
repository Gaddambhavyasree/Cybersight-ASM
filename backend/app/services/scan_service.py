from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from app.models.scan import ScanStatus, ScanStage, ScanLog
from app.schemas.scan import StartScanRequest, ScanResponse, ScanListResponse
from app.services.scanEngine import scan_engine
from fastapi import HTTPException, status


def _scan_to_response(scan: dict) -> ScanResponse:
    logs = []
    for log in scan.get("logs", []):
        logs.append({
            "message": log["message"],
            "timestamp": log["timestamp"],
            "level": log.get("level", "info"),
        })

    return ScanResponse(
        id=str(scan["_id"]),
        project_id=scan["project_id"],
        project_name=scan.get("project_name"),
        target_domain=scan.get("target_domain"),
        scan_name=scan["scan_name"],
        status=scan["status"],
        current_stage=scan["current_stage"],
        progress=scan.get("progress", 0),
        started_at=scan.get("started_at"),
        completed_at=scan.get("completed_at"),
        cancelled_at=scan.get("cancelled_at"),
        failure_stage=scan.get("failure_stage"),
        failure_message=scan.get("failure_message"),
        assets_count=scan.get("assets_count", 0),
        logs=logs,
        initiated_by=scan["initiated_by"],
        initiated_by_name=scan.get("initiated_by_name"),
        created_at=scan["created_at"],
        updated_at=scan["updated_at"],
    )


async def start_scan(
    db: AsyncIOMotorDatabase,
    data: StartScanRequest,
    user_id: str,
    user_name: str,
) -> ScanResponse:
    project = await db.projects.find_one({"_id": ObjectId(data.project_id)})
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    now = datetime.utcnow()
    logs = [
        ScanLog(message="Scan created", timestamp=now, level="info").model_dump(),
    ]

    doc = {
        "project_id": data.project_id,
        "project_name": project["name"],
        "target_domain": project.get("target_domain", ""),
        "scan_name": data.scan_name,
        "status": ScanStatus.QUEUED.value,
        "current_stage": ScanStage.WAITING.value,
        "progress": 0,
        "started_at": None,
        "completed_at": None,
        "cancelled_at": None,
        "failure_stage": None,
        "failure_message": None,
        "assets_count": 0,
        "logs": logs,
        "initiated_by": user_id,
        "initiated_by_name": user_name,
        "created_at": now,
        "updated_at": now,
    }

    result = await db.scans.insert_one(doc)
    scan_id = str(result.inserted_id)
    doc["_id"] = result.inserted_id

    await scan_engine.start(scan_id, db)

    return _scan_to_response(doc)


async def list_scans(
    db: AsyncIOMotorDatabase,
    user_id: str,
    user_role: str,
    page: int = 1,
    per_page: int = 20,
    search: str = None,
    status_filter: str = None,
    project_id: str = None,
) -> ScanListResponse:
    query = {}

    if user_role != "admin":
        query["initiated_by"] = user_id

    if search:
        query["$or"] = [
            {"scan_name": {"$regex": search, "$options": "i"}},
            {"project_name": {"$regex": search, "$options": "i"}},
        ]

    if status_filter:
        query["status"] = status_filter

    if project_id:
        query["project_id"] = project_id

    total = await db.scans.count_documents(query)
    skip = (page - 1) * per_page
    cursor = db.scans.find(query).sort("created_at", -1).skip(skip).limit(per_page)
    scans = await cursor.to_list(length=per_page)

    return ScanListResponse(
        scans=[_scan_to_response(s) for s in scans],
        total=total,
        page=page,
        per_page=per_page,
    )


async def get_scan(
    db: AsyncIOMotorDatabase, scan_id: str, user_id: str, user_role: str
) -> ScanResponse:
    scan = await db.scans.find_one({"_id": ObjectId(scan_id)})
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found"
        )

    if user_role != "admin" and scan["initiated_by"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return _scan_to_response(scan)


async def cancel_scan(
    db: AsyncIOMotorDatabase, scan_id: str, user_id: str, user_role: str
) -> ScanResponse:
    scan = await db.scans.find_one({"_id": ObjectId(scan_id)})
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found"
        )

    if user_role != "admin" and scan["initiated_by"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if scan["status"] not in (ScanStatus.PENDING.value, ScanStatus.QUEUED.value, ScanStatus.RUNNING.value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel a scan that is not pending, queued, or running",
        )

    cancelled_via_engine = await scan_engine.cancel(scan_id)

    if not cancelled_via_engine:
        now = datetime.utcnow()
        from app.services.scanEngine.logger import log_scan_cancelled
        cancel_log = log_scan_cancelled()

        await db.scans.update_one(
            {"_id": ObjectId(scan_id)},
            {
                "$set": {
                    "status": ScanStatus.CANCELLED.value,
                    "cancelled_at": now,
                    "completed_at": now,
                    "updated_at": now,
                },
                "$push": {"logs": cancel_log},
            },
        )

    updated = await db.scans.find_one({"_id": ObjectId(scan_id)})
    return _scan_to_response(updated)


async def delete_scan(
    db: AsyncIOMotorDatabase, scan_id: str, user_id: str, user_role: str
) -> dict:
    scan = await db.scans.find_one({"_id": ObjectId(scan_id)})
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found"
        )

    if user_role != "admin" and scan["initiated_by"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if scan["status"] in (ScanStatus.PENDING.value, ScanStatus.QUEUED.value, ScanStatus.RUNNING.value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a scan that is still running. Cancel it first.",
        )

    result = await db.scans.delete_one({"_id": ObjectId(scan_id)})
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found"
        )

    return {"message": "Scan deleted successfully"}
