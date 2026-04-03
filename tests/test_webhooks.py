import pytest
from httpx import AsyncClient
from app.models.webhook import Webhook
from sqlalchemy import select

@pytest.mark.anyio
async def test_webhook_registration(client: AsyncClient, db_session):
    """Test registering a webhook."""
    payload = {
        "url": "https://example.com/webhook",
        "events": ["sent", "failed"],
        "user_id": "test_user",
        "secret": "my_secret"
    }
    response = await client.post("/webhooks/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["url"] == payload["url"]
    assert data["user_id"] == payload["user_id"]
    assert data["is_active"] is True

@pytest.mark.anyio
async def test_list_webhooks(client: AsyncClient):
    """Test listing webhooks."""
    response = await client.get("/webhooks/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.anyio
async def test_toggle_webhook(client: AsyncClient, db_session):
    """Test toggling a webhook."""
    # Create one
    payload = {"url": "https://example.com/hook2", "events": ["sent"]}
    create_res = await client.post("/webhooks/", json=payload)
    hook_id = create_res.json()["id"]

    # Toggle it
    toggle_res = await client.patch(f"/webhooks/{hook_id}/toggle")
    assert toggle_res.status_code == 200
    assert toggle_res.json()["is_active"] is False

    # Toggle back
    toggle_res = await client.patch(f"/webhooks/{hook_id}/toggle")
    assert toggle_res.json()["is_active"] is True

@pytest.mark.anyio
async def test_delete_webhook(client: AsyncClient, db_session):
    """Test deleting a webhook."""
    payload = {"url": "https://example.com/hook3", "events": ["sent"]}
    create_res = await client.post("/webhooks/", json=payload)
    hook_id = create_res.json()["id"]

    del_res = await client.delete(f"/webhooks/{hook_id}")
    assert del_res.status_code == 204

    # Verify gone
    get_res = await client.get("/webhooks/")
    hooks = get_res.json()
    assert not any(h["id"] == hook_id for h in hooks)
