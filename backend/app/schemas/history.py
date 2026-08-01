from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field

class HistoryScan(BaseModel):
    id: str
    scan_id: str
    project_id: str
    project_name: Optional[str] = None
    scan_name: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    status: str = "completed"
    counts: dict[str, int] = Field(default_factory=dict)
    risk_score: int = 0
    risk_level: str = "Very Low"

class HistoryList(BaseModel):
    records: list[HistoryScan]
    total: int
    page: int
    per_page: int

class HistoryDetail(BaseModel):
    scan: HistoryScan
    statistics: dict[str, Any] = Field(default_factory=dict)
    timeline: list[dict[str, Any]] = Field(default_factory=list)

class ScanComparison(BaseModel):
    previous: HistoryScan
    current: HistoryScan
    changes: dict[str, Any] = Field(default_factory=dict)
    summary: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
