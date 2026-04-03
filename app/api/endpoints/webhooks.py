from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.api.dependencies import get_db
from app.models.webhook import Webhook
from app.schemas.webhook import WebhookCreate, WebhookResponse

router = APIRouter()

@router.post("/", response_model=WebhookResponse, status_code=201)
async def register_webhook(payload: WebhookCreate, db: AsyncSession = Depends(get_db)):
    """Register a new webhook URL to receive delivery status events."""
    hook = Webhook(
        url=payload.url,
        events=",".join(payload.events),
        user_id=payload.user_id,
        secret=payload.secret,
        is_active=True,
    )
    db.add(hook)
    await db.commit()
    await db.refresh(hook)
    return hook

@router.get("/", response_model=List[WebhookResponse])
async def list_webhooks(db: AsyncSession = Depends(get_db)):
    """List all registered webhooks."""
    result = await db.execute(select(Webhook).order_by(Webhook.created_at.desc()))
    return result.scalars().all()

@router.delete("/{webhook_id}", status_code=204)
async def delete_webhook(webhook_id: int, db: AsyncSession = Depends(get_db)):
    """Unregister (delete) a webhook by ID."""
    result = await db.execute(select(Webhook).where(Webhook.id == webhook_id))
    hook = result.scalars().first()
    if not hook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    await db.delete(hook)
    await db.commit()

@router.patch("/{webhook_id}/toggle", response_model=WebhookResponse)
async def toggle_webhook(webhook_id: int, db: AsyncSession = Depends(get_db)):
    """Pause or resume a webhook without deleting it."""
    result = await db.execute(select(Webhook).where(Webhook.id == webhook_id))
    hook = result.scalars().first()
    if not hook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    hook.is_active = not hook.is_active
    await db.commit()
    await db.refresh(hook)
    return hook
