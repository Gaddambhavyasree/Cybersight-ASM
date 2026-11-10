from fastapi import APIRouter, Depends
from app.database import get_database
from app.schemas.user import (
    UserResponse, UpdateProfileRequest, ChangePasswordRequest, MessageResponse
)
from app.services.user_service import get_user_profile, update_user_profile, change_password
from app.dependencies.auth import get_current_user
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_profile(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    return await get_user_profile(db, str(current_user["_id"]))


@router.put("/me", response_model=UserResponse)
async def update_profile(
    data: UpdateProfileRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    return await update_user_profile(db, str(current_user["_id"]), full_name=data.full_name)


@router.post("/change-password", response_model=MessageResponse)
async def change_password_endpoint(
    data: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    result = await change_password(
        db, str(current_user["_id"]),
        data.current_password, data.new_password, data.confirm_password
    )
    return MessageResponse(message=result["message"])
