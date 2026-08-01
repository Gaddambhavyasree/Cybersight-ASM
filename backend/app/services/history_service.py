import asyncio
from datetime import datetime
from bson import ObjectId
from fastapi import HTTPException

COLLECTIONS = ("assets", "ports", "technologies", "dns_records", "ssl_analysis", "web_assets", "vulnerabilities", "threat_intelligence")

def _id(doc): return str(doc.get("_id"))
def _key(doc, kind):
    if kind == "assets": return (doc.get("hostname") or doc.get("ip") or "").lower()
    if kind == "ports": return (doc.get("asset_id"), int(doc.get("port", 0)), doc.get("protocol", "tcp"))
    if kind == "technologies": return (doc.get("asset_id"), (doc.get("technology_name") or "").lower())
    if kind == "dns_records": return (doc.get("asset_id"), doc.get("record_type"), doc.get("record_value"))
    if kind == "web_assets": return (doc.get("asset_id"), doc.get("url"))
    if kind == "vulnerabilities": return (doc.get("asset_id"), doc.get("cve") or doc.get("template_id"))
    if kind == "threat_intelligence": return (doc.get("asset_id"), doc.get("cve") or doc.get("vulnerability_id"))
    return doc.get("asset_id")

async def create_snapshot(db, scan_id: str):
    scan = await db.scans.find_one({"_id": ObjectId(scan_id)})
    if not scan: return None
    project_id = str(scan.get("project_id", ""))
    query = {"scan_id": scan_id}
    counts = {name: await db[name].count_documents(query) for name in COLLECTIONS}
    # Assets are retained across scans, so use the scan's asset membership where available.
    if not counts["assets"]:
        counts["assets"] = await db.assets.count_documents({"project_id": project_id})
    live = await db.assets.count_documents({"project_id": project_id, "is_live": True, "$or": [{"scan_id": scan_id}, {"scan_id": {"$exists": False}}]})
    open_ports = await db.ports.count_documents({**query, "state": "open"})
    critical = await db.vulnerabilities.count_documents({**query, "severity": "critical"})
    risk = await db.assets.aggregate([{"$match": {"project_id": project_id, "risk_score": {"$exists": True}}}, {"$group": {"_id": None, "avg": {"$avg": "$risk_score"}}}]).to_list(1)
    risk_score = round(risk[0]["avg"]) if risk else 0
    now = datetime.utcnow()
    snapshot = {"scan_id": scan_id, "project_id": project_id, "project_name": scan.get("project_name"), "scan_name": scan.get("scan_name", "Historical scan"), "started_at": scan.get("started_at"), "completed_at": scan.get("completed_at") or now, "status": "completed", "counts": {**counts, "live_assets": live, "open_ports": open_ports, "critical_findings": critical}, "risk_score": risk_score, "risk_level": _risk_level(risk_score), "created_at": now, "updated_at": now}
    await db.scan_history.update_one({"scan_id": scan_id}, {"$set": snapshot}, upsert=True)
    await db.scans.update_one({"_id": ObjectId(scan_id)}, {"$push": {"logs": {"message": "Historical snapshot created", "timestamp": now, "level": "info"}}})
    return snapshot

def _risk_level(score): return "Very Low" if score <= 20 else "Low" if score <= 40 else "Medium" if score <= 60 else "High" if score <= 80 else "Critical"

async def _authorized_scan(db, scan_id, user, allow_missing=False):
    try: oid = ObjectId(scan_id)
    except Exception: oid = None
    scan = await db.scan_history.find_one({"$or": [{"_id": oid}, {"scan_id": scan_id}]}) if oid else await db.scan_history.find_one({"scan_id": scan_id})
    if not scan:
        scan_doc = await db.scans.find_one({"_id": oid}) if oid else None
        if scan_doc and scan_doc.get("status") == "completed": scan = await create_snapshot(db, scan_id)
    if not scan: 
        if allow_missing: return None
        raise HTTPException(404, "Historical scan not found")
    projects = await db.projects.find({"_id": ObjectId(scan["project_id"]), "created_by": str(user["_id"])}, {"_id": 1}).to_list(1) if str(user.get("role", "")).lower() != "admin" and ObjectId.is_valid(scan["project_id"]) else []
    if str(user.get("role", "")).lower() != "admin" and not projects: raise HTTPException(404, "Historical scan not found")
    return scan

