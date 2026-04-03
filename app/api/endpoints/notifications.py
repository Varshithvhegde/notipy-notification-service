from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
import math

from app.api.dependencies import get_db
from app.models.notification import Notification, NotificationStatus
from app.schemas.notification import NotificationCreate, NotificationResponse, PaginatedNotificationResponse
from app.workers.queue import notification_queue
from app.core.rate_limiter import check_rate_limit

router = APIRouter()

@router.post("/", response_model=List[NotificationResponse])
async def create_notification(noti: NotificationCreate, db: AsyncSession = Depends(get_db)):
    check_rate_limit(noti.user_id)
    
    responses = []
    
    for channel in noti.channels:
        channel_key = f"{noti.idempotency_key}_{channel}" if noti.idempotency_key else None
        
        if channel_key:
            result = await db.execute(
                select(Notification).where(Notification.idempotency_key == channel_key)
            )
            existing = result.scalars().first()
            if existing:
                responses.append(existing)
                continue
                
        db_noti = Notification(
            user_id=noti.user_id,
            channel=channel,
            priority=noti.priority,
            message_body=noti.message_body,
            idempotency_key=channel_key,
            status=NotificationStatus.PENDING
        )
        db.add(db_noti)
        await db.commit()
        await db.refresh(db_noti)
        
        await notification_queue.enqueue(db_noti.id, priority=db_noti.priority.value, template_vars=noti.template_vars)
        responses.append(db_noti)
        
    return responses


@router.get("/user/{user_id}", response_model=PaginatedNotificationResponse)
async def get_user_notifications(
    user_id: str,
    page: int = Query(default=1, ge=1, description="Page number (starts at 1)"),
    page_size: int = Query(default=10, ge=1, le=100, description="Results per page (max 100)"),
    db: AsyncSession = Depends(get_db)
):
    offset = (page - 1) * page_size

    # Total count query
    count_result = await db.execute(
        select(func.count()).select_from(Notification).where(Notification.user_id == user_id)
    )
    total = count_result.scalar_one()

    # Paginated data query
    data_result = await db.execute(
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    items = data_result.scalars().all()

    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return PaginatedNotificationResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(notification_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Notification).where(Notification.id == notification_id)
    )
    noti = result.scalars().first()
    if not noti:
        raise HTTPException(status_code=404, detail="Notification not found")
    return noti
