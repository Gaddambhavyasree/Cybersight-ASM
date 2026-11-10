from datetime import datetime
from typing import Optional
from pydantic import BaseModel
class WebAssetResponse(BaseModel):
    id: str; project_id: str; scan_id: str; asset_id: str; hostname: str; base_url: str; url: str; path: str; query: Optional[str] = None; method: str = "GET"; status_code: Optional[int] = None; content_type: Optional[str] = None; resource_type: str; depth: int = 0; title: Optional[str] = None; is_sensitive: bool = False; sensitive_reason: Optional[str] = None; source: str; first_seen: datetime; last_seen: datetime; created_at: datetime; updated_at: datetime; project_name: Optional[str] = None; scan_name: Optional[str] = None
class WebAssetListResponse(BaseModel):
    records: list[WebAssetResponse]; total: int; page: int; per_page: int
class WebStatsResponse(BaseModel):
    total_urls: int = 0; sensitive_endpoints: int = 0; javascript_files: int = 0; api_endpoints: int = 0; admin_panels: int = 0; last_crawl: Optional[datetime] = None; resource_types: list[dict] = []; sensitive_distribution: list[dict] = []; hosts: list[dict] = []
