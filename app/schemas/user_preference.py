from pydantic import BaseModel
from typing import Literal

ChannelType = Literal['email', 'sms', 'push']

class UserPreferenceBase(BaseModel):
    channel: ChannelType
    is_opted_in: bool = True

class UserPreferenceCreate(UserPreferenceBase):
    pass

class UserPreferenceResponse(UserPreferenceBase):
    user_id: str

    class Config:
        from_attributes = True
