from enum import Enum
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ProjectStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class ProjectModel(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    name: str
    organization: Optional[str] = None
    target_domain: str
    description: Optional[str] = None
    tags: list[str] = []
    status: ProjectStatus = ProjectStatus.ACTIVE
    created_by: str
    created_by_name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
