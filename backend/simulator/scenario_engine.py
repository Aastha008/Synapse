from abc import ABC, abstractmethod
from typing import Type
from models.schemas import LogLevel

class BaseScenario(ABC):
    name: str
    description: str
    duration_seconds: float = 120
    
    @abstractmethod
    def get_metric_modifiers(self, progress: float) -> dict[str, dict[str, float]]:
        pass
    
    @abstractmethod
    def get_extra_logs(self, progress: float) -> list[tuple[str, LogLevel, str]]:
        pass

class DatabaseConnectionExhaustion(BaseScenario):
    name = "db_connection_exhaustion"
    description = "Simulates database connection pool exhaustion."
    
    def get_metric_modifiers(self, progress: float) -> dict[str, dict[str, float]]:
        db_conn = min(1.0 + progress * 1.5, 98.0/40.0) # assuming baseline 40
        db_lat = 1.0 + progress * 3
        pay_lat = 1.0 + progress * 3.2
        pay_err = 1.0 + progress * 4.5
        pay_db_conn = 1.0 + progress * 1.8
        
        gw_lat = 1.0 + (progress * 2.5 if progress > 0.5 else 0)
        gw_err = 1.0 + (progress * 2 if progress > 0.5 else 0)
        
        return {
            "database-service": {
                "db_connections_percent": db_conn,
                "latency_ms": db_lat,
            },
            "payment-service": {
                "latency_ms": pay_lat,
                "error_rate": pay_err,
                "db_connections_percent": pay_db_conn,
            },
            "api-gateway": {
                "latency_ms": gw_lat,
                "error_rate": gw_err,
            }
        }
    
    def get_extra_logs(self, progress: float) -> list[tuple[str, LogLevel, str]]:
        logs = []
        if 0.19 < progress < 0.21:
            logs.append(("database-service", LogLevel.WARN, "Connection pool utilization above 80%"))
        if 0.39 < progress < 0.41:
            logs.append(("payment-service", LogLevel.WARN, "Increased query response time detected"))
        if 0.49 < progress < 0.51:
            logs.append(("database-service", LogLevel.ERROR, "Connection pool near exhaustion (94%)"))
        if 0.59 < progress < 0.61:
            logs.append(("payment-service", LogLevel.ERROR, "Transaction timeout after 3000ms"))
        if 0.69 < progress < 0.71:
            logs.append(("database-service", LogLevel.CRITICAL, "Connection pool exhausted (98%), new connections rejected"))
        if 0.79 < progress < 0.81:
            logs.append(("api-gateway", LogLevel.ERROR, "Downstream service degradation detected"))
        if 0.89 < progress < 0.91:
            logs.append(("payment-service", LogLevel.CRITICAL, "Multiple payment failures detected"))
        return logs

class MemoryLeak(BaseScenario):
    name = "memory_leak"
    description = "Simulates memory leak in user-service."
    
    def get_metric_modifiers(self, progress: float) -> dict[str, dict[str, float]]:
        return {
            "user-service": {
                "memory_percent": min(1.0 + progress * 2.0, 99.0/55.0), # baseline 55
                "latency_ms": 1.0 + progress * 2.5,
            }
        }
    
    def get_extra_logs(self, progress: float) -> list[tuple[str, LogLevel, str]]:
        logs = []
        if 0.49 < progress < 0.51:
            logs.append(("user-service", LogLevel.WARN, "High memory usage detected (80%)"))
        if 0.79 < progress < 0.81:
            logs.append(("user-service", LogLevel.ERROR, "GC pause time exceeded 1000ms"))
        if 0.95 < progress < 1.0:
            logs.append(("user-service", LogLevel.CRITICAL, "OutOfMemoryError: Java heap space"))
        return logs

class DeploymentRegression(BaseScenario):
    name = "deployment_regression"
    description = "Simulates a bad deployment causing latency spikes."
    
    def get_metric_modifiers(self, progress: float) -> dict[str, dict[str, float]]:
        return {
            "api-gateway": {
                "latency_ms": 1.0 + progress * 4.0,
                "error_rate": 1.0 + progress * 5.0,
            }
        }
    
    def get_extra_logs(self, progress: float) -> list[tuple[str, LogLevel, str]]:
        logs = []
        if 0.05 < progress < 0.1:
            logs.append(("api-gateway", LogLevel.INFO, "Starting deployment v2.3"))
        if 0.2 < progress < 0.25:
            logs.append(("api-gateway", LogLevel.WARN, "Upstream response times increasing"))
        if 0.5 < progress < 0.6:
            logs.append(("api-gateway", LogLevel.ERROR, "Failed to parse response from upstream"))
        return logs

SCENARIOS: dict[str, Type[BaseScenario]] = {
    'db_connection_exhaustion': DatabaseConnectionExhaustion,
    'memory_leak': MemoryLeak,
    'deployment_regression': DeploymentRegression,
}
