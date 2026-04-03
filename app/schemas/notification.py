from pydantic import BaseModel, Field
from typing import Optional, Literal, List
from datetime import datetime
from app.models.notification import NotificationStatus, NotificationPriority

ChannelType = Literal['email', 'sms', 'push']

class NotificationCreate(BaseModel):
    user_id: str
    channels: List[ChannelType]
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
    retry_count: int
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PaginatedNotificationResponse(BaseModel):
    items: List[NotificationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
