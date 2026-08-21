import time
import asyncio
import random
from models.schemas import LogEvent, Metric, LogLevel
from config import BASELINE_METRICS, SERVICES, SIMULATION_INTERVAL_MS, AUTO_TRIGGER_INCIDENT, INCIDENT_TRIGGER_DELAY_SECONDS
from simulator.scenario_engine import SCENARIOS, BaseScenario
from pipeline.queue import EventQueue

class LogGenerator:
    def __init__(self, queue: EventQueue):
        self._queue = queue
        self._running = False
        self._current_scenario: BaseScenario | None = None
        self._scenario_start: float | None = None
        self._deployment_version = 'v2.2'
        self._start_time = time.time()
    
    async def start(self) -> None:
        self._running = True
        self._start_time = time.time()
        
        while self._running:
            now = time.time()
            
            if AUTO_TRIGGER_INCIDENT and not self._current_scenario:
                if (now - self._start_time) > INCIDENT_TRIGGER_DELAY_SECONDS:
                    self.trigger_incident()
            
            progress = 0.0
            if self._current_scenario and self._scenario_start:
                elapsed = now - self._scenario_start
                progress = min(1.0, elapsed / self._current_scenario.duration_seconds)
                if progress >= 1.0:
                    pass # Keep scenario active or reset
            
            for service in SERVICES:
                metrics = self._generate_metrics(service, progress)
                for metric in metrics:
                    await self._queue.publish('metric', metric)
                
                if random.random() < 0.3:
                    log_event = self._generate_normal_log(service, progress)
                    await self._queue.publish('log', log_event)
            
            if self._current_scenario and progress > 0.0:
                extra_logs = self._current_scenario.get_extra_logs(progress)
                for service, level, msg in extra_logs:
                    log_event = LogEvent(
                        service=service,
                        level=level,
                        message=msg,
                        metadata={"deployment": self._deployment_version}
                    )
                    await self._queue.publish('log', log_event)
                    
            await asyncio.sleep(SIMULATION_INTERVAL_MS / 1000.0)
    
    def trigger_incident(self, scenario_name: str = 'db_connection_exhaustion') -> None:
        self._current_scenario = SCENARIOS[scenario_name]()
        self._scenario_start = time.time()
        self._deployment_version = 'v2.3'
    
    def reset(self) -> None:
        self._current_scenario = None
        self._scenario_start = None
        self._deployment_version = 'v2.2'
        self._start_time = time.time()
    
    def _generate_normal_log(self, service: str, progress: float) -> LogEvent:
        baseline = BASELINE_METRICS.get(service, {})
        base_lat = baseline.get("latency_ms", 100)
        
        if self._current_scenario and progress > 0.0:
            mods = self._current_scenario.get_metric_modifiers(progress).get(service, {})
            base_lat *= mods.get("latency_ms", 1.0)
            
        latency = max(1.0, random.gauss(base_lat, base_lat * 0.1))
        
        status = 200
        level = LogLevel.INFO
        if random.random() < 0.05:
            status = random.choice([400, 401, 403, 404])
            level = LogLevel.WARN
        
        return LogEvent(
            service=service,
            level=level,
            message=f"GET /api/{service.split('-')[0]} {status} {latency:.0f}ms",
            latency_ms=latency,
            status_code=status,
            metadata={"deployment": self._deployment_version}
        )
    
    def _generate_metrics(self, service: str, progress: float) -> list[Metric]:
        baseline = BASELINE_METRICS.get(service, {})
        metrics = []
        
        mods = {}
        if self._current_scenario and progress > 0.0:
            mods = self._current_scenario.get_metric_modifiers(progress).get(service, {})
            
        for m_name, b_val in baseline.items():
            mult = mods.get(m_name, 1.0)
            val = b_val * mult
            val = random.gauss(val, val * 0.05)
            metrics.append(Metric(service=service, metric_name=m_name, value=val))
            
        return metrics

    async def stop(self) -> None:
        self._running = False
