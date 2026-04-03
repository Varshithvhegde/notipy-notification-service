from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class TemplateCreate(BaseModel):
    name: str # e.g. "order_shipped"
    subject: Optional[str] = None
    body: str # e.g. "Hello {{name}}, your order #{{order_id}} is on the way!"
    allowed_channels: List[str] = ["email", "sms", "push"]

class TemplateResponse(BaseModel):
    id: int
    name: str
    subject: Optional[str] = None
    body: str
    allowed_channels: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
