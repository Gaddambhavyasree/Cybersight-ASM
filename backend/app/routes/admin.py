from fastapi import APIRouter, Depends, Query
from app.database import get_database
from app.schemas.user import (
    UserListResponse, UserResponse, UpdateRoleRequest,
    ToggleActiveRequest, MessageResponse
)
from app.services.user_service import (
    list_users, update_user_role, toggle_user_active, delete_user
)
from app.dependencies.auth import require_admin
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/users", response_model=UserListResponse)
async def get_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: str = Query(None),
    current_user: dict = Depends(require_admin),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    return await list_users(db, page, per_page, search)


@router.put("/users/{user_id}/role", response_model=UserResponse)
async def change_user_role(
    user_id: str,
    data: UpdateRoleRequest,
    current_user: dict = Depends(require_admin),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    return await update_user_role(db, user_id, data)


@router.put("/users/{user_id}/active", response_model=UserResponse)
async def toggle_user_active_endpoint(
    user_id: str,
    data: ToggleActiveRequest,
    current_user: dict = Depends(require_admin),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    return await toggle_user_active(db, user_id, data)


@router.delete("/users/{user_id}", response_model=MessageResponse)
async def delete_user_endpoint(
    user_id: str,
    current_user: dict = Depends(require_admin),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    result = await delete_user(db, user_id)
    return MessageResponse(message=result["message"])
