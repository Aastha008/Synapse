"""Pydantic models and schemas for the Incident Intelligence Platform."""

from __future__ import annotations

from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


# ── Enums ───────────────────────────────────────────────────────────────

class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IncidentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"


class Trend(str, Enum):
    UP = "up"
    DOWN = "down"
    STABLE = "stable"


# ── Core Event Models ──────────────────────────────────────────────────

class LogEvent(BaseModel):
    """A single log event from an application service."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    service: str
    level: LogLevel
    message: str
    latency_ms: Optional[float] = None
    status_code: Optional[int] = None
    trace_id: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class Metric(BaseModel):
    """A single metric data point."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    service: str
    metric_name: str  # "latency_ms", "error_rate", "cpu_percent", etc.
    value: float


# ── Anomaly & Incident Models ─────────────────────────────────────────

class AnomalyAlert(BaseModel):
    """An anomaly detected by the anomaly detection engine."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    service: str
    metric_name: str
    current_value: float
    baseline_value: float
    deviation_factor: float  # how many times above/below baseline
    zscore: float
    severity: Severity


class Evidence(BaseModel):
    """Supporting evidence for an incident root cause analysis."""
    timestamp: datetime
    type: str  # "anomaly", "log_pattern", "metric_correlation", "dependency"
    service: str
    description: str
    value: Optional[float] = None


class Incident(BaseModel):
    """A detected incident with root cause analysis."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    severity: Severity
    title: str
    root_cause: str
    confidence: float  # 0.0 to 1.0
    affected_services: list[str]
    evidence: list[Evidence] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    status: IncidentStatus = IncidentStatus.ACTIVE
    deployment_version: Optional[str] = None


# ── Dashboard / API Response Models ────────────────────────────────────

class ServiceHealth(BaseModel):
    """Health status of a single service."""
    service: str
    latency_ms: float = 0.0
    latency_trend: float = 0.0          # percentage change
    latency_trend_direction: Trend = Trend.STABLE
    error_rate: float = 0.0
    error_rate_trend: float = 0.0
    error_rate_trend_direction: Trend = Trend.STABLE
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    db_connections_percent: Optional[float] = None
    status: str = "healthy"             # "healthy", "degraded", "critical"
    request_count: int = 0


class SystemHealthSnapshot(BaseModel):
    """Complete system health snapshot for the dashboard."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    services: list[ServiceHealth] = Field(default_factory=list)
    overall_status: str = "healthy"
    active_incidents: int = 0
    total_requests: int = 0
    overall_error_rate: float = 0.0
    overall_latency_ms: float = 0.0


class MetricTimeSeries(BaseModel):
    """Time-series data for a specific metric."""
    service: str
    metric_name: str
    data_points: list[dict] = Field(default_factory=list)  # [{timestamp, value}]


class ErrorDistribution(BaseModel):
    """Error distribution by service."""
    service: str
    count: int
    percentage: float
    top_errors: list[str] = Field(default_factory=list)


class IncidentSummary(BaseModel):
    """Lightweight incident summary for list views."""
    id: str
    detected_at: datetime
    severity: Severity
    title: str
    root_cause: str
    confidence: float
    affected_services: list[str]
    status: IncidentStatus


# ── WebSocket Message Models ──────────────────────────────────────────

class WSMessage(BaseModel):
    """WebSocket message envelope."""
    type: str  # "health_update", "new_incident", "metric_update", "log_event"
    data: dict
    timestamp: datetime = Field(default_factory=datetime.utcnow)
