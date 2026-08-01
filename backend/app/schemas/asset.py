from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AssetResponse(BaseModel):
    id: str
    project_id: str
    scan_id: Optional[str] = None
    hostname: str
    source: str
    status: str
    first_seen: datetime
    last_seen: datetime
    created_at: datetime
    updated_at: datetime

    ip: Optional[str] = None
    http_status: Optional[int] = None
    https_enabled: Optional[bool] = None
    final_url: Optional[str] = None
    page_title: Optional[str] = None
    web_server: Optional[str] = None
    content_length: Optional[int] = None
    response_time: Optional[float] = None
    redirect_location: Optional[str] = None
    last_http_check: Optional[datetime] = None
    is_live: Optional[bool] = None
    open_ports_count: Optional[int] = None
    last_port_scan: Optional[datetime] = None
    technology_count: Optional[int] = None
    technologies: list[dict] = []
    last_technology_scan: Optional[datetime] = None
    dns_records_count: Optional[int] = None
    dns_last_scan: Optional[datetime] = None
    mx_records: list[str] = []
    txt_records: list[str] = []
    ns_records: list[str] = []
    spf: Optional[str] = None
    dmarc: Optional[str] = None
    dkim: list[str] = []


class AssetListResponse(BaseModel):
    assets: list[AssetResponse]
    total: int
    page: int
    per_page: int


class AssetStatsResponse(BaseModel):
    total_assets: int
    active_assets: int
    sources: dict[str, int]
    projects_with_assets: int


class PortResponse(BaseModel):
    id: str
    project_id: str
    scan_id: str
    asset_id: str
    hostname: str
    ip: Optional[str] = None
    port: int
    protocol: str
    state: str
    service: Optional[str] = None
    first_seen: datetime
    last_seen: datetime
    created_at: datetime
    updated_at: datetime
    project_name: Optional[str] = None
    scan_name: Optional[str] = None


class PortListResponse(BaseModel):
    ports: list[PortResponse]
    total: int
    page: int
    per_page: int


class PortStatsResponse(BaseModel):
    total_open_ports: int
    average_ports_per_asset: float
    most_common_port: Optional[int] = None
    top_open_ports: list[dict[str, int]]
    live_assets_with_ports: int = 0
    unique_services: int = 0
    last_scan_time: Optional[datetime] = None
    common_services: list[dict] = []
    ports_by_project: list[dict] = []
    risk_distribution: list[dict] = []
