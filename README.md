# Notification Service Backend

A centralized, scalable backend dispatching multi-channel communications (Email, SMS, Push notification) prioritizing critical messages safely through robust background workers.

## Core Accomplishments
- **Multi-Channel & Templating**: Renders contextual variables `{{name}}` dynamically before invoking reliable channel adapters.
- **Priority Worker Node**: Background `asyncio.PriorityQueue` instances guarantee `CRITICAL` payloads vault to the front natively.
- **Idempotency Check**: Safe hash-sum verifications intercept duplicate submissions immediately before Database entry.
- **Exponential Backoff**: Integrates intelligent 2x scaling delays mitigating upstream Provider errors natively.
- **Rate-Limiter Firewall**: Blocks spamming exceeding user restrictions (Max 100 per sliding window).

## Tech Stack Foundation
- `Python 3.10+` running `FastAPI` (Chosen for high-throughput ASGI concurrency, easy ecosystem abstractions).
- `SQLite` (Easily swappable with robust PostgreSQL instances without fundamentally modifying any architectural logic since we use declarative SQLAlchemy objects).
- Strict validation formatting through fully typed `Pydantic V2` models.

## Local Booting Instructions
```bash
# Boot virtual environment
python -m venv venv
venv\Scripts\activate # On windows

# Install necessary libraries
pip install -r requirements.txt

# Start your FastAPI listener locally
uvicorn app.main:app --reload --port 8000
```
This natively boots both the primary RestAPI gateway and attaches the Background Queue consumers to the Uvicorn Lifespan process safely.

## Validating Functionality
This assignment contains two styles of testing:
1. **Live System Testing**: An execution script named `test_api_live.py` executes 5 rigorous steps directly hitting `localhost:8000` via valid Request objects testing everything from idempotency locks to generating massive 101 payload strings validating 429 logic block paths seamlessly. Run via `python test_api_live.py`.
2. **PyTest Execution**: The native `tests/` directory natively abstracts unit checks. Ensure you've run `pip install pytest httpx`.

## API Documentation
By utilizing FastAPI properly, comprehensive OpenAPI schemas are natively generated for you automatically without rigid maintenance strings. Access full API schemas directly locally:
**`http://127.0.0.1:8000/docs`**

## Production Scaling Approaches & Assumptions
- We explicitly assume authentication/authorization firewalls (JWT checks) operate entirely safely upstream utilizing an API Gateway infrastructure (e.g. Kong, AWS Gateway).
- We utilize sliding dictionary memory for Rate Limiting to prevent latency overhead; in a full clustering setup this gracefully converts to a standard central Redis layer via `aioredis`.
