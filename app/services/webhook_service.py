"""
Webhook Service — fires registered webhook URLs when notification status changes.
Uses httpx for async HTTP delivery with a 5s timeout.
Signs the payload with HMAC-SHA256 if the webhook has a secret configured.
"""
import hmac
import hashlib
import json
import logging
import httpx
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

async def fire_webhooks(notification_id: int, user_id: str, status: str, channel: str):
    """
    Queries all active webhooks that match the event and optionally the user_id,
    then fires them concurrently via async HTTP POST.
    """
    from app.db.database import SessionLocal
    from app.models.webhook import Webhook
    from sqlalchemy import select

    async with SessionLocal() as db:
        result = await db.execute(
            select(Webhook).where(Webhook.is_active == True)
        )
        all_hooks = result.scalars().all()

    # Filter to hooks that care about this event and this user
    matching = [
        h for h in all_hooks
        if status in h.events.split(",")
        and (h.user_id is None or h.user_id == user_id)
    ]

    if not matching:
        return

    payload = {
        "event": status,
        "notification_id": notification_id,
        "user_id": user_id,
        "channel": channel,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    body = json.dumps(payload)

    async with httpx.AsyncClient(timeout=5.0) as client:
        for hook in matching:
            headers = {"Content-Type": "application/json"}

            # HMAC-SHA256 signature if secret is set
            if hook.secret:
                sig = hmac.new(
                    hook.secret.encode(), body.encode(), hashlib.sha256
                ).hexdigest()
                headers["X-Klarixa-Signature"] = f"sha256={sig}"

            try:
                resp = await client.post(hook.url, content=body, headers=headers)
                logger.info(f"[WEBHOOK] Fired to {hook.url} → HTTP {resp.status_code}")
            except Exception as e:
                logger.warning(f"[WEBHOOK] Failed to deliver to {hook.url}: {e}")
