"""Data access layer for the raw, non-normalized event archive.

Companion to database/repository.py (structured SQLite access) — this
module is the schema-less counterpart, used for two call sites only:
  - pipeline/processor.py   → archives every raw payload (fire-and-forget)
  - analytics/root_cause_analyzer.py → pulls raw evidence for a confirmed
    incident, and feeds it into the Gemini/OpenAI RCA narrative
"""

from datetime import datetime, timedelta
import logging

from database import mongo

logger = logging.getLogger("mongo_repository")


async def insert_raw_event(
    service: str,
    event_type: str,
    raw_payload: dict,
    correlation_id: str | None = None,
    timestamp: datetime | None = None,
) -> None:
    """Archive one untouched event payload. Silently no-ops if Mongo is unavailable
    so this never becomes a reason the main pipeline fails."""
    db = mongo.get_db()
    if db is None:
        return

    try:
        await db.raw_events.insert_one({
            "service": service,
            "event_type": event_type,          # "log" | "metric"
            "timestamp": timestamp or datetime.utcnow(),
            "correlation_id": correlation_id,   # LogEvent.id / trace_id, for joining back to SQLite
            "raw_payload": raw_payload,         # untouched, non-normalized — no schema enforced
        })
    except Exception as e:
        logger.error(f"Failed to archive raw event for {service}: {e}")


async def get_raw_logs_for_incident(
    services: list[str],
    around: datetime | None = None,
    window_seconds: int = 300,
    limit: int = 25,
) -> list[dict]:
    """Fetch raw payloads for the services implicated in an incident, in the
    time window around it. Used only at incident time (root_cause_analyzer.py) —
    never on the per-event hot path."""
    db = mongo.get_db()
    if db is None or not services:
        return []

    center = around or datetime.utcnow()
    start = center - timedelta(seconds=window_seconds)
    end = center + timedelta(seconds=window_seconds)

    try:
        cursor = (
            db.raw_events.find(
                {
                    "service": {"$in": services},
                    "timestamp": {"$gte": start, "$lte": end},
                },
                {"_id": 0},
            )
            .sort("timestamp", 1)
            .limit(limit)
        )
        return [doc async for doc in cursor]
    except Exception as e:
        logger.error(f"Failed to fetch raw evidence for {services}: {e}")
        return []
