from fastapi import APIRouter, Depends, Query
from app.database import get_database
from app.schemas.scan import StartScanRequest, ScanResponse, ScanListResponse
from app.schemas.user import MessageResponse
from app.services.scan_service import (
    start_scan, list_scans, get_scan, cancel_scan, delete_scan,
)
from app.dependencies.auth import get_current_user
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(prefix="/api/scans", tags=["Scans"])


@router.post("/start", response_model=ScanResponse, status_code=201)
async def start(
    data: StartScanRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    return await start_scan(
        db, data,
        user_id=str(current_user["_id"]),
        user_name=current_user["full_name"],
    )


@router.get("", response_model=ScanListResponse)
async def list_all(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: str = Query(None),
    status: str = Query(None),
    project_id: str = Query(None),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    return await list_scans(
        db,
        user_id=str(current_user["_id"]),
        user_role=current_user["role"],
        page=page,
        per_page=per_page,
        search=search,
        status_filter=status,
        project_id=project_id,
    )


@router.get("/{scan_id}", response_model=ScanResponse)
async def get_one(
    scan_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    return await get_scan(
        db, scan_id,
        user_id=str(current_user["_id"]),
        user_role=current_user["role"],
    )


@router.patch("/{scan_id}/cancel", response_model=ScanResponse)
async def cancel(
    scan_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    return await cancel_scan(
        db, scan_id,
        user_id=str(current_user["_id"]),
        user_role=current_user["role"],
    )


@router.delete("/{scan_id}", response_model=MessageResponse)
async def delete(
    scan_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    result = await delete_scan(
        db, scan_id,
        user_id=str(current_user["_id"]),
        user_role=current_user["role"],
    )
    return MessageResponse(message=result["message"])
