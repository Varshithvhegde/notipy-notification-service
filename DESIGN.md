# System Architecture Design

## High-Level Architecture
This Notification microservice assumes a strictly decoupled layout enforcing heavy background processing, separating API bottlenecks from external processing.

1. **Gatekeeping API Controller**: FastAPI heavily guards traffic initially, resolving validations via strict Pydantic structures and blocking spam users via an inner-memory Sliding Window dictionary check. Any identical `idempotency_key` string instantly returns success avoiding database overhead. 
2. **SQLite Database Interface**: SQLAlchemy wraps models natively routing payloads successfully storing them as safe `PENDING` transactions so messages are permanently shielded from application crashes.
3. **Queue Consumers**: Python's `asyncio.PriorityQueue` hooks natively into the ASGI server lifespan. Worker nodes dynamically consume tasks pulling heavily toward `priority.value` hierarchies. 

## Schema Infrastructure Decisions

### `notifications` Table
Stores raw communication states:
- `user_id` mapped via upstream ID's instead of local relationship objects since this microservice strictly isolates from user management systems safely.
- `priority` enum strings guaranteeing explicit data structuring.
- Tracking analytics mapping attributes (`retry_count`, `error_message`, `sent_at`) capturing diagnostic telemetrics over time dynamically. 

### `user_preferences` Table
Provides boolean toggle `is_opted_in` paths isolated by `user_id` and `channel`. Workers always filter explicitly through here mitigating angry clients who removed permission!

## Retry Mechanisms & Failure Resilience
In distributed system setups, network components fail often. When an external channel provider throws an unhandled Exception, the queue system gracefully suppresses it:
- The `attempt` internal cycle tracking number scales upward.
- Calculates an absolute delay multiplier: `2 ^ attempt_count`.
- Halts its execution thread asynchronously via `asyncio.sleep` to avoid blocking other workers.
- Attempts delivery exactly up to 3 boundary limits before cleanly failing natively and updating database markers to `FAILED`.

## Scalability Map
If the volume demands significantly over 1,000+ payload deliveries a second globally:
- We simply scale the FastAPI app instances behind a standard layer 7 load balancer.
- Internal `asyncio` priority queues natively decouple outward into `RabbitMQ` topics or `Redis Queue (RQ)`. This permits isolated clusters to uniquely consume high-priority loads separately from the API hardware logic entirely.
- SQLite replaces rapidly via updating environment config strings globally to native PostgreSQL without altering a single structural `models/` file!
