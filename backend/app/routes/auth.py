from fastapi import APIRouter, Depends
from app.database import get_database
from app.schemas.user import (
    RegisterRequest, VerifyEmailRequest, LoginRequest,
    ForgotPasswordRequest, ResetPasswordRequest, MessageResponse, TokenResponse
)
from app.services.auth_service import (
    register_user, verify_email, login_user,
    forgot_password, reset_password
)
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=MessageResponse, status_code=201)
async def register(data: RegisterRequest, db: AsyncIOMotorDatabase = Depends(get_database)):
    result = await register_user(db, data)
    return MessageResponse(message=result["message"])


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email_endpoint(data: VerifyEmailRequest, db: AsyncIOMotorDatabase = Depends(get_database)):
    result = await verify_email(db, data.token)
    return MessageResponse(message=result["message"])


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncIOMotorDatabase = Depends(get_database)):
    return await login_user(db, data)


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password_endpoint(data: ForgotPasswordRequest, db: AsyncIOMotorDatabase = Depends(get_database)):
    result = await forgot_password(db, data)
    return MessageResponse(message=result["message"])


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password_endpoint(data: ResetPasswordRequest, db: AsyncIOMotorDatabase = Depends(get_database)):
    result = await reset_password(db, data)
    return MessageResponse(message=result["message"])
