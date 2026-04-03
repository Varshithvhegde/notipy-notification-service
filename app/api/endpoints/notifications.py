from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api.dependencies import get_db
from app.models.notification import Notification, NotificationStatus
from app.schemas.notification import NotificationCreate, NotificationResponse
from app.workers.queue import notification_queue
from app.core.rate_limiter import check_rate_limit

router = APIRouter()

@router.post("/", response_model=List[NotificationResponse])
async def create_notification(noti: NotificationCreate, db: Session = Depends(get_db)):
    check_rate_limit(noti.user_id)
    
    responses = []
    
    for channel in noti.channels:
        # Isolate idempotency per channel so pushing 'email' and 'sms' doesn't block each other
        channel_key = f"{noti.idempotency_key}_{channel}" if noti.idempotency_key else None
        
        if channel_key:
            existing = db.query(Notification).filter(Notification.idempotency_key == channel_key).first()
            if existing:
                responses.append(existing)
                continue
                
        # Save the notification as pending
        db_noti = Notification(
            user_id=noti.user_id,
            channel=channel,
            priority=noti.priority,
            message_body=noti.message_body,
            idempotency_key=channel_key,
            status=NotificationStatus.PENDING
        )
        db.add(db_noti)
        db.commit()
        db.refresh(db_noti)
        
        await notification_queue.enqueue(db_noti.id, priority=db_noti.priority.value, template_vars=noti.template_vars)
        responses.append(db_noti)
        
    return responses

@router.get("/{notification_id}", response_model=NotificationResponse)
def get_notification(notification_id: int, db: Session = Depends(get_db)):
    noti = db.query(Notification).filter(Notification.id == notification_id).first()
    if not noti:
        raise HTTPException(status_code=404, detail="Notification not found")
    return noti

@router.get("/user/{user_id}", response_model=List[NotificationResponse])
def get_user_notifications(user_id: str, db: Session = Depends(get_db)):
    return db.query(Notification).filter(Notification.user_id == user_id).order_by(Notification.created_at.desc()).all()
