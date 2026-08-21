"""Two-tier anomaly detection: Z-score (statistical) + Isolation Forest (ML)."""

from collections import defaultdict, deque
from datetime import datetime, timedelta
import numpy as np

from models.schemas import Metric, AnomalyAlert, Severity
import config


class AnomalyDetector:
    def __init__(self):
        self._windows: dict[tuple[str, str], deque] = defaultdict(
            lambda: deque(maxlen=config.ANOMALY_WINDOW_SIZE)
        )
        self._recent_anomalies: deque[AnomalyAlert] = deque(maxlen=100)
        self._isolation_forest_models: dict[str, object] = {}
        self._sample_count: dict[str, int] = defaultdict(int)
        self._ml_enabled = True

        try:
            from sklearn.ensemble import IsolationForest
            self._IsolationForest = IsolationForest
        except ImportError:
            self._ml_enabled = False
            self._IsolationForest = None

    def add_data_point(self, metric: Metric) -> AnomalyAlert | None:
        key = (metric.service, metric.metric_name)
        self._windows[key].append(metric.value)
        self._sample_count[metric.service] += 1

        if len(self._windows[key]) < 20:
            return None

        z_score = self._detect_zscore(metric.service, metric.metric_name, metric.value)
        ml_anomaly = False

        if self._ml_enabled and self._sample_count[metric.service] >= config.MIN_SAMPLES_FOR_ML:
            ml_anomaly = self._detect_isolation_forest(metric.service)

        if z_score is not None or ml_anomaly:
            abs_z = abs(z_score) if z_score is not None else 0.0

            if abs_z > 4.0:
                severity = Severity.CRITICAL
            elif abs_z > 3.5:
                severity = Severity.HIGH
            elif abs_z > 3.0:
                severity = Severity.MEDIUM
            else:
                severity = Severity.LOW

            baseline = self._get_baseline(metric.service, metric.metric_name)
            deviation = metric.value / baseline if baseline > 0 else 0.0

            alert = AnomalyAlert(
                timestamp=metric.timestamp,
                service=metric.service,
                metric_name=metric.metric_name,
                current_value=metric.value,
                baseline_value=baseline,
                deviation_factor=deviation,
                zscore=z_score if z_score is not None else 0.0,
                severity=severity,
            )
            self._recent_anomalies.append(alert)
            return alert

        return None

    def _detect_zscore(self, service: str, metric_name: str, value: float) -> float | None:
        window = list(self._windows[(service, metric_name)])
        if not window:
            return None

        mean = float(np.mean(window))
        std = float(np.std(window))

        if std < 0.001:
            if abs(value - mean) > 0.001:
                return 10.0 if value > mean else -10.0
            return None

        z_score = (value - mean) / std
        if abs(z_score) > config.ZSCORE_THRESHOLD:
            return float(z_score)
        return None

    def _detect_isolation_forest(self, service: str) -> bool:
        if not self._ml_enabled or self._IsolationForest is None:
            return False

        metrics_for_service = [k for k in self._windows.keys() if k[0] == service]
        if not metrics_for_service:
            return False

        min_len = min(len(self._windows[k]) for k in metrics_for_service)
        if min_len < config.MIN_SAMPLES_FOR_ML:
            return False

        feature_matrix = []
        for i in range(min_len):
            row = [self._windows[k][len(self._windows[k]) - min_len + i] for k in metrics_for_service]
            feature_matrix.append(row)

        X = np.array(feature_matrix)

        if self._sample_count[service] % 50 == 0 or service not in self._isolation_forest_models:
            model = self._IsolationForest(
                contamination=config.ISOLATION_FOREST_CONTAMINATION,
                random_state=42,
            )
            model.fit(X)
            self._isolation_forest_models[service] = model

        model = self._isolation_forest_models.get(service)
        if model is not None:
            latest = X[-1].reshape(1, -1)
            pred = model.predict(latest)
            return bool(pred[0] == -1)

        return False

    def get_recent_anomalies(self, minutes: int = 10) -> list[AnomalyAlert]:
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        return [a for a in self._recent_anomalies if a.timestamp >= cutoff]

    def get_anomaly_count(self) -> int:
        return len(self._recent_anomalies)

    def _get_baseline(self, service: str, metric_name: str) -> float:
        return config.BASELINE_METRICS.get(service, {}).get(metric_name, 0.0)
