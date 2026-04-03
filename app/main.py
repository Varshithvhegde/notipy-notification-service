from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.endpoints import users, notifications
from app.db.database import engine
from app.models.base_class import Base
from app.core.logging import setup_logging

setup_logging()

# Create database tables
Base.metadata.create_all(bind=engine)
from app.workers.queue import notification_queue

@asynccontextmanager
async def lifespan(app: FastAPI):
    await notification_queue.start(workers=2)
    yield
    await notification_queue.stop()

app = FastAPI(
    title="Klarixa Notification Service",
    description="Backend service for dispatching multi-channel notifications",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])

@app.get("/ping")
def health_check():
    return {"status": "ok", "message": "Notification service is running"}

