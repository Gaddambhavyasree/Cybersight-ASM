import asyncio
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.user import UserModel, UserRole
from app.schemas.user import (
    RegisterRequest, LoginRequest, ForgotPasswordRequest,
    ResetPasswordRequest, UserResponse, TokenResponse
)
from app.utils.security import hash_password, verify_password, generate_token, hash_token
from app.utils.token import create_access_token
from app.services.email_service import send_verification_email, send_reset_password_email
from fastapi import HTTPException, status
from pymongo.errors import DuplicateKeyError
import logging

logger = logging.getLogger(__name__)

VERIFICATION_TOKEN_EXPIRY_HOURS = 24
RESET_TOKEN_EXPIRY_HOURS = 1


async def register_user(db: AsyncIOMotorDatabase, data: RegisterRequest) -> dict:
    if data.password != data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )

    email = str(data.email).strip().lower()
    full_name = data.full_name.strip()

    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists"
        )

    verification_token = generate_token()
    token_hash = hash_token(verification_token)

    user_doc = {
        "full_name": full_name,
        "email": email,
        "hashed_password": hash_password(data.password),
        "role": UserRole.THREAT_ANALYST.value,
        "is_active": True,
        "email_verified": True,
        "verification_token": token_hash,
        "verification_token_expires": datetime.utcnow() + timedelta(hours=VERIFICATION_TOKEN_EXPIRY_HOURS),
        "reset_token": None,
        "reset_token_expires": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    try:
        result = await db.users.insert_one(user_doc)
    except DuplicateKeyError:
        # The unique database index is the final authority when two requests
        # try to register the same email at the same time.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists"
        ) from None

    asyncio.get_event_loop().run_in_executor(
        None,
        lambda: send_verification_email(email, verification_token, full_name),
    )

    return {
        "message": "Registration successful.",
        "user_id": str(result.inserted_id),
        "verification_token": verification_token,
    }


async def verify_email(db: AsyncIOMotorDatabase, token: str) -> dict:
    token_hash = hash_token(token)

    user = await db.users.find_one({
        "verification_token": token_hash,
        "verification_token_expires": {"$gt": datetime.utcnow()}
    })

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )

    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {
            "email_verified": True,
            "verification_token": None,
            "verification_token_expires": None,
            "updated_at": datetime.utcnow(),
        }}
    )

    return {"message": "Email verified successfully. You can now log in."}


async def login_user(db: AsyncIOMotorDatabase, data: LoginRequest) -> TokenResponse:
    email = str(data.email).strip().lower()
    user = await db.users.find_one({"email": email})

    password_is_valid = False
    if user:
        try:
            password_is_valid = verify_password(data.password, user["hashed_password"])
        except (KeyError, TypeError, ValueError):
            # A malformed legacy record must not turn a failed sign-in into a
            # server error or reveal details about the account.
            logger.warning("User %s has an invalid stored password hash", user.get("_id"))

    if not user or not password_is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Contact an administrator."
        )

    if not user.get("email_verified", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before logging in"
        )

    access_token = create_access_token(data={"sub": str(user["_id"]), "role": user["role"]})

    user_response = UserResponse(
        id=str(user["_id"]),
        full_name=user["full_name"],
        email=user["email"],
        role=user["role"],
        is_active=user["is_active"],
        email_verified=user["email_verified"],
        created_at=user["created_at"],
    )

    return TokenResponse(access_token=access_token, user=user_response)


async def forgot_password(db: AsyncIOMotorDatabase, data: ForgotPasswordRequest) -> dict:
    user = await db.users.find_one({"email": data.email.lower()})

    if not user:
        return {"message": "If an account with this email exists, a reset link has been sent."}

    reset_token = generate_token()
    token_hash = hash_token(reset_token)

    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {
            "reset_token": token_hash,
            "reset_token_expires": datetime.utcnow() + timedelta(hours=RESET_TOKEN_EXPIRY_HOURS),
            "updated_at": datetime.utcnow(),
        }}
    )

    send_reset_password_email(data.email, reset_token, user["full_name"])

    return {"message": "If an account with this email exists, a reset link has been sent."}


async def reset_password(db: AsyncIOMotorDatabase, data: ResetPasswordRequest) -> dict:
    if data.password != data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )

    token_hash = hash_token(data.token)

    user = await db.users.find_one({
        "reset_token": token_hash,
        "reset_token_expires": {"$gt": datetime.utcnow()}
    })

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {
            "hashed_password": hash_password(data.password),
            "reset_token": None,
            "reset_token_expires": None,
            "updated_at": datetime.utcnow(),
        }}
    )

    return {"message": "Password reset successful. You can now log in with your new password."}
