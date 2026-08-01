from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from app.models.asset import AssetStatus
from app.schemas.asset import AssetResponse, AssetListResponse, AssetStatsResponse
from fastapi import HTTPException, status


def _asset_to_response(asset: dict) -> AssetResponse:
    return AssetResponse(
        id=str(asset["_id"]),
        project_id=asset["project_id"],
        scan_id=asset.get("scan_id"),
        hostname=asset["hostname"],
        source=asset.get("source", "Subfinder"),
        status=asset.get("status", AssetStatus.ACTIVE.value),
        first_seen=asset.get("first_seen", asset.get("created_at")),
        last_seen=asset.get("last_seen", asset.get("updated_at")),
        created_at=asset["created_at"],
        updated_at=asset["updated_at"],
        ip=asset.get("ip"),
        http_status=asset.get("http_status"),
        https_enabled=asset.get("https_enabled"),
        final_url=asset.get("final_url"),
        page_title=asset.get("page_title"),
        web_server=asset.get("web_server"),
        content_length=asset.get("content_length"),
        response_time=asset.get("response_time"),
        redirect_location=asset.get("redirect_location"),
        last_http_check=asset.get("last_http_check"),
        is_live=asset.get("is_live"),
        open_ports_count=asset.get("open_ports_count", 0),
        last_port_scan=asset.get("last_port_scan"),
        technology_count=asset.get("technology_count", 0),
        technologies=asset.get("technologies", []),
        last_technology_scan=asset.get("last_technology_scan"),
        dns_records_count=asset.get("dns_records_count", 0),
        dns_last_scan=asset.get("dns_last_scan"),
        mx_records=asset.get("mx_records", []),
        txt_records=asset.get("txt_records", []),
        ns_records=asset.get("ns_records", []),
        spf=asset.get("spf"),
        dmarc=asset.get("dmarc"),
        dkim=asset.get("dkim", []),
    )


async def save_assets(
    db: AsyncIOMotorDatabase,
    project_id: str,
    scan_id: str,
    hostnames: list[str],
    source: str = "Subfinder",
) -> dict:
    now = datetime.utcnow()
    new_count = 0
    updated_count = 0

    for hostname in hostnames:
        existing = await db.assets.find_one({
            "project_id": project_id,
            "hostname": hostname,
        })

        if existing:
            await db.assets.update_one(
                {"_id": existing["_id"]},
                {
                    "$set": {
                        "last_seen": now,
                        "updated_at": now,
                        "scan_id": scan_id,
                    },
                },
            )
            updated_count += 1
        else:
            doc = {
                "project_id": project_id,
                "scan_id": scan_id,
                "hostname": hostname,
                "source": source,
                "status": AssetStatus.ACTIVE.value,
                "first_seen": now,
                "last_seen": now,
                "created_at": now,
                "updated_at": now,
            }
            await db.assets.insert_one(doc)
            new_count += 1

    return {
        "new_count": new_count,
        "updated_count": updated_count,
        "total": new_count + updated_count,
    }


async def list_assets(
    db: AsyncIOMotorDatabase,
    user_id: str,
    user_role: str,
    page: int = 1,
    per_page: int = 50,
    search: str = None,
    source_filter: str = None,
    status_filter: str = None,
    project_id: str = None,
) -> AssetListResponse:
    query = {}

    if user_role != "admin":
        user_projects = await db.projects.find(
            {"created_by": user_id}, {"_id": 1}
        ).to_list(length=None)
        project_ids = [str(p["_id"]) for p in user_projects]
        if project_id:
            if project_id in project_ids:
                query["project_id"] = project_id
            else:
                query["project_id"] = {"$in": []}
        else:
            query["project_id"] = {"$in": project_ids}
    elif project_id:
        query["project_id"] = project_id

    if search:
        query["hostname"] = {"$regex": search, "$options": "i"}

    if source_filter:
        query["source"] = source_filter

    if status_filter:
        query["status"] = status_filter

    total = await db.assets.count_documents(query)
    skip = (page - 1) * per_page
    cursor = db.assets.find(query).sort("created_at", -1).skip(skip).limit(per_page)
    assets = await cursor.to_list(length=per_page)

    return AssetListResponse(
        assets=[_asset_to_response(a) for a in assets],
        total=total,
        page=page,
        per_page=per_page,
    )


async def get_assets_by_project(
    db: AsyncIOMotorDatabase,
    project_id: str,
    user_id: str,
    user_role: str,
    page: int = 1,
    per_page: int = 50,
    search: str = None,
    source_filter: str = None,
) -> AssetListResponse:
    return await list_assets(
        db,
        user_id=user_id,
        user_role=user_role,
        page=page,
        per_page=per_page,
        search=search,
        source_filter=source_filter,
        project_id=project_id,
    )


async def get_asset_stats(db: AsyncIOMotorDatabase) -> AssetStatsResponse:
    total_assets = await db.assets.count_documents({})

    active_assets = await db.assets.count_documents({"status": AssetStatus.ACTIVE.value})

    pipeline = [
        {"$group": {"_id": "$source", "count": {"$sum": 1}}},
    ]
    source_cursor = db.assets.aggregate(pipeline)
    sources = {}
    async for doc in source_cursor:
        sources[doc["_id"]] = doc["count"]

    projects_pipeline = [
        {"$group": {"_id": "$project_id"}},
        {"$count": "total"},
    ]
    projects_cursor = db.assets.aggregate(projects_pipeline)
    projects_with_assets = 0
    async for doc in projects_cursor:
        projects_with_assets = doc.get("total", 0)

    return AssetStatsResponse(
        total_assets=total_assets,
        active_assets=active_assets,
        sources=sources,
        projects_with_assets=projects_with_assets,
    )
