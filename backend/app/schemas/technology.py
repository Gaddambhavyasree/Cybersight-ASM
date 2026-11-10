from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class TechnologyResponse(BaseModel):
    id: str
    project_id: str
    scan_id: str
    asset_id: str
    hostname: str
    ip: Optional[str] = None
    technology_name: str
    category: str
    version: Optional[str] = None
    source: str
    confidence: float = 1.0
    first_seen: datetime
    last_seen: datetime
    created_at: datetime
    updated_at: datetime
    project_name: Optional[str] = None
    scan_name: Optional[str] = None

class TechnologyListResponse(BaseModel):
    technologies: list[TechnologyResponse]
    total: int
    page: int
    per_page: int

class TechnologyStatsResponse(BaseModel):
    total_technologies: int
    unique_technologies: int
    most_used_technology: Optional[str] = None
    frameworks_detected: int = 0
    programming_languages: int = 0
    last_scan_time: Optional[datetime] = None
    top_technologies: list[dict] = []
    categories: list[dict] = []
    frameworks: list[dict] = []
    web_servers: list[dict] = []
