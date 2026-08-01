from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from app.database import get_database
from app.schemas.asset import PortResponse, PortListResponse, PortStatsResponse
from app.dependencies.auth import get_current_user
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

router = APIRouter(prefix="/api/ports", tags=["Ports"])


@router.get("", response_model=PortListResponse)
async def list_ports(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    asset_id: str = Query(None),
    project_id: str = Query(None),
    scan_id: str = Query(None),
    hostname: str = Query(None),
    ip: str = Query(None),
    port: int = Query(None, ge=1, le=65535),
    protocol: str = Query(None),
    state: str = Query(None),
    service: str = Query(None),
    date_from: str = Query(None),
    date_to: str = Query(None),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    skip = (page - 1) * per_page
    filter_query = {}

    # Enforce project visibility for every request, not just project-scoped
    # requests. Port documents store project IDs as strings.
    project_filter = {} if current_user["role"] == "admin" else {
        "created_by": str(current_user["_id"])
    }
    accessible_projects = [str(p["_id"]) async for p in db.projects.find(project_filter, {"_id": 1})]
    filter_query["project_id"] = {"$in": accessible_projects}

    if asset_id:
        filter_query["asset_id"] = asset_id
    if project_id:
        filter_query["project_id"] = project_id if project_id in accessible_projects else {"$in": []}
    if asset_id: filter_query["asset_id"] = asset_id
    if scan_id: filter_query["scan_id"] = scan_id
    if hostname: filter_query["hostname"] = {"$regex": hostname, "$options": "i"}
    if ip: filter_query["ip"] = {"$regex": ip, "$options": "i"}
    if port is not None: filter_query["port"] = port
    if protocol: filter_query["protocol"] = protocol.lower()
    if state: filter_query["state"] = state
    if service: filter_query["service"] = {"$regex": service, "$options": "i"}
    if date_from or date_to:
        date_filter = {}
        if date_from:
            date_filter["$gte"] = datetime.fromisoformat(date_from.replace("Z", "+00:00")).replace(tzinfo=None)
        if date_to:
            date_filter["$lt"] = datetime.fromisoformat(date_to.replace("Z", "+00:00")).replace(tzinfo=None) + timedelta(days=1)
        filter_query["last_seen"] = date_filter

    total = await db.ports.count_documents(filter_query)
    cursor = db.ports.find(filter_query).sort([("port", 1), ("hostname", 1)]).skip(skip).limit(per_page)
    ports = await cursor.to_list(length=per_page)

    # Convert ObjectId to string
    for port in ports:
        port["id"] = str(port["_id"])
        del port["_id"]

    project_ids = {p.get("project_id") for p in ports if p.get("project_id")}
    scan_ids = {p.get("scan_id") for p in ports if p.get("scan_id")}
    project_docs = await db.projects.find({"_id": {"$in": [ObjectId(p) for p in project_ids if ObjectId.is_valid(p)]}}, {"name": 1}).to_list(length=None)
    scan_docs = await db.scans.find({"_id": {"$in": [ObjectId(s) for s in scan_ids if ObjectId.is_valid(s)]}}, {"scan_name": 1, "created_at": 1}).to_list(length=None)
    projects = {str(p["_id"]): p.get("name", "Unknown project") for p in project_docs}
    scans = {str(s["_id"]): s.get("scan_name", str(s["_id"])) for s in scan_docs}
    for item in ports:
        item["project_name"] = projects.get(item.get("project_id"), "Unknown project")
        item["scan_name"] = scans.get(item.get("scan_id"), item.get("scan_id", "--"))

    return PortListResponse(
        ports=ports,
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/stats", response_model=PortStatsResponse)
async def get_port_stats(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    # Get project IDs that the user has access to
    project_filter = {"created_by": str(current_user["_id"])}
    if current_user["role"] == "admin":
        project_filter = {}
    project_cursor = db.projects.find(project_filter, {"_id": 1})
    project_ids = [str(p["_id"]) async for p in project_cursor]

    if not project_ids:
        return PortStatsResponse(
            total_open_ports=0,
            average_ports_per_asset=0.0,
            most_common_port=None,
            top_open_ports=[],
        )

    filter_query = {"project_id": {"$in": project_ids}}

    total_open_ports = await db.ports.count_documents(filter_query)

    # Average across every accessible asset, including assets with zero open
    # ports. This keeps the dashboard metric an actual ports-per-asset value.
    total_assets = await db.assets.count_documents({"project_id": {"$in": project_ids}})
    average_ports = (total_open_ports / total_assets) if total_assets else 0.0

    # Get top open ports
    top_ports_cursor = db.ports.aggregate([
        {"$match": filter_query},
        {"$group": {"_id": "$port", "count": {"$sum": 1}}},
        {"$sort": {"count": -1, "_id": 1}},
        {"$limit": 10}
    ])
    top_ports = [{"port": p["_id"], "count": p["count"]} async for p in top_ports_cursor]

    most_common_port = top_ports[0]["port"] if top_ports else None

    live_asset_ids = [str(asset["_id"]) async for asset in db.assets.find(
        {"project_id": {"$in": project_ids}, "is_live": True}, {"_id": 1}
    )]
    live_port_assets = await db.ports.distinct("asset_id", {
        **filter_query, "asset_id": {"$in": live_asset_ids}
    })
    live_assets_with_ports = len(live_port_assets)
    services = await db.ports.aggregate([
        {"$match": {**filter_query, "service": {"$nin": [None, ""]}}},
        {"$group": {"_id": "$service", "count": {"$sum": 1}}},
        {"$sort": {"count": -1, "_id": 1}}, {"$limit": 10},
    ]).to_list(length=10)
    common_services = [{"service": s["_id"], "count": s["count"]} for s in services]
    unique_services = len(await db.ports.distinct("service", {**filter_query, "service": {"$nin": [None, ""]}}))
    latest = await db.ports.find_one(filter_query, sort=[("last_seen", -1)])
    project_chart = await db.ports.aggregate([
        {"$match": filter_query}, {"$group": {"_id": "$project_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}, {"$limit": 10},
    ]).to_list(length=10)
    ports_by_project = [{"project_id": p["_id"], "count": p["count"]} for p in project_chart]
    risk_groups = {"Critical": [22, 23, 3389, 5900], "High": [445, 21, 25, 1433, 3306], "Medium": [8080, 8443, 8000], "Low": [80, 443]}
    risk_distribution = [{"risk": label, "count": await db.ports.count_documents({**filter_query, "port": {"$in": ports}})} for label, ports in risk_groups.items()]

    return PortStatsResponse(
        total_open_ports=total_open_ports,
        average_ports_per_asset=average_ports,
        most_common_port=most_common_port,
        top_open_ports=top_ports,
        live_assets_with_ports=live_assets_with_ports,
        unique_services=unique_services,
        last_scan_time=latest.get("last_seen") if latest else None,
        common_services=common_services,
        ports_by_project=ports_by_project,
        risk_distribution=risk_distribution,
    )
