# Notipy - Advanced Async Notification Engine 🚀

**Notipy** is a production-ready, fully asynchronous notification microservice built with **FastAPI**, **SQLAlchemy (Async)**, and **Jinja2**. It is designed to orchestrate high-throughput delivery across Email, SMS, and Push channels with built-in reliability and intelligence.

---

## 🌟 Key Features

### 1. High-Performance Core
*   **Fully Asynchronous**: Uses `asyncpg` (PostgreSQL) and `aiosqlite` (SQLite) for non-blocking database operations.
*   **Priority Queue**: A native `asyncio.Queue` based worker system that processes jobs based on priority (`CRITICAL`, `HIGH`, `NORMAL`, `LOW`).
*   **Atomic Batch API**: Send personalized notifications to hundreds of users in a single request.

### 2. Multi-Channel Reliability
*   **Strategy Pattern**: Clean provider abstraction allowing easy swaps between Twilio, SendGrid, or Mock providers.
*   **Retries & Error Tracking**: Exponential backoff (simulated) for transient failures with detailed error logging per job.
*   **Idempotency Locks**: Prevent double-firing notifications for duplicate requests using unique keys.

### 3. Intelligence & Control
*   **Template Library**: DB-backed Jinja2 templates with real-time variable injection.
*   **User Preferences**: Global opt-out registry per user-channel pair.
*   **Sliding Window Rate Limiting**: Protect your upstream providers from spam with per-user footprint monitoring.

### 4. Enterprise Observability
*   **Real-time Analytics**: Aggregate throughput stats (sent/failed/pending) grouped by channel and time period.
*   **Webhooks**: Register HTTP callback endpoints for `SENT` or `FAILED` notification events.
*   **Paginated Telemetry**: Full historical audit trail for every user ID.

---

## 🛠️ Architecture & Assumptions

### User Identity
This service uses a **Lazy User Model**. A `user_id` is simply a unique string representing an identity. You do **not** need to register a user before sending a notification. 
*   **Assumption**: If no preference is found in the database, the user is considered **Opted-In** to all channels by default.

### Workers
The engine starts **2 concurrent worker threads** within the same process under the FastAPI lifespan. It automatically handles table creation (`metadata.create_all`) on startup.

---

## 🚀 Getting Started

### 1. Local Setup
```bash
# Clone and enter directory
cd notipy_AI_Backend-Assignment

# Setup Virtual Environment
python -m venv venv
source venv/Scripts/activate  # On Windows: venv\Scripts\activate

# Install Dependencies
pip install -r requirements.txt
```

### 2. Configure Database
Update the `.env` file with your PostgreSQL credentials:
```env
# DATABASE_URL=sqlite+aiosqlite:///./test.db # For SQLite
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/notipy_db
```

### 3. Run the Engine
```bash
uvicorn app.main:app --reload --port 8000
```

---

## 🐳 Docker Deployment

The project includes a multi-stage `Dockerfile` for easy containerization.

```bash
# Build the image
docker build -t notipy-engine .

# Run the container
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/db \
  notipy-engine
```

---

## 🖥️ Using the Notipy Dashboard

The project features a **Premium Web Dashboard** located at `index.html`. It uses Glassmorphism aesthetics and provides a no-code interface for managing the entire engine.

**To run the UI:**
1.  Open `index.html` using a local server (e.g., VS Code **Live Server** on port 5500).
2.  The UI is pre-configured to talk to the backend at `http://127.0.0.1:8000`.
3.  **Functions**: Use the tabs to dispatch Batch/Single notifications, manage Template Variables, and track Live Telemetry.

---

## 🧪 Testing

### 1. Core Test Suite (Pytest)
Run the comprehensive async test suite (17+ cases):
```bash
python -m pytest tests/ -v
```

### 2. Live Diagnostics CLI
Run our custom diagnostic tool for a beautiful, interactive system verify:
```bash
python test_api_live.py
```

---

## 📁 API Reference & Curl Examples

### 1. Send Notification (Single User)
```bash
curl -X POST "http://127.0.0.1:8000/notifications/" \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": "cust_123",
       "channels": ["email", "sms"],
       "message_body": "Hello {{name}}!",
       "template_vars": {"name": "Varshith"},
       "priority": "critical"
     }'
```

### 2. Create Template
```bash
curl -X POST "http://127.0.0.1:8000/templates/" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "welcome_tpl",
       "subject": "Welcome!",
       "body": "Welcome aboard {{user}}!",
       "allowed_channels": ["email", "push"]
     }'
```

### 3. Batch Dispatch
```bash
curl -X POST "http://127.0.0.1:8000/notifications/batch" \
     -H "Content-Type: application/json" \
     -d '{
       "notifications": [
         {"user_id": "u1", "channels": ["email"], "message_body": "User 1 msg"},
         {"user_id": "u2", "channels": ["sms"], "message_body": "User 2 msg"}
       ]
     }'
```

### 4. Fetch Strategy Stats
```bash
curl "http://127.0.0.1:8000/analytics/stats?start=2024-01-01T00:00:00"
```

---

