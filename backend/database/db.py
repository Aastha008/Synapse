import aiosqlite
from pathlib import Path
from config import DATA_DIR, DB_PATH
import asyncio

_pool = None

async def get_connection():
    global _pool
    if _pool is None:
        _pool = await aiosqlite.connect(DB_PATH)
    return _pool

async def init_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    db = await get_connection()
    await db.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id TEXT PRIMARY KEY,
            timestamp TEXT,
            service TEXT,
            level TEXT,
            message TEXT,
            latency_ms REAL,
            status_code INT,
            trace_id TEXT,
            metadata TEXT
        )
    ''')
    await db.execute('''
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            service TEXT,
            metric_name TEXT,
            value REAL
        )
    ''')
    await db.execute('''
        CREATE TABLE IF NOT EXISTS incidents (
            id TEXT PRIMARY KEY,
            detected_at TEXT,
            severity TEXT,
            title TEXT,
            root_cause TEXT,
            confidence REAL,
            affected_services TEXT,
            evidence TEXT,
            recommended_actions TEXT,
            status TEXT,
            deployment_version TEXT
        )
    ''')
    await db.execute('CREATE INDEX IF NOT EXISTS idx_logs_timestamp_service ON logs(timestamp, service)')
    await db.execute('CREATE INDEX IF NOT EXISTS idx_metrics_timestamp_service ON metrics(timestamp, service)')
    await db.commit()
