"""Log Processing Engine — orchestrates the data flow from queue to storage, analytics, and WebSocket."""

import time
import logging
from typing import Any

from models.schemas import LogEvent, Metric, AnomalyAlert, WSMessage


logger = logging.getLogger("processor")


class LogProcessor:
    def __init__(
        self,
        queue: Any,
        repository: Any,
        metrics_engine: Any,
        anomaly_detector: Any,
        root_cause_analyzer: Any,
        ws_manager: Any = None,
    ):
        self.queue = queue
        self.repository = repository
        self.metrics_engine = metrics_engine
        self.anomaly_detector = anomaly_detector
        self.root_cause_analyzer = root_cause_analyzer
        self.ws_manager = ws_manager

        self._anomaly_buffer: list[AnomalyAlert] = []
        self._rca_cooldown = 30  # seconds between RCA runs
        self._last_rca_time: float = 0

    async def start(self) -> None:
        await self.queue.subscribe("log", self._handle_log)
        await self.queue.subscribe("metric", self._handle_metric)

    async def _handle_log(self, data: dict) -> None:
        try:
            log_event = LogEvent(**data)
            await self.repository.insert_log(log_event)

            # Track errors in metrics engine
            if log_event.level in ("ERROR", "CRITICAL"):
                self.metrics_engine.record_error(log_event.service, log_event.message)

            # Track requests
            self.metrics_engine.record_request(log_event.service)

            # Broadcast to dashboard
            if self.ws_manager:
                msg = WSMessage(
                    type="log_event",
                    data=log_event.model_dump(mode="json"),
                )
                await self.ws_manager.broadcast(msg)
        except Exception as e:
            logger.error(f"Error handling log event: {e}")

    async def _handle_metric(self, data: dict) -> None:
        try:
            metric = Metric(**data)
            await self.repository.insert_metric(metric)
            self.metrics_engine.record_metric(metric)

            # Feed to anomaly detector
            anomaly = self.anomaly_detector.add_data_point(metric)
            if anomaly:
                self._anomaly_buffer.append(anomaly)

                # Run RCA when enough anomalies accumulate and cooldown has passed
                now = time.time()
                if (
                    len(self._anomaly_buffer) >= 3
                    and (now - self._last_rca_time) > self._rca_cooldown
                ):
                    incident = await self.root_cause_analyzer.analyze(
                        self._anomaly_buffer, self.metrics_engine,
                    )
                    if incident:
                        await self.repository.insert_incident(incident)
                        self.metrics_engine.increment_active_incidents()
                        if self.ws_manager:
                            msg = WSMessage(
                                type="new_incident",
                                data=incident.model_dump(mode="json"),
                            )
                            await self.ws_manager.broadcast(msg)
                        self._anomaly_buffer.clear()
                        self._last_rca_time = now
        except Exception as e:
            logger.error(f"Error handling metric: {e}")
