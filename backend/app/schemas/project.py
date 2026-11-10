from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from app.models.project import ProjectStatus
import re


class CreateProjectRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    organization: Optional[str] = Field(None, max_length=200)
    target_domain: str = Field(..., min_length=1, max_length=253)
    description: Optional[str] = Field(None, max_length=2000)
    tags: list[str] = Field(default_factory=list)
    status: ProjectStatus = ProjectStatus.ACTIVE

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Project name is required")
        return v

    @field_validator("target_domain")
    @classmethod
    def validate_domain(cls, v):
        v = v.strip().lower()
        if not v:
            raise ValueError("Target domain is required")
        domain_pattern = re.compile(
            r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
        )
        if not domain_pattern.match(v):
            raise ValueError("Invalid domain format (e.g., example.com)")
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v):
        return [t.strip().lower() for t in v if t.strip()]


class UpdateProjectRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    organization: Optional[str] = Field(None, max_length=200)
    target_domain: Optional[str] = Field(None, min_length=1, max_length=253)
    description: Optional[str] = Field(None, max_length=2000)
    tags: Optional[list[str]] = None
    status: Optional[ProjectStatus] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Project name cannot be empty")
        return v

    @field_validator("target_domain")
    @classmethod
    def validate_domain(cls, v):
        if v is not None:
            v = v.strip().lower()
            if not v:
                raise ValueError("Target domain cannot be empty")
            domain_pattern = re.compile(
                r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
            )
            if not domain_pattern.match(v):
                raise ValueError("Invalid domain format (e.g., example.com)")
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v):
        if v is not None:
            return [t.strip().lower() for t in v if t.strip()]
        return v


class ProjectResponse(BaseModel):
    id: str
    name: str
    organization: Optional[str] = None
    target_domain: str
    description: Optional[str] = None
    tags: list[str] = []
    status: ProjectStatus
    created_by: str
    created_by_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(BaseModel):
    projects: list[ProjectResponse]
    total: int
    page: int
    per_page: int
