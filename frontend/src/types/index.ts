export interface ServiceHealth {
  service: string;
  latency_ms: number;
  latency_trend: number;
  latency_trend_direction: 'up' | 'down' | 'stable';
  error_rate: number;
  error_rate_trend: number;
  error_rate_trend_direction: 'up' | 'down' | 'stable';
  cpu_percent: number;
  memory_percent: number;
  db_connections_percent: number | null;
  status: 'healthy' | 'degraded' | 'critical';
  request_count: number;
}

export interface Incident {
  id: string;
  detected_at: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  title: string;
  root_cause: string;
  confidence: number;
  affected_services: string[];
  evidence: Array<{timestamp: string; type: string; service: string; description: string; value?: number}>;
  recommended_actions: string[];
  status: 'ACTIVE' | 'INVESTIGATING' | 'RESOLVED';
}

export interface SystemHealthSnapshot {
  services: ServiceHealth[];
  overall_status: 'healthy' | 'degraded' | 'critical';
  active_incidents: number;
}

export interface LogEvent {
  timestamp: string;
  service: string;
  level: 'INFO' | 'WARN' | 'ERROR' | 'CRITICAL';
  message: string;
}
