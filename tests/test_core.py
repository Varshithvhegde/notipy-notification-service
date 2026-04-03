import pytest
from fastapi import HTTPException
from app.workers.queue import notification_queue, PRIORITY_MAP
from app.core.rate_limiter import check_rate_limit, _rate_limits
from app.services.providers import get_provider

def test_template_rendering_engine():
    """Unit test testing the logic of our template engine variable substitution."""
    res = notification_queue._render_template("Hello {{name}}!", {"name": "Varshith"})
    assert res == "Hello Varshith!"
    
    res2 = notification_queue._render_template("Hello {{name}}!", {})
    assert res2 == "Hello {{name}}!"
    
    res3 = notification_queue._render_template(
        "Urgent: System {{system_id}} reported status {{status}}", 
        {"system_id": "X100", "status": "CRITICAL"}
    )
    assert res3 == "Urgent: System X100 reported status CRITICAL"

def test_rate_limiter_logic():
    """Unit test manually asserting that the dictionary-based sliding window acts correctly."""
    test_user = "test_rate_user"
    _rate_limits[test_user].clear()
    
    for _ in range(100):
        check_rate_limit(test_user)
        
    with pytest.raises(HTTPException) as exc_info:
        check_rate_limit(test_user)
        
    assert exc_info.value.status_code == 429
    assert "Rate limit exceeded" in exc_info.value.detail

def test_priority_map_values():
    """Ensures priority levels correctly map to queue weights (lower is higher priority)."""
    assert PRIORITY_MAP["critical"] == 0
    assert PRIORITY_MAP["high"] == 1
    assert PRIORITY_MAP["normal"] == 2
    assert PRIORITY_MAP["low"] == 3

def test_get_valid_provider():
    """Ensures provider factory functions fetch the correct class."""
    provider_email = get_provider("email")
    assert provider_email.name == "email"
    
    provider_sms = get_provider("sms")
    assert provider_sms.name == "sms"
    
    provider_push = get_provider("push")
    assert provider_push.name == "push"

def test_get_invalid_provider():
    """Ensures unsupported channels raise ValueError safely."""
    with pytest.raises(ValueError) as exc_info:
        get_provider("carrier_pigeon")
    assert "No provider for channel" in str(exc_info.value)
