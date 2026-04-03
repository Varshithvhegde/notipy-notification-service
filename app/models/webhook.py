from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .base_class import Base

class Webhook(Base):
    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=False)
    # Comma-separated events to listen to: "sent,failed,delivered"
    events = Column(String, nullable=False, default="sent,failed")
    # Optional: only fire for a specific user. NULL = fire for all users.
    user_id = Column(String, nullable=True, index=True)
    secret = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