def _public(doc):
    out = dict(doc); out["id"] = _id(out) if out.get("_id") is not None else str(out.get("scan_id", "")); out.pop("_id", None)
    if out.get("started_at") and out.get("completed_at"): out["duration_seconds"] = (out["completed_at"] - out["started_at"]).total_seconds()
    out.setdefault("counts", {}); return out

async def list_history(db, user, page=1, per_page=25, project_id=None, search=None, status="completed", risk_level=None):
    pids = [str(x["_id"]) async for x in db.projects.find({} if str(user.get("role", "")).lower() == "admin" else {"created_by": str(user["_id"])}, {"_id": 1})]
    # Backfill snapshots for completed scans created before the history module
    # was enabled, without duplicating scan data.
    completed = db.scans.find({"project_id": {"$in": pids}, "status": "completed"}, {"_id": 1})
    async for scan in completed:
        scan_id = str(scan["_id"])
        if not await db.scan_history.find_one({"scan_id": scan_id}, {"_id": 1}):
            try: await create_snapshot(db, scan_id)
            except Exception: pass
    q = {"project_id": project_id if project_id in pids else {"$in": []}} if project_id else {"project_id": {"$in": pids}}
    if status: q["status"] = status
    if risk_level: q["risk_level"] = risk_level
    if search: q["$or"] = [{"scan_name": {"$regex": search, "$options": "i"}}, {"project_name": {"$regex": search, "$options": "i"}}]
    total = await db.scan_history.count_documents(q); docs = await db.scan_history.find(q).sort("completed_at", -1).skip((page - 1) * per_page).limit(per_page).to_list(per_page)
    return {"records": [_public(x) for x in docs], "total": total, "page": page, "per_page": per_page}

async def detail(db, scan_id, user):
    scan = await _authorized_scan(db, scan_id, user)
    stats = {name: await db[name].count_documents({"scan_id": scan_id}) for name in COLLECTIONS}
    timeline = [{"timestamp": x.get("timestamp"), "message": x.get("message"), "level": x.get("level", "info")} for x in (await db.scans.find_one({"_id": ObjectId(scan_id)}, {"logs": 1}) or {}).get("logs", [])]
    return {"scan": _public(scan), "statistics": stats, "timeline": timeline}

async def delete_history(db, scan_id, user):
    scan = await _authorized_scan(db, scan_id, user)
    await db.scan_history.delete_one({"_id": scan["_id"]})
    return {"message": "Historical snapshot deleted"}

async def compare(db, previous_id, current_id, user):
    previous, current = await asyncio.gather(_authorized_scan(db, previous_id, user), _authorized_scan(db, current_id, user))
    if previous["project_id"] != current["project_id"]: raise HTTPException(400, "Scans must belong to the same project")
    changes = {}
    for kind in COLLECTIONS:
        a, b = await asyncio.gather(db[kind].find({"scan_id": previous_id}).to_list(None), db[kind].find({"scan_id": current_id}).to_list(None))
        old, new = {_key(x, kind): x for x in a}, {_key(x, kind): x for x in b}
        added, removed = sorted(set(new) - set(old), key=str), sorted(set(old) - set(new), key=str)
        changed = []
        for key in set(old) & set(new):
            if kind == "technologies" and old[key].get("version") != new[key].get("version"): changed.append({"key": key, "from": old[key].get("version"), "to": new[key].get("version")})
            elif kind == "ports" and old[key].get("service") != new[key].get("service"): changed.append({"key": key, "from": old[key].get("service"), "to": new[key].get("service")})
            elif kind == "vulnerabilities" and old[key].get("severity") != new[key].get("severity"): changed.append({"key": key, "from": old[key].get("severity"), "to": new[key].get("severity")})
        changes[kind] = {"added": [str(x) for x in added], "removed": [str(x) for x in removed], "changed": changed}
    delta = current.get("risk_score", 0) - previous.get("risk_score", 0); summary = [f"{len(changes['assets']['added'])} new assets", f"{len(changes['ports']['added'])} new open ports", f"{len(changes['vulnerabilities']['added'])} new vulnerabilities", f"Risk {'increased' if delta >= 0 else 'decreased'} by {abs(delta)}"]
    return {"previous": _public(previous), "current": _public(current), "changes": changes, "summary": summary, "recommendations": ["Review newly exposed ports and critical vulnerabilities"] if changes["ports"]["added"] or changes["vulnerabilities"]["added"] else []}
