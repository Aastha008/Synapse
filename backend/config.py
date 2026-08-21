"""Central configuration for the AI Incident Intelligence Platform."""

from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

# ── Paths ───────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

DB_PATH = DATA_DIR / "incidents.db"

# ── Queue ───────────────────────────────────────────────────────────────
QUEUE_MAX_SIZE = 10_000

# ── Simulator ───────────────────────────────────────────────────────────
SIMULATION_INTERVAL_MS = 200          # ms between log events (normal mode)
INCIDENT_TRIGGER_DELAY_SECONDS = 60   # seconds before incident scenario starts
AUTO_TRIGGER_INCIDENT = True

# ── Anomaly Detection ──────────────────────────────────────────────────
ANOMALY_WINDOW_SIZE = 100             # data points in sliding window
ZSCORE_THRESHOLD = 2.5                # z-score threshold for statistical anomaly
ISOLATION_FOREST_CONTAMINATION = 0.1  # expected outlier proportion
MIN_SAMPLES_FOR_ML = 50              # min samples before ML detection activates

# ── Metrics Engine ──────────────────────────────────────────────────────
METRICS_WINDOW_SECONDS = 300          # 5-minute sliding window
AGGREGATION_INTERVAL_SECONDS = 2      # aggregate every 2 seconds
HEALTH_BROADCAST_INTERVAL_SECONDS = 3 # broadcast health snapshot interval

# ── API ─────────────────────────────────────────────────────────────────
API_HOST = "127.0.0.1"
API_PORT = 8000
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
]

# ── LLM (optional: Gemini or OpenAI) ──────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_ENABLED = bool(GEMINI_API_KEY or OPENAI_API_KEY)
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
OPENAI_MODEL = "gpt-4o-mini"

# ── Service Definitions ────────────────────────────────────────────────
SERVICES = [
    "api-gateway",
    "payment-service",
    "user-service",
    "database-service",
    "notification-service",
]

# Directed dependency graph: key → list of services it depends on
SERVICE_DEPENDENCIES: dict[str, list[str]] = {
    "api-gateway": ["payment-service", "user-service", "notification-service"],
    "payment-service": ["database-service"],
    "user-service": ["database-service"],
    "notification-service": [],
    "database-service": [],
}

# ── Baseline Metrics (normal operating ranges) ─────────────────────────
BASELINE_METRICS: dict[str, dict[str, float]] = {
    "api-gateway": {
        "latency_ms": 92,
        "error_rate": 0.003,
        "cpu_percent": 45,
        "memory_percent": 62,
    },
    "payment-service": {
        "latency_ms": 145,
        "error_rate": 0.005,
        "cpu_percent": 52,
        "memory_percent": 58,
        "db_connections_percent": 35,
    },
    "user-service": {
        "latency_ms": 78,
        "error_rate": 0.002,
        "cpu_percent": 38,
        "memory_percent": 55,
        "db_connections_percent": 28,
    },
    "database-service": {
        "latency_ms": 12,
        "error_rate": 0.001,
        "cpu_percent": 60,
        "memory_percent": 70,
        "db_connections_percent": 40,
    },
    "notification-service": {
        "latency_ms": 200,
        "error_rate": 0.008,
        "cpu_percent": 30,
        "memory_percent": 45,
    },
}
