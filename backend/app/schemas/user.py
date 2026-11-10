from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from app.models.user import UserRole


class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str

    class Config:
        json_schema_extra = {
            "example": {
                "full_name": "John Doe",
                "email": "john@example.com",
                "password": "SecurePass123!",
                "confirm_password": "SecurePass123!"
            }
        }


class VerifyEmailRequest(BaseModel):
    token: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None


class UserResponse(BaseModel):
    id: str
    full_name: str
    email: str
    role: UserRole
    is_active: bool
    email_verified: bool
    created_at: datetime


class UserListResponse(BaseModel):
    users: list[UserResponse]
    total: int
    page: int
    per_page: int


class UpdateRoleRequest(BaseModel):
    role: UserRole


class ToggleActiveRequest(BaseModel):
    is_active: bool


class MessageResponse(BaseModel):
    message: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
