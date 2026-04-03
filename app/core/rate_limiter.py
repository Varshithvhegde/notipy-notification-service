import time
from collections import defaultdict
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

# Basic In-Memory Rate Limiting for Demo Purposes
# (In production, replace this with Redis-backed counters)
_rate_limits = defaultdict(list)
MAX_REQUESTS_PER_HOUR = 100
ONE_HOUR = 3600

def check_rate_limit(user_id: str):
    now = time.time()
    
    # Prune timestamps older than 1 hour
    _rate_limits[user_id] = [t for t in _rate_limits[user_id] if now - t < ONE_HOUR]
    
    if len(_rate_limits[user_id]) >= MAX_REQUESTS_PER_HOUR:
        logger.warning(f"Rate limit exceeded for user: {user_id}. Attempted beyond {MAX_REQUESTS_PER_HOUR} requests/hr.")
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Maximum {MAX_REQUESTS_PER_HOUR} notifications per hour per user."
        )
    
    _rate_limits[user_id].append(now)
