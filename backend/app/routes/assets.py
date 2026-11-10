from fastapi import APIRouter, Depends, Query, HTTPException
from datetime import datetime
from bson import ObjectId
from pydantic import BaseModel, Field
from app.database import get_database
from app.schemas.asset import AssetResponse, AssetListResponse, AssetStatsResponse
from app.services.asset_service import (
    list_assets, get_assets_by_project, get_asset_stats,
)
from app.dependencies.auth import get_current_user
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(prefix="/api/assets", tags=["Assets"])

CONTEXTS = ("production", "staging", "development", "third_party", "cloud_junk", "internal")


class AssetContextUpdate(BaseModel):
    business_context: str | None = None
    tags: list[str] = Field(default_factory=list)
    criticality: int | None = None  # 1 (internal/dev) .. 5 (crown jewel)


async def _owned_asset(db: AsyncIOMotorDatabase, asset_id: str, user: dict) -> dict:
    try:
        oid = ObjectId(asset_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Asset not found")
    asset = await db.assets.find_one({"_id": oid})
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    if str(user.get("role", "")).lower() != "admin":
        project = await db.projects.find_one(
            {"_id": ObjectId(str(asset["project_id"])), "created_by": str(user["_id"])}
        )
        if not project:
            raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.get("", response_model=AssetListResponse)
async def list_all(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    search: str = Query(None),
    source: str = Query(None),
    status: str = Query(None),
    project_id: str = Query(None),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    return await list_assets(
        db,
        user_id=str(current_user["_id"]),
        user_role=current_user["role"],
        page=page,
        per_page=per_page,
        search=search,
        source_filter=source,
        status_filter=status,
        project_id=project_id,
    )


@router.get("/stats", response_model=AssetStatsResponse)
async def stats(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    return await get_asset_stats(db)


@router.get("/project/{project_id}", response_model=AssetListResponse)
async def by_project(
    project_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    search: str = Query(None),
    source: str = Query(None),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    return await get_assets_by_project(
        db,
        project_id=project_id,
        user_id=str(current_user["_id"]),
        user_role=current_user["role"],
        page=page,
        per_page=per_page,
        search=search,
        source_filter=source,
    )


@router.patch("/{asset_id}/context")
async def update_context(
    asset_id: str,
    payload: AssetContextUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Business-context tagging: who owns this and how important is it.

    Feeds the patch-priority engine (business criticality) and risk assessment.
    """
    asset = await _owned_asset(db, asset_id, current_user)
    update: dict = {"updated_at": datetime.utcnow()}
    if payload.business_context is not None:
        if payload.business_context not in CONTEXTS:
            raise HTTPException(status_code=400, detail=f"business_context must be one of {CONTEXTS}")
        update["business_context"] = payload.business_context
    if payload.tags is not None:
        update["tags"] = [t.strip()[:40] for t in payload.tags if isinstance(t, str) and t.strip()][:10]
    if payload.criticality is not None:
        if not isinstance(payload.criticality, int) or not (1 <= payload.criticality <= 5):
            raise HTTPException(status_code=400, detail="criticality must be an integer between 1 and 5")
        update["criticality"] = payload.criticality
    if payload.business_context == "production" and payload.criticality is None and not asset.get("criticality"):
        update["criticality"] = 4
    await db.assets.update_one({"_id": asset["_id"]}, {"$set": update})
    doc = await db.assets.find_one({"_id": asset["_id"]})
    return {
        "message": "Asset context updated",
        "asset": {"id": str(doc["_id"]), "tags": doc.get("tags", []),
                  "business_context": doc.get("business_context"), "criticality": doc.get("criticality")},
    }


@router.get("/{asset_id}/screenshot")
async def screenshot(
    asset_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Serve the stored httpx screenshot for an asset (requires SCREENSHOTS_ENABLED)."""
    from fastapi.responses import FileResponse
    from pathlib import Path
    from app.config import get_settings

    asset = await _owned_asset(db, asset_id, current_user)
    path = asset.get("screenshot_file")
    if not path or not Path(path).is_file():
        settings = get_settings()
        directory = Path(settings.STORAGE_DIR) / "screenshots"
        candidates = sorted(
            directory.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True
        ) if directory.is_dir() else []
        host = (asset.get("hostname") or "").lower()
        match = next((p for p in candidates if host.replace("-", ".") in p.name.lower().replace("-", ".")), None)
        path = str(match) if match else (str(candidates[0]) if candidates else None)
    if not path or not Path(path).is_file():
        raise HTTPException(status_code=404, detail="No screenshot available for this asset")
    return FileResponse(path, media_type="image/png")
