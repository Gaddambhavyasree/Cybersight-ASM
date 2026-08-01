from enum import Enum
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class AssetStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    UNKNOWN = "unknown"


class AssetSource(str, Enum):
    SUBFINDER = "Subfinder"
    AMASS = "Amass"
    MANUAL = "Manual"


class AssetModel(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    project_id: str
    scan_id: Optional[str] = None
    hostname: str
    source: str = AssetSource.SUBFINDER.value
    status: AssetStatus = AssetStatus.ACTIVE
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

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
    ssl_enabled: Optional[bool] = None
    certificate_expiry: Optional[datetime] = None
    days_remaining: Optional[int] = None
    tls_version: Optional[str] = None
    cipher: Optional[str] = None
    ssl_grade: Optional[str] = None
    ssl_last_scan: Optional[datetime] = None
    endpoint_count: Optional[int] = None
    javascript_files: Optional[int] = None
    api_count: Optional[int] = None
    admin_panels: Optional[int] = None
    crawl_last_scan: Optional[datetime] = None
    critical_count: Optional[int] = None
    high_count: Optional[int] = None
    medium_count: Optional[int] = None
    low_count: Optional[int] = None
    info_count: Optional[int] = None
    total_vulnerabilities: Optional[int] = None
    last_vulnerability_scan: Optional[datetime] = None
    risk_score: Optional[int] = None
    risk_level: Optional[str] = None
    risk_factors: list[str] = []
    risk_breakdown: dict = {}
    risk_recommendations: list[str] = []
    last_risk_calculation: Optional[datetime] = None

    class Config:
        populate_by_name = True


class PortModel(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    project_id: str
    scan_id: str
    asset_id: str
    hostname: str
    ip: Optional[str] = None
    port: int
    protocol: str = "tcp"
    state: str = "open"
    service: Optional[str] = None
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
