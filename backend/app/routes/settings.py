from fastapi import APIRouter, Depends
from app.database import get_database
from app.dependencies.auth import get_current_user
from app.schemas.settings import SettingsPayload, SettingsResponse, ConnectionTest
from app.services.settings_service import get_global, update_global, get_user, update_user, test_connection

router = APIRouter(prefix="/api/settings", tags=["Settings"])

@router.get("/global", response_model=SettingsResponse)
async def global_settings(current_user: dict = Depends(get_current_user), db=Depends(get_database)):
    return await get_global(db)

@router.put("/global", response_model=SettingsResponse)
async def save_global(data: SettingsPayload, current_user: dict = Depends(get_current_user), db=Depends(get_database)):
    return await update_global(db, current_user, data.model_dump())

@router.get("/user", response_model=SettingsResponse)
async def user_settings(current_user: dict = Depends(get_current_user), db=Depends(get_database)):
    return await get_user(db, current_user)

@router.put("/user", response_model=SettingsResponse)
async def save_user(data: SettingsPayload, current_user: dict = Depends(get_current_user), db=Depends(get_database)):
    return await update_user(db, current_user, data.model_dump())

@router.post("/integrations/test")
async def connection(data: ConnectionTest, current_user: dict = Depends(get_current_user), db=Depends(get_database)):
    return await test_connection(db, current_user, data.provider)
