import enum
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum
from datetime import datetime, timezone
from .base_class import Base

class NotificationStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"

class NotificationPriority(str, enum.Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    channel = Column(String)  # email, sms, push
    priority = Column(SQLEnum(NotificationPriority), default=NotificationPriority.NORMAL)
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.PENDING)
    message_body = Column(String)
    idempotency_key = Column(String, index=True, unique=True, nullable=True) # Used for deduplication
    retry_count = Column(Integer, default=0)
    error_message = Column(String, nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
