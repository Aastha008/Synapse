import React, { useEffect, useState } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { fetchErrorDistribution } from '../services/api';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

export const ErrorDistribution: React.FC = () => {
  const [data, setData] = useState<{name: string; value: number}[]>([]);

  useEffect(() => {
    const loadData = async () => {
      try {
        const res = await fetchErrorDistribution();
        const formatted = Array.isArray(res) 
          ? res.map((d: { service?: string; name?: string; count?: number; value?: number }) => ({
              name: d.service || d.name || 'Unknown',
              value: Number(d.count ?? d.value ?? 0)
            })).filter(d => d.value > 0)
          : Object.entries(res).map(([k, v]) => ({ name: k, value: Number(v) })).filter(d => d.value > 0);
        setData(formatted);
      } catch (e) {
        console.error(e);
      }
    };
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 shadow-md h-80 flex flex-col">
      <h3 className="text-sm font-semibold text-gray-400 mb-2 uppercase tracking-wider">Error Distribution</h3>
      {data.length === 0 ? (
        <div className="flex-1 flex items-center justify-center text-gray-500 text-sm">No errors recorded</div>
      ) : (
        <div className="flex-1">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={80}
                paddingAngle={5}
                dataKey="value"
                stroke="none"
              >
                {data.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', fontSize: '12px', color: '#fff' }}
                itemStyle={{ color: '#fff' }}
              />
              <Legend wrapperStyle={{ fontSize: '12px' }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
};
