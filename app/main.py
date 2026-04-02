from fastapi import FastAPI
from app.api.endpoints import users
from app.db.database import engine
from app.models.base_class import Base

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Klarixa Notification Service",
    description="Backend service for dispatching multi-channel notifications",
    version="1.0.0"
)

app.include_router(users.router, prefix="/users", tags=["Users"])

@app.get("/ping")
def health_check():
    return {"status": "ok", "message": "Notification service is running"}

