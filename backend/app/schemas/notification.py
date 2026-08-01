from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field

class NotificationItem(BaseModel):
    id: str
    project_id: str
    scan_id: str
    asset_id: Optional[str] = None
    type: str
    title: str
    description: str
    severity: str = "Info"
    status: str = "unread"
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

class NotificationList(BaseModel):
    records: list[NotificationItem]
    total: int
    unread_count: int
    page: int
    per_page: int
