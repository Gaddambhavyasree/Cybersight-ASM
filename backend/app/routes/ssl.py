import re
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query
from app.database import get_database
from app.dependencies.auth import get_current_user
from app.schemas.ssl import SSLListResponse, SSLResponse, SSLStatsResponse

router = APIRouter(prefix="/api/ssl-analysis", tags=["SSL Analysis"])
async def _ids(db, user):
    q = {} if user["role"] == "admin" else {"created_by": str(user["_id"])}
    return [str(x["_id"]) async for x in db.projects.find(q, {"_id": 1})]
async def _decorate(db, docs):
    pids = [ObjectId(x) for x in {d.get("project_id") for d in docs} if isinstance(x, str) and ObjectId.is_valid(x)]; sids = [ObjectId(x) for x in {d.get("scan_id") for d in docs} if isinstance(x, str) and ObjectId.is_valid(x)]
    ps = await db.projects.find({"_id": {"$in": pids}}, {"name": 1}).to_list(None); ss = await db.scans.find({"_id": {"$in": sids}}, {"scan_name": 1}).to_list(None)
    pn = {str(x["_id"]): x.get("name") for x in ps}; sn = {str(x["_id"]): x.get("scan_name") for x in ss}
    for d in docs: d["id"] = str(d.pop("_id")); d["project_name"] = pn.get(d.get("project_id")); d["scan_name"] = sn.get(d.get("scan_id"), d.get("scan_id"))
    return docs

@router.get("", response_model=SSLListResponse)
async def list_ssl(page: int = Query(1, ge=1), per_page: int = Query(50, ge=1, le=200), search: str | None = None, hostname: str | None = None, ssl_grade: str | None = None, tls_version: str | None = None, expired: bool | None = None, self_signed: bool | None = None, issuer: str | None = None, project_id: str | None = None, scan_id: str | None = None, current_user: dict = Depends(get_current_user), db=Depends(get_database)):
    ids = await _ids(db, current_user); q = {"project_id": project_id if project_id in ids else {"$in": []}} if project_id else {"project_id": {"$in": ids}}
    for field, val in (("hostname", hostname), ("issuer", issuer)):
        if val: q[field] = {"$regex": re.escape(val), "$options": "i"}
    if ssl_grade: q["ssl_grade"] = ssl_grade
    if tls_version: q["tls_version"] = tls_version
    if expired is not None: q["expired"] = expired
    if self_signed is not None: q["self_signed"] = self_signed
    if scan_id: q["scan_id"] = scan_id
    if search: q["$or"] = [{k: {"$regex": re.escape(search), "$options": "i"}} for k in ("hostname", "issuer", "common_name", "tls_version", "cipher", "ssl_grade")]
    total = await db.ssl_analysis.count_documents(q); docs = await db.ssl_analysis.find(q).sort([("last_seen", -1), ("hostname", 1)]).skip((page - 1) * per_page).limit(per_page).to_list(per_page)
    return SSLListResponse(records=await _decorate(db, docs), total=total, page=page, per_page=per_page)

@router.get("/stats", response_model=SSLStatsResponse)
async def ssl_stats(current_user: dict = Depends(get_current_user), db=Depends(get_database)):
    q = {"project_id": {"$in": await _ids(db, current_user)}}; dist = await db.ssl_analysis.aggregate([{"$match": q}, {"$group": {"_id": "$ssl_grade", "count": {"$sum": 1}}}, {"$sort": {"_id": 1}}]).to_list(None); tls = await db.ssl_analysis.aggregate([{"$match": q}, {"$group": {"_id": "$tls_version", "count": {"$sum": 1}}}]).to_list(None); issuers = await db.ssl_analysis.aggregate([{"$match": q}, {"$group": {"_id": "$issuer", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}, {"$limit": 10}]).to_list(None); weak = await db.ssl_analysis.aggregate([{"$match": {**q, "tls_version": {"$in": ["TLSv1", "TLSv1.1"]}}}, {"$group": {"_id": "$tls_version", "count": {"$sum": 1}}}]).to_list(None); latest = await db.ssl_analysis.find_one(q, sort=[("last_seen", -1)])
    grade_weight = {"A": 6, "A-": 5, "B": 4, "C": 3, "D": 2, "F": 1}; total = sum(x["count"] for x in dist); average = None
    if total:
        score = round(sum(grade_weight.get(x["_id"], 1) * x["count"] for x in dist) / total)
        average = next((g for g, w in grade_weight.items() if w == score), "F")
    return SSLStatsResponse(assets_with_ssl=await db.ssl_analysis.count_documents(q), expired_certificates=await db.ssl_analysis.count_documents({**q, "expired": True}), expiring_soon=await db.ssl_analysis.count_documents({**q, "expired": False, "days_remaining": {"$lte": 30}}), weak_tls_versions=await db.ssl_analysis.count_documents({**q, "tls_version": {"$in": ["TLSv1", "TLSv1.1"]}}), average_ssl_grade=average, last_scan_time=latest.get("last_seen") if latest else None, grade_distribution=[{"label": x["_id"], "count": x["count"]} for x in dist], tls_distribution=[{"label": x["_id"], "count": x["count"]} for x in tls], issuer_distribution=[{"label": x["_id"], "count": x["count"]} for x in issuers], weak_tls_usage=[{"label": x["_id"], "count": x["count"]} for x in weak])

@router.get("/{record_id}", response_model=SSLResponse)
async def ssl_detail(record_id: str, current_user: dict = Depends(get_current_user), db=Depends(get_database)):
    if not ObjectId.is_valid(record_id): raise HTTPException(404, "SSL analysis not found")
    doc = await db.ssl_analysis.find_one({"_id": ObjectId(record_id), "project_id": {"$in": await _ids(db, current_user)}})
    if not doc: raise HTTPException(404, "SSL analysis not found")
    return SSLResponse(**(await _decorate(db, [doc]))[0])
