from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.scan import ScanStatus, ScanStage


class StartScanRequest(BaseModel):
    project_id: str = Field(..., min_length=1)
    scan_name: str = Field(..., min_length=1, max_length=200)


class ScanLogResponse(BaseModel):
    message: str
    timestamp: datetime
    level: str


class ScanResponse(BaseModel):
    id: str
    project_id: str
    project_name: Optional[str] = None
    target_domain: Optional[str] = None
    scan_name: str
    status: ScanStatus
    current_stage: ScanStage
    progress: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    failure_stage: Optional[ScanStage] = None
    failure_message: Optional[str] = None
    assets_count: int = 0
    logs: list[ScanLogResponse] = []
    initiated_by: str
    initiated_by_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ScanListResponse(BaseModel):
    scans: list[ScanResponse]
    total: int
    page: int
    per_page: int
