import { SystemHealthSnapshot, Incident, LogEvent } from '../types';

export const fetchHealth = async (): Promise<SystemHealthSnapshot> => {
  const res = await fetch('/api/health');
  return res.json();
};

export const fetchIncidents = async (): Promise<Incident[]> => {
  const res = await fetch('/api/incidents');
  return res.json();
};

export const fetchActiveIncidents = async (): Promise<Incident[]> => {
  const res = await fetch('/api/incidents/active');
  return res.json();
};

export const fetchMetricsTimeseries = async (service: string, metric: string, minutes: number = 5) => {
  const res = await fetch(`/api/metrics/timeseries?service=${service}&metric=${metric}&minutes=${minutes}`);
  return res.json();
};

export const fetchAllTimeseries = async (minutes: number = 5) => {
  const res = await fetch(`/api/metrics/all-timeseries?minutes=${minutes}`);
  return res.json();
};

export const fetchErrorDistribution = async () => {
  const res = await fetch('/api/metrics/errors');
  return res.json();
};

export const fetchLogs = async (service?: string, level?: string, limit: number = 100): Promise<LogEvent[]> => {
  const params = new URLSearchParams();
  if (service) params.append('service', service);
  if (level) params.append('level', level);
  if (limit) params.append('limit', limit.toString());
  const res = await fetch(`/api/logs?${params.toString()}`);
  return res.json();
};

export const triggerScenario = async (name: string) => {
  const res = await fetch(`/api/scenario/trigger?name=${name}`);
  return res.json();
};

export const resetScenario = async () => {
  const res = await fetch('/api/scenario/reset');
  return res.json();
};
