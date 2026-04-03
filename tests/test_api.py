import pytest

pytestmark = pytest.mark.anyio

# Reset rate limiter between tests
@pytest.fixture(autouse=True)
def reset_rate_limiter():
    from app.core.rate_limiter import _rate_limit_store
    _rate_limit_store.clear()
    yield

async def test_health_check(client):
    res = await client.get("/ping")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

async def test_notification_creation_and_idempotency(client):
    """Creates a notification and validates idempotency key deduplication."""
    payload = {
        "user_id": "test_idem_user",
        "channels": ["email"],
        "priority": "normal",
        "message_body": "This is a purely automated Pytest payload.",
        "idempotency_key": "unique_pytest_key_10x"
    }
    res1 = await client.post("/notifications/", json=payload)
    assert res1.status_code == 200
    data = res1.json()[0]
    assert data["message_body"] == "This is a purely automated Pytest payload."
    assert "id" in data

    res2 = await client.post("/notifications/", json=payload)
    assert res2.status_code == 200
    assert res1.json()[0]["id"] == res2.json()[0]["id"]

async def test_user_notification_history(client):
    """Validates notification history list endpoint with pagination."""
    user_id = "history_pytest_user"
    await client.post("/notifications/", json={"user_id": user_id, "channels": ["push"], "message_body": "Message 1", "idempotency_key": "hist1"})
    await client.post("/notifications/", json={"user_id": user_id, "channels": ["push"], "message_body": "Message 2", "idempotency_key": "hist2"})

    res = await client.get(f"/notifications/user/{user_id}")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 2
    assert data["page"] == 1
    assert len(data["items"]) >= 2

async def test_pagination_params(client):
    """Validates page and page_size query parameters work correctly."""
    user_id = "pagination_test_user"
    for i in range(5):
        await client.post("/notifications/", json={"user_id": user_id, "channels": ["email"], "message_body": f"Msg {i}", "idempotency_key": f"pg_key_{i}"})

    res = await client.get(f"/notifications/user/{user_id}?page=1&page_size=2")
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["total_pages"] == 3
    assert data["has_next"] == True
    assert data["has_prev"] == False

    res2 = await client.get(f"/notifications/user/{user_id}?page=2&page_size=2")
    data2 = res2.json()
    assert data2["has_prev"] == True
    assert data2["has_next"] == True

async def test_404_on_missing_notification(client):
    """Returns 404 for a non-existent ID."""
    res = await client.get("/notifications/999999")
    assert res.status_code == 404

async def test_validation_error_on_bad_channel(client):
    """Pydantic rejects invalid channel values."""
    payload = {
        "user_id": "test_bad_channel",
        "channels": ["slack"],
        "priority": "normal",
        "message_body": "Will fail schema validation"
    }
    res = await client.post("/notifications/", json=payload)
    assert res.status_code == 422

async def test_user_preferences_api(client):
    """Sets and retrieves user channel preferences."""
    user_id = "pref_test_user"
    pref_payload = {"channel": "email", "is_opted_in": False}

    res = await client.post(f"/users/{user_id}/preferences", json=pref_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["channel"] == "email"
    assert data["is_opted_in"] == False

    get_res = await client.get(f"/users/{user_id}/preferences")
    assert get_res.status_code == 200
    prefs = get_res.json()
    assert any(p["channel"] == "email" for p in prefs)

async def test_api_rate_limiter_edge(client):
    """Triggers rate limiter after 100 requests."""
    payload = {
        "user_id": "spam_pytest_user",
        "channels": ["email"],
        "priority": "low",
        "message_body": "Spam"
    }
    for _ in range(100):
        await client.post("/notifications/", json=payload)

    res = await client.post("/notifications/", json=payload)
    assert res.status_code == 429
