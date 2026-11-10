from enum import Enum
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class UserRole(str, Enum):
    ADMIN = "admin"
    THREAT_ANALYST = "threat_analyst"
    SOC_ANALYST = "soc_analyst"
    VIEWER = "viewer"


class UserModel(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    full_name: str
    email: str
    hashed_password: str
    role: UserRole = UserRole.THREAT_ANALYST
    is_active: bool = True
    email_verified: bool = False
    verification_token: Optional[str] = None
    verification_token_expires: Optional[datetime] = None
    reset_token: Optional[str] = None
    reset_token_expires: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True


ROLE_HIERARCHY = {
    UserRole.ADMIN: 4,
    UserRole.THREAT_ANALYST: 3,
    UserRole.SOC_ANALYST: 2,
    UserRole.VIEWER: 1,
}
