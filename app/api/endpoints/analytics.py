from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import Optional

from app.api.dependencies import get_db
from app.schemas.notification import AnalyticsResponse
from app.services.analytics import get_analytics_stats

router = APIRouter()

@router.get("/stats", response_model=AnalyticsResponse)
async def get_system_stats(
    start: Optional[datetime] = Query(None, description="ISO START DATETIME"),
    end: Optional[datetime] = Query(None, description="ISO END DATETIME"),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns high-level system analytics for sent, failed, and pending jobs.
    Useful for health monitoring and usage breakdown.
    """
    return await get_analytics_stats(db, start=start, end=end)
