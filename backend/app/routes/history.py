from fastapi import APIRouter, Depends, Query
from app.database import get_database
from app.dependencies.auth import get_current_user
from app.schemas.history import HistoryList, HistoryDetail, ScanComparison
from app.services.history_service import list_history, detail, compare, delete_history

router = APIRouter(prefix="/api/history", tags=["Historical Scans"])

@router.get("", response_model=HistoryList)
async def listing(page: int = Query(1, ge=1), per_page: int = Query(25, ge=1, le=200), project_id: str | None = None, search: str | None = None, status: str = "completed", risk_level: str | None = None, current_user: dict = Depends(get_current_user), db=Depends(get_database)):
    return await list_history(db, current_user, page, per_page, project_id, search, status, risk_level)

@router.get("/compare", response_model=ScanComparison)
async def comparison(previous_id: str, current_id: str, current_user: dict = Depends(get_current_user), db=Depends(get_database)):
    return await compare(db, previous_id, current_id, current_user)

@router.get("/{scan_id}", response_model=HistoryDetail)
async def one(scan_id: str, current_user: dict = Depends(get_current_user), db=Depends(get_database)):
    return await detail(db, scan_id, current_user)

@router.delete("/{scan_id}")
async def remove(scan_id: str, current_user: dict = Depends(get_current_user), db=Depends(get_database)):
    return await delete_history(db, scan_id, current_user)
