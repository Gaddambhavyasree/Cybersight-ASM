from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field

class ReportCreate(BaseModel):
    scan_id: str
    report_type: str = "executive"
    name: Optional[str] = None

class ReportItem(BaseModel):
    id: str
    scan_id: str
    project_id: str
    project_name: Optional[str] = None
    scan_name: str
    name: str
    report_type: str
    generated_by: Optional[str] = None
    generated_at: datetime
    status: str = "completed"

class ReportList(BaseModel):
    records: list[ReportItem]
    total: int
    page: int
    per_page: int

class ReportResponse(ReportItem):
    data: dict[str, Any] = Field(default_factory=dict)
