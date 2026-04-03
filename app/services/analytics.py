from datetime import datetime
from typing import Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
import logging

from app.models.notification import Notification, NotificationStatus
from app.schemas.notification import AnalyticsResponse, ChannelStats

logger = logging.getLogger(__name__)

async def get_analytics_stats(
    db: AsyncSession,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> AnalyticsResponse:
    """
    Computes real-time data across the notification stream.
    Aggregates sent/failed/pending counts by channel and overall status.
    """
    filters = []
    if start:
        filters.append(Notification.created_at >= start)
    if end:
        filters.append(Notification.created_at <= end)

    where = and_(*filters) if filters else True

    # 1. Total Job Count
    count_res = await db.execute(select(func.count()).select_from(Notification).where(where))
    total_notifications = count_res.scalar_one()

    # 2. Channel + Status breakdown
    # select channel, status, count(id) group by channel, status
    group_res = await db.execute(
        select(
            Notification.channel,
            Notification.status,
            func.count(Notification.id)
        )
        .where(where)
        .group_by(Notification.channel, Notification.status)
    )
    rows = group_res.all()

    # Data transformation
    channel_map: Dict[str, Dict[str, int]] = {}
    status_totals: Dict[str, int] = {}

    for channel, status_val, count in rows:
        # status_val is likely the Enum member
        status_name = status_val.value if hasattr(status_val, 'value') else str(status_val)
        
        if channel not in channel_map:
            channel_map[channel] = {"sent": 0, "failed": 0, "pending": 0}
            
        channel_map[channel][status_name] = channel_map[channel].get(status_name, 0) + count
        status_totals[status_name] = status_totals.get(status_name, 0) + count

    by_channel = []
    for ch, stats in channel_map.items():
        by_channel.append(ChannelStats(
            channel=ch,
            sent=stats.get("sent", 0),
            failed=stats.get("failed", 0),
            pending=stats.get("pending", 0),
            total=sum(stats.values())
        ))

    return AnalyticsResponse(
        period_start=start,
        period_end=end,
        total_notifications=total_notifications,
        by_channel=by_channel,
        by_status=status_totals
    )
