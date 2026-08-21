"""Real-time metrics aggregation engine with in-memory ring buffers."""

from collections import defaultdict, deque
from datetime import datetime, timedelta
import threading

from models.schemas import (
    Metric, ServiceHealth, SystemHealthSnapshot,
    MetricTimeSeries, ErrorDistribution, Trend,
)
import config


class MetricsEngine:
    def __init__(self):
        # Ring buffers: {service: {metric_name: deque of (datetime, float)}}
        self._buffers: dict[str, dict[str, deque]] = defaultdict(
            lambda: defaultdict(lambda: deque(maxlen=config.ANOMALY_WINDOW_SIZE * 3))
        )
        self._error_counts: dict[str, int] = defaultdict(int)
        self._request_counts: dict[str, int] = defaultdict(int)
        self._error_messages: dict[str, list[str]] = defaultdict(list)
        self._active_incidents: int = 0
        self._lock = threading.RLock()

    def set_active_incidents(self, count: int) -> None:
        with self._lock:
            self._active_incidents = count

    def increment_active_incidents(self) -> None:
        with self._lock:
            self._active_incidents += 1

    def reset(self) -> None:
        with self._lock:
            self._active_incidents = 0
            self._error_counts.clear()
            self._error_messages.clear()

    # ── recording ──────────────────────────────────────────────────────

    def record_metric(self, metric: Metric) -> None:
        with self._lock:
            self._buffers[metric.service][metric.metric_name].append(
                (metric.timestamp, metric.value)
            )

    def record_error(self, service: str, message: str) -> None:
        with self._lock:
            self._error_counts[service] += 1
            msgs = self._error_messages[service]
            msgs.append(message)
            if len(msgs) > 50:
                msgs.pop(0)

    def record_request(self, service: str) -> None:
        with self._lock:
            self._request_counts[service] += 1

    # ── health snapshots ───────────────────────────────────────────────

    def get_current_health(self) -> SystemHealthSnapshot:
        with self._lock:
            now = datetime.utcnow()
            services_list: list[ServiceHealth] = []
            worst_status = "healthy"

            all_services = sorted(
                set(list(self._buffers.keys()) + config.SERVICES)
            )
            total_requests = 0
            total_errors = 0

            for service in all_services:
                health = self._build_service_health(service)
                services_list.append(health)
                total_requests += health.request_count

                if health.status == "critical":
                    worst_status = "critical"
                elif health.status == "degraded" and worst_status != "critical":
                    worst_status = "degraded"

            overall_error_rate = 0.0
            overall_latency = 0.0
            if services_list:
                overall_error_rate = sum(s.error_rate for s in services_list) / len(services_list)
                overall_latency = sum(s.latency_ms for s in services_list) / len(services_list)

            active_incidents = self._active_incidents

            return SystemHealthSnapshot(
                timestamp=now,
                services=services_list,
                overall_status=worst_status,
                active_incidents=active_incidents,
                total_requests=total_requests,
                overall_error_rate=overall_error_rate,
                overall_latency_ms=overall_latency,
            )

    def get_service_health(self, service: str) -> ServiceHealth:
        with self._lock:
            return self._build_service_health(service)

    def _build_service_health(self, service: str) -> ServiceHealth:
        """Build a ServiceHealth using the shared Pydantic schema fields."""
        latency = self._get_latest_value(service, "latency_ms")
        latency_pct, latency_dir = self._calculate_trend(service, "latency_ms")

        error_rate = self._get_latest_value(service, "error_rate")
        err_pct, err_dir = self._calculate_trend(service, "error_rate")

        cpu = self._get_latest_value(service, "cpu_percent")
        mem = self._get_latest_value(service, "memory_percent")

        db_conn = None
        baseline = config.BASELINE_METRICS.get(service, {})
        if "db_connections_percent" in baseline or "db_connections_percent" in self._buffers.get(service, {}):
            db_conn = self._get_latest_value(service, "db_connections_percent")

        # Determine status
        status = "healthy"
        if db_conn is not None and db_conn > 90:
            status = "critical"
        elif db_conn is not None and db_conn > 75:
            status = "degraded" if status != "critical" else status
        if latency > 500:
            status = "critical"
        elif latency > 200 and status != "critical":
            status = "degraded"
        if error_rate > 0.05:
            status = "critical"
        elif error_rate > 0.01 and status != "critical":
            status = "degraded"

        return ServiceHealth(
            service=service,
            latency_ms=round(latency, 1),
            latency_trend=round(latency_pct, 1),
            latency_trend_direction=latency_dir,
            error_rate=round(error_rate, 4),
            error_rate_trend=round(err_pct, 1),
            error_rate_trend_direction=err_dir,
            cpu_percent=round(cpu, 1),
            memory_percent=round(mem, 1),
            db_connections_percent=round(db_conn, 1) if db_conn is not None else None,
            status=status,
            request_count=self._request_counts.get(service, 0),
        )

    # ── time-series ────────────────────────────────────────────────────

    def get_timeseries(
        self, service: str, metric_name: str, minutes: int = 60,
    ) -> MetricTimeSeries:
        with self._lock:
            cutoff = datetime.utcnow() - timedelta(minutes=minutes)
            data_points = []

            buffer = self._buffers.get(service, {}).get(metric_name, deque())
            for ts, val in buffer:
                if ts >= cutoff:
                    data_points.append({"timestamp": ts.isoformat(), "value": round(val, 2)})

            return MetricTimeSeries(
                service=service,
                metric_name=metric_name,
                data_points=data_points,
            )

    def get_all_timeseries(self, minutes: int = 5) -> dict[str, dict[str, MetricTimeSeries]]:
        with self._lock:
            result: dict[str, dict[str, MetricTimeSeries]] = defaultdict(dict)
            for service, metrics in self._buffers.items():
                for metric_name in metrics.keys():
                    result[service][metric_name] = self.get_timeseries(
                        service, metric_name, minutes,
                    )
            return dict(result)

    # ── error distribution ─────────────────────────────────────────────

    def get_error_distribution(self) -> list[ErrorDistribution]:
        with self._lock:
            total = sum(self._error_counts.values())
            dist = []
            if total > 0:
                for svc, count in self._error_counts.items():
                    if count > 0:
                        dist.append(
                            ErrorDistribution(
                                service=svc,
                                count=count,
                                percentage=round((count / total) * 100.0, 1),
                                top_errors=self._error_messages.get(svc, [])[-5:],
                            )
                        )
            return sorted(dist, key=lambda x: x.count, reverse=True)

    # ── internal helpers ───────────────────────────────────────────────

    def _get_latest_value(self, service: str, metric_name: str) -> float:
        buffer = self._buffers.get(service, {}).get(metric_name)
        if buffer and len(buffer) > 0:
            return buffer[-1][1]
        return config.BASELINE_METRICS.get(service, {}).get(metric_name, 0.0)

    def _get_average(self, service: str, metric_name: str, seconds: int) -> float:
        cutoff = datetime.utcnow() - timedelta(seconds=seconds)
        buffer = self._buffers.get(service, {}).get(metric_name, deque())
        vals = [v for ts, v in buffer if ts >= cutoff]
        if vals:
            return sum(vals) / len(vals)
        return config.BASELINE_METRICS.get(service, {}).get(metric_name, 0.0)

    def _calculate_trend(
        self, service: str, metric_name: str,
    ) -> tuple[float, Trend]:
        recent_avg = self._get_average(service, metric_name, 30)

        cutoff_recent = datetime.utcnow() - timedelta(seconds=30)
        cutoff_prior = cutoff_recent - timedelta(seconds=30)

        buffer = self._buffers.get(service, {}).get(metric_name, deque())
        prior_vals = [v for ts, v in buffer if cutoff_prior <= ts < cutoff_recent]

        prior_avg = (
            sum(prior_vals) / len(prior_vals)
            if prior_vals
            else config.BASELINE_METRICS.get(service, {}).get(metric_name, 0.0)
        )

        if prior_avg == 0:
            return (100.0, Trend.UP) if recent_avg != 0 else (0.0, Trend.STABLE)

        percent_change = ((recent_avg - prior_avg) / prior_avg) * 100.0

        if percent_change > 5.0:
            return percent_change, Trend.UP
        elif percent_change < -5.0:
            return percent_change, Trend.DOWN
        return percent_change, Trend.STABLE
