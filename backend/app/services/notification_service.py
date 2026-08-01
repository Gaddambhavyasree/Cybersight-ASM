import logging
from datetime import datetime, timedelta
from bson import ObjectId
from fastapi import HTTPException
logger = logging.getLogger(__name__)

def _key(x, kind):
    if kind == "assets": return (x.get("hostname") or x.get("ip") or "").lower()
    if kind == "ports": return (x.get("asset_id"), x.get("port"), x.get("protocol", "tcp"))
    if kind == "technologies": return (x.get("asset_id"), (x.get("technology_name") or "").lower())
    if kind == "vulnerabilities": return (x.get("asset_id"), x.get("cve") or x.get("template_id"))
    return x.get("asset_id")

async def _items(db, scan_id, collection): return await db[collection].find({"scan_id": scan_id}).to_list(None)

async def generate_notifications(db, scan_id):
    try:
        scan = await db.scans.find_one({"_id": ObjectId(scan_id)})
        if not scan: return 0
        project_id = str(scan.get("project_id", "")); previous = await db.scans.find_one({"project_id": project_id, "status": "completed", "_id": {"$ne": ObjectId(scan_id)}, "completed_at": {"$lt": scan.get("completed_at", datetime.utcnow())}}, sort=[("completed_at", -1)])
        notifications = []
        def add(kind, title, description, severity="Info", asset_id=None, metadata=None): notifications.append({"project_id": project_id, "scan_id": scan_id, "asset_id": asset_id, "type": kind, "title": title, "description": description, "severity": severity, "status": "unread", "created_at": datetime.utcnow(), "updated_at": datetime.utcnow(), "metadata": metadata or {}})
        add("scan_completed", "Scan completed", f"{scan.get('scan_name', 'Security scan')} completed successfully.")
        current = {kind: await _items(db, scan_id, kind) for kind in ("assets", "ports", "technologies", "vulnerabilities")}
        old = {kind: await _items(db, str(previous["_id"]), kind) for kind in current} if previous else {kind: [] for kind in current}
        for x in current["assets"]:
            if _key(x, "assets") not in {_key(y, "assets") for y in old["assets"]}: add("new_asset", "New asset detected", f"{x.get('hostname') or x.get('ip', 'Unknown asset')} was discovered.", asset_id=str(x.get("_id")), metadata={"hostname": x.get("hostname"), "ip": x.get("ip")})
        for x in current["ports"]:
            if _key(x, "ports") not in {_key(y, "ports") for y in old["ports"]}: add("new_open_port", f"Port {x.get('port')} opened", f"Port {x.get('port')} is open on {x.get('hostname', 'an asset')}.", "High", str(x.get("asset_id")), {"port": x.get("port"), "hostname": x.get("hostname")})
        for x in current["vulnerabilities"]:
            if _key(x, "vulnerabilities") not in {_key(y, "vulnerabilities") for y in old["vulnerabilities"]}: add("critical_vulnerability" if str(x.get("severity", "")).lower() == "critical" else "new_vulnerability", "Critical vulnerability detected" if str(x.get("severity", "")).lower() == "critical" else "New vulnerability detected", f"{x.get('cve') or x.get('template_name', 'A vulnerability')} was detected.", "Critical" if str(x.get("severity", "")).lower() == "critical" else "High", str(x.get("asset_id")), {"cve": x.get("cve"), "severity": x.get("severity")})
        # Risk changes and SSL alerts are stored on assets/SSL records, so they do not require a duplicate snapshot.
        assets = current["assets"]
        if previous:
            prior_assets = await db.assets.find({"project_id": project_id, "scan_id": str(previous["_id"])}).to_list(None)
            prior = {_key(x, "assets"): x for x in prior_assets}
            for x in assets:
                old_score = prior.get(_key(x, "assets"), {}).get("risk_score"); new_score = x.get("risk_score")
                if old_score is not None and new_score is not None and abs(new_score - old_score) >= 10: add("risk_increased" if new_score > old_score else "risk_decreased", "Risk score increased" if new_score > old_score else "Risk score decreased", f"{x.get('hostname', 'Asset')} changed from {old_score} to {new_score}.", "High" if new_score > old_score else "Info", str(x.get("_id")), {"previous": old_score, "current": new_score})
        await db.notifications.insert_many(notifications) if notifications else None
        await db.scans.update_one({"_id": ObjectId(scan_id)}, {"$push": {"logs": {"message": f"Notification generation completed: {len(notifications)} alerts", "timestamp": datetime.utcnow(), "level": "info"}}})
        return len(notifications)
    except Exception: logger.exception("Notification generation failed for scan %s", scan_id); return 0

async def list_notifications(db, user, page=1, per_page=25, severity=None, kind=None, status=None, search=None):
    pids = [str(x["_id"]) async for x in db.projects.find({} if str(user.get("role", "")).lower() == "admin" else {"created_by": str(user["_id"])}, {"_id": 1})]
    q = {"project_id": {"$in": pids}}
    if severity: q["severity"] = severity
    if kind: q["type"] = kind
    if status in ("read", "unread"): q["status"] = status
    if search: q["$or"] = [{"title": {"$regex": search, "$options": "i"}}, {"description": {"$regex": search, "$options": "i"}}, {"metadata.hostname": {"$regex": search, "$options": "i"}}, {"metadata.cve": {"$regex": search, "$options": "i"}}]
    total = await db.notifications.count_documents(q); unread = await db.notifications.count_documents({**q, "status": "unread"}); docs = await db.notifications.find(q).sort("created_at", -1).skip((page - 1) * per_page).limit(per_page).to_list(per_page)
    return {"records": [{**dict(x), "id": str(x.pop("_id"))} for x in docs], "total": total, "unread_count": unread, "page": page, "per_page": per_page}

async def owned(db, notification_id, user):
    try: oid = ObjectId(notification_id)
    except Exception: raise HTTPException(404, "Notification not found")
    doc = await db.notifications.find_one({"_id": oid});
    if not doc: raise HTTPException(404, "Notification not found")
    if str(user.get("role", "")).lower() != "admin":
        ok = await db.projects.find_one({"_id": ObjectId(doc["project_id"]), "created_by": str(user["_id"])})
        if not ok: raise HTTPException(404, "Notification not found")
    return doc
