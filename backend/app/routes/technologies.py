from bson import ObjectId
from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.database import get_database
from app.dependencies.auth import get_current_user
from app.schemas.technology import TechnologyListResponse, TechnologyStatsResponse

router = APIRouter(prefix="/api/technologies", tags=["Technologies"])

async def _project_ids(db, user):
    query = {} if user["role"] == "admin" else {"created_by": str(user["_id"])}
    return [str(item["_id"]) async for item in db.projects.find(query, {"_id": 1})]

@router.get("", response_model=TechnologyListResponse)
async def list_technologies(page: int = Query(1, ge=1), per_page: int = Query(50, ge=1, le=200),
    search: str = Query(None), hostname: str = Query(None), technology: str = Query(None),
    category: str = Query(None), project_id: str = Query(None), scan_id: str = Query(None),
    current_user: dict = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_database)):
    ids = await _project_ids(db, current_user)
    query = {"project_id": project_id if project_id in ids else {"$in": ids}} if project_id else {"project_id": {"$in": ids}}
    if search: query["$or"] = [{"hostname": {"$regex": search, "$options": "i"}}, {"technology_name": {"$regex": search, "$options": "i"}}]
    if hostname: query["hostname"] = {"$regex": hostname, "$options": "i"}
    if technology: query["technology_name"] = {"$regex": technology, "$options": "i"}
    if category: query["category"] = category
    if scan_id: query["scan_id"] = scan_id
    total = await db.technologies.count_documents(query)
    docs = await db.technologies.find(query).sort([("last_seen", -1), ("technology_name", 1)]).skip((page - 1) * per_page).limit(per_page).to_list(length=per_page)
    project_docs = await db.projects.find({"_id": {"$in": [ObjectId(p) for p in {d.get('project_id') for d in docs} if ObjectId.is_valid(p)]}}, {"name": 1}).to_list(length=None)
    scan_docs = await db.scans.find({"_id": {"$in": [ObjectId(s) for s in {d.get('scan_id') for d in docs} if ObjectId.is_valid(s)]}}, {"scan_name": 1}).to_list(length=None)
    project_names = {str(d["_id"]): d.get("name") for d in project_docs}; scan_names = {str(d["_id"]): d.get("scan_name") for d in scan_docs}
    for doc in docs:
        doc["id"] = str(doc.pop("_id")); doc["project_name"] = project_names.get(doc.get("project_id")); doc["scan_name"] = scan_names.get(doc.get("scan_id"), doc.get("scan_id"))
    return TechnologyListResponse(technologies=docs, total=total, page=page, per_page=per_page)

@router.get("/stats", response_model=TechnologyStatsResponse)
async def technology_stats(current_user: dict = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_database)):
    ids = await _project_ids(db, current_user); query = {"project_id": {"$in": ids}}
    total = await db.technologies.count_documents(query)
    groups = await db.technologies.aggregate([{"$match": query}, {"$group": {"_id": "$technology_name", "count": {"$sum": 1}}}, {"$sort": {"count": -1, "_id": 1}}, {"$limit": 10}]).to_list(length=10)
    categories = await db.technologies.aggregate([{"$match": query}, {"$group": {"_id": "$category", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}]).to_list(length=20)
    frameworks = await db.technologies.aggregate([{"$match": {**query, "category": "Framework"}}, {"$group": {"_id": "$technology_name", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}, {"$limit": 10}]).to_list(length=10)
    servers = await db.technologies.aggregate([{"$match": {**query, "category": "Web Server"}}, {"$group": {"_id": "$technology_name", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}, {"$limit": 10}]).to_list(length=10)
    latest = await db.technologies.find_one(query, sort=[("last_seen", -1)])
    return TechnologyStatsResponse(total_technologies=total, unique_technologies=len(await db.technologies.distinct("technology_name", query)), most_used_technology=groups[0]["_id"] if groups else None, frameworks_detected=await db.technologies.count_documents({**query, "category": "Framework"}), programming_languages=await db.technologies.count_documents({**query, "category": "Programming Language"}), last_scan_time=latest.get("last_seen") if latest else None, top_technologies=[{"label": x["_id"], "count": x["count"]} for x in groups], categories=[{"label": x["_id"], "count": x["count"]} for x in categories], frameworks=[{"label": x["_id"], "count": x["count"]} for x in frameworks], web_servers=[{"label": x["_id"], "count": x["count"]} for x in servers])
