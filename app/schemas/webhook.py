from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime

class WebhookCreate(BaseModel):
    url: str
    events: List[str] = ["sent", "failed"]  # e.g. ["sent", "failed", "delivered"]
    user_id: Optional[str] = None           # Scope to a specific user (optional)
    secret: Optional[str] = None            # HMAC secret for signature verification

class WebhookResponse(BaseModel):
    id: int
    url: str
    events: str                             # stored as comma-separated string in DB
    user_id: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
