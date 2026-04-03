from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal, List
from datetime import datetime
from app.models.notification import NotificationStatus, NotificationPriority

ChannelType = Literal['email', 'sms', 'push']

class NotificationCreate(BaseModel):
    user_id: str
    channels: List[ChannelType]
    priority: NotificationPriority = NotificationPriority.NORMAL
    message_body: Optional[str] = None # Optional if template_name is used
    template_name: Optional[str] = None # DB-backed template name
    idempotency_key: Optional[str] = None
    template_vars: Optional[dict] = None

class NotificationBatchCreate(BaseModel):
    notifications: List[NotificationCreate]

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

    model_config = ConfigDict(from_attributes=True)

class PaginatedNotificationResponse(BaseModel):
    items: List[NotificationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool

class ChannelStats(BaseModel):
    channel: str
    sent: int
    failed: int
    pending: int
    total: int

class AnalyticsResponse(BaseModel):
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    total_notifications: int
    by_channel: List[ChannelStats]
    by_status: dict[str, int]
