from typing import Any
from pydantic import BaseModel, Field

class SettingsPayload(BaseModel):
    settings: dict[str, Any] = Field(default_factory=dict)

class SettingsResponse(BaseModel):
    settings: dict[str, Any] = Field(default_factory=dict)

class ConnectionTest(BaseModel):
    provider: str
