"""MongoDB connection manager — raw, non-normalized event archive.

Mirrors the connection-singleton pattern used in database/db.py (SQLite),
but for schema-less JSON payloads that don't belong in a relational table.
Kept fully optional: if MONGO_ENABLED is False or the connection fails,
the rest of the platform runs exactly as before — this archive only
feeds the incident-time evidence lookup in root_cause_analyzer.py, never
the hot anomaly-detection path.
"""

import logging

import config

logger = logging.getLogger("mongo")

_client = None
_db = None


async def connect() -> None:
    """Open the Mongo connection and ensure indexes exist. No-op if disabled."""
    global _client, _db

    if not config.MONGO_ENABLED:
        logger.info("MongoDB archive disabled (set MONGO_URI or MONGO_ENABLED=true to enable)")
        return

    try:
        import motor.motor_asyncio

        _client = motor.motor_asyncio.AsyncIOMotorClient(
            config.MONGO_URI, serverSelectionTimeoutMS=5000
        )
        # fail fast on startup if the URI is wrong, rather than on first query
        await _client.admin.command("ping")
        _db = _client[config.MONGO_DB_NAME]

        # Envelope fields are indexed for the queries we actually run
        # (by service + time range). raw_payload itself is deliberately
        # left unindexed and schema-less.
        await _db.raw_events.create_index([("service", 1), ("timestamp", -1)])
        await _db.raw_events.create_index(
            "timestamp", expireAfterSeconds=config.RAW_EVENT_TTL_SECONDS
        )
        logger.info(f"MongoDB raw event archive connected → {config.MONGO_DB_NAME}.raw_events")
    except Exception as e:
        logger.error(f"MongoDB connection failed, raw event archive disabled: {e}")
        _client = None
        _db = None


async def close() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None


def get_db():
    """Returns the Mongo database handle, or None if archiving is unavailable."""
    return _db


def is_connected() -> bool:
    return _db is not None
