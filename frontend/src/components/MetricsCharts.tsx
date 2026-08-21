import React, { useEffect, useState } from 'react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, Legend } from 'recharts';
import { fetchAllTimeseries } from '../services/api';

const SERVICE_COLORS: Record<string, string> = {
  'api-gateway': '#3b82f6',
  'payment-service': '#ef4444',
  'user-service': '#10b981',
  'database-service': '#f59e0b',
  'notification-service': '#8b5cf6',
};

export const MetricsCharts: React.FC = () => {
  const [rawTimeseries, setRawTimeseries] = useState<Record<string, Record<string, { data_points: { timestamp: string; value: number }[] }>>>({});

  useEffect(() => {
    const loadData = async () => {
      try {
        const res = await fetchAllTimeseries(5);
        if (res && typeof res === 'object') {
          setRawTimeseries(res);
        }
      } catch (e) {
        console.error('Failed to fetch timeseries', e);
      }
    };
    loadData();
    const interval = setInterval(loadData, 3000);
    return () => clearInterval(interval);
  }, []);

  // Transform raw data: { [service]: { [metric]: { data_points: [...] } } }
  // into an array of { timestamp, [service]: value } sorted by time for a given metric
  const formatMetricData = (metricKey: string) => {
    const timeMap: Record<string, Record<string, number>> = {};
    const services = Object.keys(rawTimeseries);

    services.forEach(service => {
      const metricObj = rawTimeseries[service]?.[metricKey];
      if (metricObj?.data_points) {
        metricObj.data_points.forEach(dp => {
          // Round timestamp to nearest 2-3 seconds for grouping
          const timeKey = dp.timestamp;
          if (!timeMap[timeKey]) {
            timeMap[timeKey] = {};
          }
          timeMap[timeKey][service] = dp.value;
        });
      }
    });

    const sortedTimestamps = Object.keys(timeMap).sort();
    // Keep last 30 data points
    const recentTimestamps = sortedTimestamps.slice(-30);

    return recentTimestamps.map(ts => ({
      timestamp: ts,
      ...timeMap[ts]
    }));
  };

  const renderChart = (title: string, metricKey: string, unit: string = '') => {
    const chartData = formatMetricData(metricKey);
    const activeServices = Object.keys(rawTimeseries).filter(
      s => rawTimeseries[s]?.[metricKey]?.data_points?.length
    );

    return (
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 shadow-md h-72 flex flex-col">
        <div className="flex justify-between items-center mb-2">
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">{title}</h3>
          <span className="text-[10px] text-gray-500">{unit}</span>
        </div>
        <div className="flex-1 w-full min-h-0">
          {chartData.length === 0 ? (
            <div className="h-full flex items-center justify-center text-gray-600 text-xs">Accumulating metric telemetry...</div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
                <XAxis 
                  dataKey="timestamp" 
                  stroke="#4b5563" 
                  fontSize={10} 
                  tickFormatter={(t) => {
                    try {
                      return new Date(t).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                    } catch {
                      return '';
                    }
                  }} 
                />
                <YAxis stroke="#4b5563" fontSize={10} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', fontSize: '11px', borderRadius: '6px' }}
                  itemStyle={{ padding: '2px 0' }}
                  labelFormatter={(l) => {
                    try {
                      return new Date(l).toLocaleTimeString();
                    } catch {
                      return String(l);
                    }
                  }}
                />
                <Legend wrapperStyle={{ fontSize: '10px', paddingTop: '4px' }} />
                {activeServices.map((s) => (
                  <Line 
                    key={s} 
                    type="monotone" 
                    dataKey={s} 
                    name={s}
                    stroke={SERVICE_COLORS[s] || '#9ca3af'} 
                    strokeWidth={1.5}
                    dot={false}
                    isAnimationActive={false}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {renderChart('API Latency', 'latency_ms', 'ms')}
      {renderChart('Error Rate', 'error_rate', 'ratio')}
      {renderChart('CPU Utilization', 'cpu_percent', '%')}
      {renderChart('Database Connections', 'db_connections_percent', '%')}
    </div>
  );
};
