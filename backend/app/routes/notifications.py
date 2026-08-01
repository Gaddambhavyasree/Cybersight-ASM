from fastapi import APIRouter, Depends, Query
from app.database import get_database
from app.dependencies.auth import get_current_user
from app.services.notification_service import list_notifications, owned

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

@router.get("")
async def listing(page: int = Query(1, ge=1), per_page: int = Query(25, ge=1, le=200), severity: str | None = None, type: str | None = None, status: str | None = None, search: str | None = None, current_user: dict = Depends(get_current_user), db=Depends(get_database)):
    return await list_notifications(db, current_user, page, per_page, severity, type, status, search)

@router.get("/unread-count")
async def unread(current_user: dict = Depends(get_current_user), db=Depends(get_database)):
    data = await list_notifications(db, current_user, 1, 1, status="unread")
    return {"unread_count": data["unread_count"]}

@router.patch("/{notification_id}/read")
async def mark_read(notification_id: str, current_user: dict = Depends(get_current_user), db=Depends(get_database)):
    doc = await owned(db, notification_id, current_user); from datetime import datetime
    await db.notifications.update_one({"_id": doc["_id"]}, {"$set": {"status": "read", "updated_at": datetime.utcnow()}})
    return {"message": "Notification marked as read"}

@router.patch("/read-all")
async def mark_all(current_user: dict = Depends(get_current_user), db=Depends(get_database)):
    pids = [str(x["_id"]) async for x in db.projects.find({} if str(current_user.get("role", "")).lower() == "admin" else {"created_by": str(current_user["_id"])}, {"_id": 1})]
    from datetime import datetime
    result = await db.notifications.update_many({"project_id": {"$in": pids}, "status": "unread"}, {"$set": {"status": "read", "updated_at": datetime.utcnow()}})
    return {"updated": result.modified_count}

@router.delete("/read")
async def delete_read(current_user: dict = Depends(get_current_user), db=Depends(get_database)):
    pids = [str(x["_id"]) async for x in db.projects.find({} if str(current_user.get("role", "")).lower() == "admin" else {"created_by": str(current_user["_id"])}, {"_id": 1})]
    result = await db.notifications.delete_many({"project_id": {"$in": pids}, "status": "read"})
    return {"deleted": result.deleted_count}

@router.delete("/{notification_id}")
async def remove(notification_id: str, current_user: dict = Depends(get_current_user), db=Depends(get_database)):
    doc = await owned(db, notification_id, current_user); await db.notifications.delete_one({"_id": doc["_id"]}); return {"message": "Notification deleted"}
