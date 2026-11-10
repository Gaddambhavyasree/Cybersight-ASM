from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DNSRecordResponse(BaseModel):
    id: str
    project_id: str
    scan_id: str
    asset_id: str
    hostname: str
    record_type: str
    record_value: str
    ttl: Optional[int] = None
    source: str
    first_seen: datetime
    last_seen: datetime
    created_at: datetime
    updated_at: datetime
    project_name: Optional[str] = None
    scan_name: Optional[str] = None


class DNSRecordListResponse(BaseModel):
    records: list[DNSRecordResponse]
    total: int
    page: int
    per_page: int


class DNSRecordDetailResponse(DNSRecordResponse):
    related_records: list[DNSRecordResponse] = []


class DNSStatsResponse(BaseModel):
    total_dns_records: int = 0
    assets_with_dns_records: int = 0
    mx_records: int = 0
    txt_records: int = 0
    dnssec_enabled: int = 0
    last_scan_time: Optional[datetime] = None
    record_distribution: list[dict] = []
    top_mx_domains: list[dict] = []
    assets_per_record_type: list[dict] = []
