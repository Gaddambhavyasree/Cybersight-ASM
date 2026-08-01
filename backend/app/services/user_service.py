from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from app.schemas.user import UserResponse, UserListResponse, UpdateRoleRequest, ToggleActiveRequest
from app.utils.security import hash_password
from fastapi import HTTPException, status


def _user_to_response(user: dict) -> UserResponse:
    return UserResponse(
        id=str(user["_id"]),
        full_name=user["full_name"],
        email=user["email"],
        role=user["role"],
        is_active=user.get("is_active", True),
        email_verified=user.get("email_verified", False),
        created_at=user.get("created_at", datetime.utcnow()),
    )


async def get_user_profile(db: AsyncIOMotorDatabase, user_id: str) -> UserResponse:
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return _user_to_response(user)


async def update_user_profile(db: AsyncIOMotorDatabase, user_id: str, full_name: str = None) -> UserResponse:
    update_fields = {"updated_at": datetime.utcnow()}
    if full_name:
        update_fields["full_name"] = full_name.strip()

    await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": update_fields})
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    return _user_to_response(user)


async def change_password(db: AsyncIOMotorDatabase, user_id: str, current_password: str, new_password: str, confirm_password: str):
    if new_password != confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New passwords do not match")

    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    from app.utils.security import verify_password
    if not verify_password(current_password, user["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")

    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {
            "hashed_password": hash_password(new_password),
            "updated_at": datetime.utcnow(),
        }}
    )
    return {"message": "Password changed successfully"}


async def list_users(db: AsyncIOMotorDatabase, page: int = 1, per_page: int = 20, search: str = None) -> UserListResponse:
    query = {}
    if search:
        query["$or"] = [
            {"full_name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
        ]

    total = await db.users.count_documents(query)
    skip = (page - 1) * per_page
    cursor = db.users.find(query).sort("created_at", -1).skip(skip).limit(per_page)
    users = await cursor.to_list(length=per_page)

    return UserListResponse(
        users=[_user_to_response(u) for u in users],
        total=total,
        page=page,
        per_page=per_page,
    )


async def update_user_role(db: AsyncIOMotorDatabase, user_id: str, data: UpdateRoleRequest) -> UserResponse:
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"role": data.role.value, "updated_at": datetime.utcnow()}}
    )
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    return _user_to_response(user)


async def toggle_user_active(db: AsyncIOMotorDatabase, user_id: str, data: ToggleActiveRequest) -> UserResponse:
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"is_active": data.is_active, "updated_at": datetime.utcnow()}}
    )
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    return _user_to_response(user)


async def delete_user(db: AsyncIOMotorDatabase, user_id: str) -> dict:
    result = await db.users.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"message": "User deleted successfully"}
