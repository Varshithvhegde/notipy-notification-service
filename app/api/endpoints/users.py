from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.api.dependencies import get_db
from app.models.user_preference import UserPreference
from app.schemas.user_preference import UserPreferenceCreate, UserPreferenceResponse

router = APIRouter()

@router.post("/{user_id}/preferences", response_model=UserPreferenceResponse)
def set_user_preference(
    user_id: str, 
    preference: UserPreferenceCreate, 
    db: Session = Depends(get_db)
):
    # Check if preference already exists
    pref = db.query(UserPreference).filter(
        UserPreference.user_id == user_id, 
        UserPreference.channel == preference.channel
    ).first()
    
    if pref:
        pref.is_opted_in = preference.is_opted_in
    else:
        pref = UserPreference(
            user_id=user_id,
            channel=preference.channel,
            is_opted_in=preference.is_opted_in
        )
        db.add(pref)
        
    db.commit()
    db.refresh(pref)
    return pref

@router.get("/{user_id}/preferences", response_model=List[UserPreferenceResponse])
def get_user_preferences(user_id: str, db: Session = Depends(get_db)):
    prefs = db.query(UserPreference).filter(UserPreference.user_id == user_id).all()
    return prefs
