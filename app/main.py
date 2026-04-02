from fastapi import FastAPI

app = FastAPI(
    title="Klarixa Notification Service",
    description="Backend service for dispatching multi-channel notifications",
    version="1.0.0"
)

@app.get("/ping")
def health_check():
    return {"status": "ok", "message": "Notification service is running"}
