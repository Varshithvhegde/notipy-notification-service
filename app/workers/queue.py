import asyncio
import logging
from datetime import datetime, timezone
from app.db.database import SessionLocal
from app.models.notification import Notification, NotificationStatus
from app.models.user_preference import UserPreference
from app.services.providers import get_provider

PRIORITY_MAP = {
    "critical": 0,
    "high": 1,
    "normal": 2,
    "low": 3,
}

logger = logging.getLogger(__name__)

class NotificationQueue:
    def __init__(self):
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._workers: list[asyncio.Task] = []
        self._running = False

    async def enqueue(self, notification_id: int, priority: str = "normal", template_vars: dict = None, attempt: int = 1):
        prio_val = PRIORITY_MAP.get(priority.lower(), 2)
        await self._queue.put((prio_val, notification_id, template_vars, attempt))

    async def start(self, workers: int = 2):
        self._running = True
        for i in range(workers):
            task = asyncio.create_task(self._worker(i))
            self._workers.append(task)
        print(f"Queue started with {workers} workers")

    async def stop(self):
        self._running = False
        for w in self._workers:
            w.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)
        print("Queue stopped")

    async def _worker(self, worker_id: int):
        while self._running:
            try:
                priority, notification_id, template_vars, attempt = await asyncio.wait_for(
                    self._queue.get(), timeout=1.0
                )
                await self._process(notification_id, template_vars, attempt)
                self._queue.task_done()
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Worker {worker_id} error: {e}")

    def _render_template(self, body: str, variables_dict: dict) -> str:
        if not variables_dict or not body:
            return body
        result = body
        for k, v in variables_dict.items():
            result = result.replace(f"{{{{{k}}}}}", str(v))
        return result

    async def _process(self, notification_id: int, template_vars: dict, attempt: int):

        def db_process():
            db = SessionLocal()
            try:
                noti = db.query(Notification).filter(Notification.id == notification_id).first()
                if not noti:
                    return None, None
                
                # Check user preferences
                pref = db.query(UserPreference).filter(
                    UserPreference.user_id == noti.user_id,
                    UserPreference.channel == noti.channel
                ).first()
                
                is_opted_in = True
                if pref:
                    is_opted_in = pref.is_opted_in

                return noti, is_opted_in
            finally:
                db.close()
                
        notification, is_opted_in = await asyncio.to_thread(db_process)
        if not notification:
            return

        if not is_opted_in:
            print(f"[{notification.channel.upper()}] User {notification.user_id} opted out. Skipping.")
            return

        channel = notification.channel
        
        try:
            provider = get_provider(channel)
            rendered_body = self._render_template(notification.message_body, template_vars)
            
            await provider.send(
                user_id=notification.user_id,
                body=rendered_body,
            )

            def mark_success():
                db = SessionLocal()
                try:
                    noti = db.query(Notification).filter(Notification.id == notification_id).first()
                    if noti:
                        noti.status = NotificationStatus.SENT
                        noti.sent_at = datetime.now(timezone.utc)
                        noti.retry_count = attempt - 1
                        noti.message_body = rendered_body
                        db.commit()
                finally:
                    db.close()

            await asyncio.to_thread(mark_success)
            print(f"[{channel.upper()}] Delivered notification -> user={notification.user_id} on attempt {attempt}")
            
        except Exception as e:
            error_msg = str(e)
            print(f"Failed to deliver: {error_msg} (Attempt {attempt})")
            
            if attempt < 3: # MAX_RETRIES
                delay = 1.0 * (2 ** (attempt - 1))
                def mark_retry():
                    db = SessionLocal()
                    try:
                        noti = db.query(Notification).filter(Notification.id == notification_id).first()
                        if noti:
                            noti.retry_count = attempt
                            noti.error_message = error_msg
                            noti.message_body = rendered_body
                            db.commit()
                    finally:
                        db.close()
                
                await asyncio.to_thread(mark_retry)
                await asyncio.sleep(delay)
                await self.enqueue(notification_id, priority=notification.priority.value, template_vars=template_vars, attempt=attempt + 1)
            else:
                def mark_failed():
                    db = SessionLocal()
                    try:
                        noti = db.query(Notification).filter(Notification.id == notification_id).first()
                        if noti:
                            noti.status = NotificationStatus.FAILED
                            noti.error_message = error_msg
                            noti.retry_count = attempt
                            noti.message_body = rendered_body
                            db.commit()
                    finally:
                        db.close()
                        
                await asyncio.to_thread(mark_failed)

notification_queue = NotificationQueue()
