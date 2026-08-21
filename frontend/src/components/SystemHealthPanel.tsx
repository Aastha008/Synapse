import React from 'react';
import { SystemHealthSnapshot } from '../types';
import { ArrowUpRight, ArrowDownRight, Database, Clock, AlertCircle } from 'lucide-react';

export const SystemHealthPanel: React.FC<{ health: SystemHealthSnapshot | null }> = ({ health }) => {
  if (!health) return <div className="p-4 text-gray-400 animate-pulse">Loading health data...</div>;

  const aggregated = health.services.reduce(
    (acc, s) => {
      acc.avgLatency += s.latency_ms;
      acc.avgError += s.error_rate;
      acc.avgCpu += s.cpu_percent;
      if (s.db_connections_percent) acc.maxDb = Math.max(acc.maxDb, s.db_connections_percent);
      return acc;
    },
    { avgLatency: 0, avgError: 0, avgCpu: 0, maxDb: 0 }
  );

  const numServices = health.services.length || 1;
  aggregated.avgLatency /= numServices;
  aggregated.avgError /= numServices;
  aggregated.avgCpu /= numServices;

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'bg-green-500';
      case 'degraded': return 'bg-yellow-500';
      case 'critical': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 p-4 bg-gray-950">
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 shadow-md relative overflow-hidden">
        <div className="flex justify-between items-start mb-2">
          <h3 className="text-gray-400 font-medium text-sm flex items-center"><Clock className="w-4 h-4 mr-1"/> API Latency</h3>
          <span className={`flex items-center text-sm font-semibold ${aggregated.avgLatency > 200 ? 'text-red-400' : aggregated.avgLatency > 120 ? 'text-yellow-400' : 'text-green-400'}`}>
            {aggregated.avgLatency > 120 ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
            {aggregated.avgLatency > 120 ? 'Elevated' : 'Normal'}
          </span>
        </div>
        <div className="text-3xl font-bold text-gray-100">{aggregated.avgLatency.toFixed(0)} ms</div>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 shadow-md relative">
        <div className="flex justify-between items-start mb-2">
          <h3 className="text-gray-400 font-medium text-sm flex items-center"><AlertCircle className="w-4 h-4 mr-1"/> Error Rate</h3>
          <span className={`flex items-center text-sm font-semibold ${aggregated.avgError > 0.01 ? 'text-red-400' : 'text-green-400'}`}>
            {aggregated.avgError > 0.01 ? <ArrowUpRight className="w-4 h-4" /> : null}
            {aggregated.avgError > 0.01 ? 'High' : 'Normal'}
          </span>
        </div>
        <div className="text-3xl font-bold text-gray-100">{(aggregated.avgError * 100).toFixed(2)}%</div>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 shadow-md relative">
        <div className="flex justify-between items-start mb-2">
          <h3 className="text-gray-400 font-medium text-sm flex items-center"><Database className="w-4 h-4 mr-1"/> DB Connections</h3>
          {aggregated.maxDb > 80 && <AlertCircle className="w-4 h-4 text-red-500 animate-pulse" />}
        </div>
        <div className="text-3xl font-bold text-gray-100">{aggregated.maxDb.toFixed(0)}%</div>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 shadow-md relative flex items-center justify-between">
        <div>
          <h3 className="text-gray-400 font-medium text-sm mb-1">Overall Status</h3>
          <div className="text-xl font-bold uppercase tracking-wide flex items-center mt-2">
            <span className={`w-4 h-4 rounded-full mr-2 shadow-[0_0_10px_currentColor] animate-pulse ${getStatusColor(health.overall_status)}`} />
            {health.overall_status}
          </div>
        </div>
        <div className="text-right">
          <div className="text-xs text-gray-500">Active Incidents</div>
          <div className="text-2xl font-bold text-gray-300">{health.active_incidents}</div>
        </div>
      </div>
    </div>
  );
};
