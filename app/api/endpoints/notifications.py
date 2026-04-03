from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
import math

from app.api.dependencies import get_db
from app.models.notification import Notification, NotificationStatus
from app.models.template import NotificationTemplate
from app.schemas.notification import NotificationCreate, NotificationResponse, PaginatedNotificationResponse, NotificationBatchCreate
from app.workers.queue import notification_queue
from app.core.rate_limiter import check_rate_limit

router = APIRouter()

async def process_single_notification(noti: NotificationCreate, db: AsyncSession):
    """Internal helper to create notifications per channel and enqueue them."""
    check_rate_limit(noti.user_id)
    
    # 1. Resolve message body from template or payload
    final_body = noti.message_body
    
    if noti.template_name:
        res = await db.execute(select(NotificationTemplate).where(NotificationTemplate.name == noti.template_name))
        tpl = res.scalars().first()
        if not tpl:
            raise HTTPException(status_code=400, detail=f"Drafting logic failed: Template '{noti.template_name}' not found locally.")
        final_body = tpl.body
        
    if not final_body:
        raise HTTPException(status_code=400, detail="Missing notification content: provide either 'message_body' or a valid 'template_name'.")

    responses = []
    
    for channel in noti.channels:
        channel_key = f"{noti.idempotency_key}_{channel}" if noti.idempotency_key else None
        
        if channel_key:
            # ... (lookup logic remains same)
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
            message_body=final_body,
            idempotency_key=channel_key,
            status=NotificationStatus.PENDING
        )
        db.add(db_noti)
        # Flush to get ID without full commit yet (Batch API will commit all at once)
        await db.flush() 
        
        await notification_queue.enqueue(db_noti.id, priority=db_noti.priority.value, template_vars=noti.template_vars)
        responses.append(db_noti)
    return responses

@router.post("/", response_model=List[NotificationResponse])
async def create_notification(noti: NotificationCreate, db: AsyncSession = Depends(get_db)):
    """Single-user multi-channel notification dispatch."""
    results = await process_single_notification(noti, db)
    await db.commit()
    return results

@router.post("/batch", response_model=dict)
async def create_batch_notifications(batch: NotificationBatchCreate, db: AsyncSession = Depends(get_db)):
    """Batch API: Dispatch notifications for multiple users simultaneously."""
    total_queued = 0
    for noti in batch.notifications:
        # Each user has their own rate limit checked inside the helper
        try:
            results = await process_single_notification(noti, db)
            total_queued += len(results)
        except HTTPException as e:
            # If one user in the batch fails rate limit, we can log it but continue?
            # Or stop? Let's log it and continue for the others in the batch.
            continue
            
    await db.commit()
    return {"status": "success", "queued_count": total_queued}

@router.get("/user/{user_id}", response_model=PaginatedNotificationResponse)
async def get_user_notifications(
    user_id: str,
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=10, ge=1, le=100, description="Results per page"),
    db: AsyncSession = Depends(get_db)
):
    offset = (page - 1) * page_size
    count_result = await db.execute(select(func.count()).select_from(Notification).where(Notification.user_id == user_id))
    total = count_result.scalar_one()
    data_result = await db.execute(select(Notification).where(Notification.user_id == user_id).order_by(Notification.created_at.desc()).offset(offset).limit(page_size))
    items = data_result.scalars().all()
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    return PaginatedNotificationResponse(items=items, total=total, page=page, page_size=page_size, total_pages=total_pages, has_next=page < total_pages, has_prev=page > 1)

@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(notification_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Notification).where(Notification.id == notification_id))
    noti = result.scalars().first()
    if not noti:
        raise HTTPException(status_code=404, detail="Notification not found")
    return noti
