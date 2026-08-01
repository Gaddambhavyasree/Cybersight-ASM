from fastapi import APIRouter, Depends, Query
from app.database import get_database
from app.schemas.asset import AssetResponse, AssetListResponse, AssetStatsResponse
from app.services.asset_service import (
    list_assets, get_assets_by_project, get_asset_stats,
)
from app.dependencies.auth import get_current_user
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(prefix="/api/assets", tags=["Assets"])


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
