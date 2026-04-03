def test_health_check(client):
    """Verifies that the API ping route resolves and validates our JSON."""
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "Notification service is running"}

def test_user_preferences_api(client):
    """Integration checks to make sure we can mutate and read back data via the REST DB wrapper."""
    user_id = "pytest_user_88"
    
    # Check default behavior first
    response = client.get(f"/users/{user_id}/preferences")
    assert response.status_code == 200
    
    # POST an opt-out preference for sms
    payload = {"channel": "sms", "is_opted_in": False}
    response2 = client.post(f"/users/{user_id}/preferences", json=payload)
    assert response2.status_code == 200
    assert response2.json()["channel"] == "sms"
    assert response2.json()["is_opted_in"] == False

def test_notification_creation_and_idempotency(client):
    """Submits a full notification request to the queue and inherently validates idempotency logic blocks."""
    payload = {
        "user_id": "test_idem_user",
        "channel": "email",
        "priority": "normal",
        "message_body": "This is a purely automated Pytest payload.",
        "idempotency_key": "unique_pytest_key_10x"
    }
    
    # Fire Request 1
    res1 = client.post("/notifications/", json=payload)
    assert res1.status_code == 200
    data = res1.json()
    assert data["message_body"] == "This is a purely automated Pytest payload."
    assert "id" in data
    
    # Fire Request 2 strictly matching via idempotency key
    res2 = client.post("/notifications/", json=payload)
    assert res2.status_code == 200
    
    # Both IDs mapped exactly the same (meaning the database didn't actually insert duplicate rows)
    assert res1.json()["id"] == res2.json()["id"]

def test_user_notification_history(client):
    """Check retrieving lists from user queries."""
    user_id = "history_pytest_user"
    
    # Create 2 unique messages
    client.post("/notifications/", json={"user_id": user_id, "channel": "push", "message_body": "Message 1", "idempotency_key": "hist1"})
    client.post("/notifications/", json={"user_id": user_id, "channel": "push", "message_body": "Message 2", "idempotency_key": "hist2"})
    
    res = client.get(f"/notifications/user/{user_id}")
    assert res.status_code == 200
    
    data_list = res.json()
    assert len(data_list) == 2
    assert type(data_list) == list

def test_404_on_missing_notification(client):
    """Verifies that requesting an invalid ID returns 404 cleanly."""
    response = client.get("/notifications/99999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Notification not found"

def test_validation_error_on_bad_channel(client):
    """Verifies Pydantic catches bad ENUM channels immediately."""
    payload = {
        "user_id": "test_bad_channel",
        "channel": "slack", # Not in ['email', 'sms', 'push']
        "priority": "normal",
        "message_body": "Will fail schema validation"
    }
    response = client.post("/notifications/", json=payload)
    assert response.status_code == 422 # Unprocessable Entity
    
    # Assert validation error format
    assert response.json()["detail"][0]["msg"].startswith("Input should be")

def test_api_rate_limiter_edge(client):
    """Spams the API via test client to ensure 429 status code translates to the requester."""
    payload = {
        "user_id": "spam_pytest_user",
        "channel": "email",
        "priority": "low",
        "message_body": "Spam"
    }
    # Safely burn exactly 100 requests (The limit) - Use idempotent key to save DB IO overhead
    for i in range(100):
        client.post("/notifications/", json={**payload, "idempotency_key": "burn_limit"})
        
    # The 101st MUST fail dynamically at rate limiter
    failed_res = client.post("/notifications/", json=payload)
    assert failed_res.status_code == 429
    assert "Rate limit exceeded" in failed_res.json()["detail"]
