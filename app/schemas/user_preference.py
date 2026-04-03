from pydantic import BaseModel, ConfigDict
from typing import Literal, Optional

ChannelType = Literal['email', 'sms', 'push']

class UserPreferenceBase(BaseModel):
    channel: ChannelType
    is_opted_in: bool = True

class UserPreferenceCreate(UserPreferenceBase):
    pass

class UserPreferenceBulkUpdate(BaseModel):
    email_enabled: bool = True
    sms_enabled: bool = True
    push_enabled: bool = True

class UserPreferenceResponse(UserPreferenceBase):
    user_id: str
    
    model_config = ConfigDict(from_attributes=True)
