import re
from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.database import get_database
from app.dependencies.auth import get_current_user
from app.schemas.dns import DNSRecordDetailResponse, DNSRecordListResponse, DNSStatsResponse

router = APIRouter(prefix="/api/dns-records", tags=["DNS Intelligence"])


async def _project_ids(db, user):
    query = {} if user["role"] == "admin" else {"created_by": str(user["_id"])}
    return [str(project["_id"]) async for project in db.projects.find(query, {"_id": 1})]


async def _decorate(db, records):
    project_ids = {record.get("project_id") for record in records if record.get("project_id")}
    scan_ids = {record.get("scan_id") for record in records if record.get("scan_id")}
    projects = await db.projects.find({"_id": {"$in": [ObjectId(x) for x in project_ids if isinstance(x, str) and ObjectId.is_valid(x)]}}, {"name": 1}).to_list(None)
    scans = await db.scans.find({"_id": {"$in": [ObjectId(x) for x in scan_ids if isinstance(x, str) and ObjectId.is_valid(x)]}}, {"scan_name": 1}).to_list(None)
    project_names = {str(item["_id"]): item.get("name") for item in projects}
    scan_names = {str(item["_id"]): item.get("scan_name") for item in scans}
    for record in records:
        record["id"] = str(record.pop("_id"))
        record["project_name"] = project_names.get(record.get("project_id"))
        record["scan_name"] = scan_names.get(record.get("scan_id"), record.get("scan_id"))
    return records


@router.get("", response_model=DNSRecordListResponse)
async def list_dns_records(
    page: int = Query(1, ge=1), per_page: int = Query(50, ge=1, le=200),
    hostname: str | None = None, record_type: str | None = None, record_value: str | None = None,
    search: str | None = None, project_id: str | None = None, scan_id: str | None = None,
    current_user: dict = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_database),
):
    ids = await _project_ids(db, current_user)
    query = {"project_id": project_id if project_id in ids else {"$in": []}} if project_id else {"project_id": {"$in": ids}}
    if hostname: query["hostname"] = {"$regex": re.escape(hostname), "$options": "i"}
    if record_type: query["record_type"] = record_type.upper()
    if record_value: query["record_value"] = {"$regex": re.escape(record_value), "$options": "i"}
    if scan_id: query["scan_id"] = scan_id
    if search:
        query["$and"] = query.get("$and", []) + [{"$or": [
            {"hostname": {"$regex": re.escape(search), "$options": "i"}},
            {"record_type": {"$regex": re.escape(search), "$options": "i"}},
            {"record_value": {"$regex": re.escape(search), "$options": "i"}},
        ]}]
    total = await db.dns_records.count_documents(query)
    records = await db.dns_records.find(query).sort([("last_seen", -1), ("hostname", 1)]).skip((page - 1) * per_page).limit(per_page).to_list(per_page)
    return DNSRecordListResponse(records=await _decorate(db, records), total=total, page=page, per_page=per_page)


@router.get("/stats", response_model=DNSStatsResponse)
async def dns_stats(current_user: dict = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_database)):
    query = {"project_id": {"$in": await _project_ids(db, current_user)}}
    distribution = await db.dns_records.aggregate([{"$match": query}, {"$group": {"_id": "$record_type", "count": {"$sum": 1}}}, {"$sort": {"count": -1, "_id": 1}}]).to_list(None)
    mx = await db.dns_records.aggregate([{"$match": {**query, "record_type": "MX"}}, {"$group": {"_id": "$record_value", "count": {"$sum": 1}}}, {"$sort": {"count": -1, "_id": 1}}, {"$limit": 10}]).to_list(10)
    by_asset = await db.dns_records.aggregate([{"$match": query}, {"$group": {"_id": {"type": "$record_type", "asset": "$asset_id"}}}, {"$group": {"_id": "$_id.type", "count": {"$sum": 1}}}, {"$sort": {"count": -1, "_id": 1}}]).to_list(None)
    latest = await db.dns_records.find_one(query, sort=[("last_seen", -1)])
    return DNSStatsResponse(total_dns_records=await db.dns_records.count_documents(query), assets_with_dns_records=len(await db.dns_records.distinct("asset_id", query)), mx_records=await db.dns_records.count_documents({**query, "record_type": "MX"}), txt_records=await db.dns_records.count_documents({**query, "record_type": "TXT"}), dnssec_enabled=await db.dns_records.count_documents({**query, "record_type": "DNSKEY"}), last_scan_time=latest.get("last_seen") if latest else None, record_distribution=[{"label": item["_id"], "count": item["count"]} for item in distribution], top_mx_domains=[{"label": item["_id"], "count": item["count"]} for item in mx], assets_per_record_type=[{"label": item["_id"], "count": item["count"]} for item in by_asset])


@router.get("/{record_id}", response_model=DNSRecordDetailResponse)
async def dns_record_detail(record_id: str, current_user: dict = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_database)):
    if not ObjectId.is_valid(record_id): raise HTTPException(404, "DNS record not found")
    record = await db.dns_records.find_one({"_id": ObjectId(record_id), "project_id": {"$in": await _project_ids(db, current_user)}})
    if not record: raise HTTPException(404, "DNS record not found")
    related = await db.dns_records.find({"project_id": record["project_id"], "asset_id": record["asset_id"]}).sort("record_type", 1).to_list(None)
    main = (await _decorate(db, [record]))[0]
    main["related_records"] = await _decorate(db, related)
    return DNSRecordDetailResponse(**main)
