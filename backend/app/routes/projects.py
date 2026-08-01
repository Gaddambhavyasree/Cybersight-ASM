from fastapi import APIRouter, Depends, Query
from app.database import get_database
from app.schemas.project import (
    CreateProjectRequest, UpdateProjectRequest,
    ProjectResponse, ProjectListResponse,
)
from app.schemas.user import MessageResponse
from app.services.project_service import (
    create_project, list_projects, get_project,
    update_project, delete_project,
)
from app.dependencies.auth import get_current_user
from app.models.user import UserRole
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(prefix="/api/projects", tags=["Projects"])


@router.post("", response_model=ProjectResponse, status_code=201)
async def create(
    data: CreateProjectRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    return await create_project(
        db, data,
        user_id=str(current_user["_id"]),
        user_name=current_user["full_name"],
    )


@router.get("", response_model=ProjectListResponse)
async def list_all(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: str = Query(None),
    status: str = Query(None),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    return await list_projects(
        db,
        user_id=str(current_user["_id"]),
        user_role=current_user["role"],
        page=page,
        per_page=per_page,
        search=search,
        status_filter=status,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_one(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    return await get_project(
        db, project_id,
        user_id=str(current_user["_id"]),
        user_role=current_user["role"],
    )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update(
    project_id: str,
    data: UpdateProjectRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    return await update_project(
        db, project_id, data,
        user_id=str(current_user["_id"]),
        user_role=current_user["role"],
    )


@router.delete("/{project_id}", response_model=MessageResponse)
async def delete(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    result = await delete_project(
        db, project_id,
        user_id=str(current_user["_id"]),
        user_role=current_user["role"],
    )
    return MessageResponse(message=result["message"])
