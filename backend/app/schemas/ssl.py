from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class SSLResponse(BaseModel):
    id: str; project_id: str; scan_id: str; asset_id: str; hostname: str; ip: Optional[str] = None
    issuer: Optional[str] = None; subject: Optional[str] = None; common_name: Optional[str] = None; san: list[str] = []
    tls_version: Optional[str] = None; cipher: Optional[str] = None; signature_algorithm: Optional[str] = None; public_key_algorithm: Optional[str] = None; key_size: Optional[int] = None
    certificate_version: Optional[str] = None; valid_from: Optional[datetime] = None; valid_until: Optional[datetime] = None; days_remaining: Optional[int] = None
    expired: bool = False; self_signed: bool = False; hostname_match: bool = False; hsts_enabled: bool = False; risk_level: str = "low"; findings: list[str] = []
    certificate_chain_length: Optional[int] = None; ocsp_status: Optional[str] = None
    first_seen: datetime; last_seen: datetime; created_at: datetime; updated_at: datetime; project_name: Optional[str] = None; scan_name: Optional[str] = None; related_records: list[dict] = []

class SSLListResponse(BaseModel):
    records: list[SSLResponse]; total: int; page: int; per_page: int

class SSLStatsResponse(BaseModel):
    assets_with_ssl: int = 0; expired_certificates: int = 0; expiring_soon: int = 0; weak_tls_versions: int = 0; average_ssl_grade: Optional[str] = None; last_scan_time: Optional[datetime] = None
    grade_distribution: list[dict] = []; tls_distribution: list[dict] = []; issuer_distribution: list[dict] = []; expiration_timeline: list[dict] = []; weak_tls_usage: list[dict] = []
