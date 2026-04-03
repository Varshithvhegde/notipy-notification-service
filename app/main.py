from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.endpoints import users, notifications
from app.workers.queue import notification_queue
from app.core.logging import setup_logging

setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Import engine lazily so test patches are respected
    from app.db.database import engine
    from app.models.base_class import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    await notification_queue.start(workers=2)
    yield
    await notification_queue.stop()

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Klarixa Notification Service",
    description="Backend service for dispatching multi-channel notifications",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])

@app.get("/ping")
def health_check():
    return {"status": "ok", "message": "Notification service is running"}

