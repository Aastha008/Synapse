import React from 'react';
import { SystemHealthSnapshot } from '../types';

export const ServiceMap: React.FC<{ health: SystemHealthSnapshot | null }> = ({ health }) => {
  const getStatusColor = (serviceName: string) => {
    if (!health) return 'bg-gray-800 border-gray-700 text-gray-400';
    const s = health.services.find(s => s.service === serviceName);
    if (!s) return 'bg-gray-800 border-gray-700 text-gray-400';
    
    switch (s.status) {
      case 'healthy': return 'bg-green-950/40 border-green-500 text-green-400 shadow-[0_0_10px_rgba(34,197,94,0.2)]';
      case 'degraded': return 'bg-yellow-950/40 border-yellow-500 text-yellow-400 animate-pulse shadow-[0_0_12px_rgba(234,179,8,0.3)]';
      case 'critical': return 'bg-red-950/40 border-red-500 text-red-400 animate-pulse shadow-[0_0_15px_rgba(239,68,68,0.5)]';
      default: return 'bg-gray-800 border-gray-700 text-gray-400';
    }
  };

  const Node = ({ name, label }: { name: string; label: string }) => (
    <div className={`px-4 py-2.5 rounded-lg border-2 text-xs font-semibold flex items-center justify-center z-10 w-32 text-center transition-all duration-500 shadow-md ${getStatusColor(name)}`}>
      {label}
    </div>
  );

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 shadow-md h-full flex flex-col">
      <h3 className="text-sm font-semibold text-gray-400 mb-4 uppercase tracking-wider">Service Topology</h3>
      <div className="flex-1 relative flex items-center justify-center overflow-hidden min-h-[300px]">
        {/* Connection lines */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ zIndex: 0 }}>
          <line x1="50%" y1="18%" x2="20%" y2="50%" stroke="#374151" strokeWidth="2" strokeDasharray="4 4" />
          <line x1="50%" y1="18%" x2="50%" y2="50%" stroke="#374151" strokeWidth="2" strokeDasharray="4 4" />
          <line x1="50%" y1="18%" x2="80%" y2="50%" stroke="#374151" strokeWidth="2" strokeDasharray="4 4" />
          <line x1="20%" y1="50%" x2="50%" y2="82%" stroke="#374151" strokeWidth="2" strokeDasharray="4 4" />
          <line x1="50%" y1="50%" x2="50%" y2="82%" stroke="#374151" strokeWidth="2" strokeDasharray="4 4" />
          <line x1="80%" y1="50%" x2="50%" y2="82%" stroke="#374151" strokeWidth="2" strokeDasharray="4 4" />
        </svg>

        <div className="w-full h-full flex flex-col justify-between items-center py-2 relative z-10">
          <div className="w-full flex justify-center">
            <Node name="api-gateway" label="API Gateway" />
          </div>
          <div className="w-full flex justify-around px-2">
            <Node name="user-service" label="User Svc" />
            <Node name="payment-service" label="Payment Svc" />
            <Node name="notification-service" label="Notification" />
          </div>
          <div className="w-full flex justify-center">
            <Node name="database-service" label="Database Svc" />
          </div>
        </div>
      </div>
    </div>
  );
};
