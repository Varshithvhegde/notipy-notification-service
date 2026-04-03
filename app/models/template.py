from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime, timezone
from .base_class import Base

class NotificationTemplate(Base):
    __tablename__ = "notification_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False) # e.g. "order_confirmation"
    subject = Column(String, nullable=True)                      # For email
    body = Column(Text, nullable=False)                          # The Jinja2 string
    # Optional: restricts which channels this template works for
    # comma separated: "email,sms"
    allowed_channels = Column(String, default="email,sms,push")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
