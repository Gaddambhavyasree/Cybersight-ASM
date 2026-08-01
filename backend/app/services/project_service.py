from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from app.schemas.project import (
    CreateProjectRequest, UpdateProjectRequest,
    ProjectResponse, ProjectListResponse,
)
from fastapi import HTTPException, status


def _project_to_response(project: dict) -> ProjectResponse:
    return ProjectResponse(
        id=str(project["_id"]),
        name=project["name"],
        organization=project.get("organization"),
        target_domain=project["target_domain"],
        description=project.get("description"),
        tags=project.get("tags", []),
        status=project["status"],
        created_by=project["created_by"],
        created_by_name=project.get("created_by_name"),
        created_at=project["created_at"],
        updated_at=project["updated_at"],
    )


async def create_project(
    db: AsyncIOMotorDatabase, data: CreateProjectRequest, user_id: str, user_name: str
) -> ProjectResponse:
    existing = await db.projects.find_one({
        "created_by": user_id,
        "target_domain": data.target_domain,
    })
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A project with this target domain already exists in your account",
        )

    now = datetime.utcnow()
    doc = {
        "name": data.name,
        "organization": data.organization,
        "target_domain": data.target_domain,
        "description": data.description,
        "tags": data.tags,
        "status": data.status.value,
        "created_by": user_id,
        "created_by_name": user_name,
        "created_at": now,
        "updated_at": now,
    }

    result = await db.projects.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _project_to_response(doc)


async def list_projects(
    db: AsyncIOMotorDatabase,
    user_id: str,
    user_role: str,
    page: int = 1,
    per_page: int = 20,
    search: str = None,
    status_filter: str = None,
) -> ProjectListResponse:
    query = {}

    if user_role != "admin":
        query["created_by"] = user_id

    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"organization": {"$regex": search, "$options": "i"}},
            {"target_domain": {"$regex": search, "$options": "i"}},
        ]

    if status_filter:
        query["status"] = status_filter

    total = await db.projects.count_documents(query)
    skip = (page - 1) * per_page
    cursor = db.projects.find(query).sort("created_at", -1).skip(skip).limit(per_page)
    projects = await cursor.to_list(length=per_page)

    return ProjectListResponse(
        projects=[_project_to_response(p) for p in projects],
        total=total,
        page=page,
        per_page=per_page,
    )


async def get_project(
    db: AsyncIOMotorDatabase, project_id: str, user_id: str, user_role: str
) -> ProjectResponse:
    project = await db.projects.find_one({"_id": ObjectId(project_id)})
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if user_role != "admin" and project["created_by"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return _project_to_response(project)


async def update_project(
    db: AsyncIOMotorDatabase,
    project_id: str,
    data: UpdateProjectRequest,
    user_id: str,
    user_role: str,
) -> ProjectResponse:
    project = await db.projects.find_one({"_id": ObjectId(project_id)})
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if user_role != "admin" and project["created_by"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    update_fields = {"updated_at": datetime.utcnow()}
    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        if key == "status" and value is not None:
            update_fields["status"] = value.value
        else:
            update_fields[key] = value

    if "target_domain" in update_data:
        existing = await db.projects.find_one({
            "created_by": project["created_by"],
            "target_domain": update_fields["target_domain"],
            "_id": {"$ne": ObjectId(project_id)},
        })
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A project with this target domain already exists",
            )

    await db.projects.update_one(
        {"_id": ObjectId(project_id)}, {"$set": update_fields}
    )

    updated = await db.projects.find_one({"_id": ObjectId(project_id)})
    return _project_to_response(updated)


async def delete_project(
    db: AsyncIOMotorDatabase, project_id: str, user_id: str, user_role: str
) -> dict:
    project = await db.projects.find_one({"_id": ObjectId(project_id)})
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if user_role != "admin" and project["created_by"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    result = await db.projects.delete_one({"_id": ObjectId(project_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    return {"message": "Project deleted successfully"}
