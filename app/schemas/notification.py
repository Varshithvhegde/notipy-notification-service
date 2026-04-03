from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from app.models.notification import NotificationStatus, NotificationPriority

ChannelType = Literal['email', 'sms', 'push']

class NotificationCreate(BaseModel):
    user_id: str
    channel: ChannelType
    priority: NotificationPriority = NotificationPriority.NORMAL
    message_body: str
    idempotency_key: Optional[str] = None
    template_vars: Optional[dict] = None

class NotificationResponse(BaseModel):
    id: int
    user_id: str
    channel: ChannelType
    priority: NotificationPriority
    status: NotificationStatus
    message_body: str
    idempotency_key: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
