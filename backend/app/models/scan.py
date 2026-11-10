from enum import Enum
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ScanStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScanStage(str, Enum):
    WAITING = "waiting"
    ASSET_DISCOVERY = "asset_discovery"
    LIVE_HOST_DETECTION = "live_host_detection"
    PORT_SCANNING = "port_scanning"
    TECHNOLOGY_DETECTION = "technology_detection"
    DNS_INTELLIGENCE = "dns_intelligence"
    SSL_ANALYSIS = "ssl_analysis"
    WEB_CRAWLING = "web_crawling"
    VULNERABILITY_ASSESSMENT = "vulnerability_assessment"
    THREAT_INTELLIGENCE = "threat_intelligence"
    RISK_ASSESSMENT = "risk_assessment"
    COMPLETED = "completed"


class ScanLog(BaseModel):
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: str = "info"


class ScanModel(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    project_id: str
    project_name: Optional[str] = None
    target_domain: Optional[str] = None
    scan_name: str
    status: ScanStatus = ScanStatus.PENDING
    current_stage: ScanStage = ScanStage.WAITING
    progress: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    failure_stage: Optional[ScanStage] = None
    failure_message: Optional[str] = None
    assets_count: int = 0
    logs: list[ScanLog] = []
    initiated_by: str
    initiated_by_name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
