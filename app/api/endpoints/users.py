from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.api.dependencies import get_db
from app.models.user_preference import UserPreference
from app.schemas.user_preference import UserPreferenceCreate, UserPreferenceResponse

router = APIRouter()

@router.post("/{user_id}/preferences", response_model=UserPreferenceResponse)
async def set_user_preference(
    user_id: str, 
    preference: UserPreferenceCreate, 
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(UserPreference).where(
            UserPreference.user_id == user_id,
            UserPreference.channel == preference.channel
        )
    )
    pref = result.scalars().first()
    
    if pref:
        pref.is_opted_in = preference.is_opted_in
    else:
        pref = UserPreference(
            user_id=user_id,
            channel=preference.channel,
            is_opted_in=preference.is_opted_in
        )
        db.add(pref)
        
    await db.commit()
    await db.refresh(pref)
    return pref

@router.get("/{user_id}/preferences", response_model=List[UserPreferenceResponse])
async def get_user_preferences(user_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(UserPreference).where(UserPreference.user_id == user_id)
    )
    return result.scalars().all()
