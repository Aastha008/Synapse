import React from 'react';
import { Incident } from '../types';
import { CheckCircle, AlertTriangle, Cpu } from 'lucide-react';

export const IncidentPanel: React.FC<{ incidents: Incident[] }> = ({ incidents }) => {
  const activeIncident = incidents.find(i => i.status !== 'RESOLVED');

  if (!activeIncident) {
    return (
      <div className="h-full bg-gray-900 border border-gray-800 rounded-lg p-8 flex flex-col items-center justify-center shadow-lg text-center">
        <div className="w-16 h-16 bg-green-500/10 rounded-full flex items-center justify-center mb-4 shadow-[0_0_30px_rgba(34,197,94,0.2)]">
          <CheckCircle className="w-8 h-8 text-green-500" />
        </div>
        <h2 className="text-xl font-semibold text-gray-200">System Healthy</h2>
        <p className="text-gray-500 mt-2">No active incidents detected.</p>
      </div>
    );
  }

  const sevColors = {
    CRITICAL: 'bg-red-600 text-white shadow-red-900/50',
    HIGH: 'bg-orange-500 text-white',
    MEDIUM: 'bg-yellow-500 text-gray-900',
    LOW: 'bg-blue-500 text-white'
  };

  return (
    <div className="h-full bg-gray-900 border border-red-900/50 rounded-lg shadow-lg flex flex-col relative overflow-hidden">
      <div className="absolute top-0 left-0 w-full h-1 bg-red-500 animate-pulse" />
      <div className="p-5 border-b border-gray-800 bg-gray-900/50">
        <div className="flex items-center justify-between mb-3">
          <span className={`px-3 py-1 text-xs font-bold rounded-full shadow-lg ${sevColors[activeIncident.severity]}`}>
            {activeIncident.severity}
          </span>
          <span className="text-xs text-gray-400">{new Date(activeIncident.detected_at).toLocaleTimeString()}</span>
        </div>
        <h2 className="text-xl font-bold text-gray-100 flex items-center">
          <AlertTriangle className="w-5 h-5 mr-2 text-red-500" />
          {activeIncident.title}
        </h2>
      </div>

      <div className="p-5 flex-1 overflow-y-auto space-y-6">
        <div>
          <h3 className="text-sm font-semibold text-gray-400 mb-2 uppercase tracking-wider flex items-center">
            <Cpu className="w-4 h-4 mr-1"/> AI Root Cause Analysis
          </h3>
          <div className="bg-gray-950 p-4 rounded border border-gray-800">
            <p className="text-sm text-gray-200 leading-relaxed">{activeIncident.root_cause}</p>
            <div className="mt-4 flex items-center">
              <span className="text-xs text-gray-500 mr-3">Confidence:</span>
              <div className="flex-1 h-2 bg-gray-800 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-blue-500 transition-all duration-1000" 
                  style={{ width: `${activeIncident.confidence * 100}%` }} 
                />
              </div>
              <span className="text-xs font-medium text-blue-400 ml-3">{(activeIncident.confidence * 100).toFixed(0)}%</span>
            </div>
          </div>
        </div>

        <div>
          <h3 className="text-sm font-semibold text-gray-400 mb-2 uppercase tracking-wider">Affected Services</h3>
          <div className="flex flex-wrap gap-2">
            {activeIncident.affected_services.map(s => (
              <span key={s} className="px-2 py-1 bg-red-900/30 text-red-400 border border-red-900/50 rounded text-xs font-mono">
                {s}
              </span>
            ))}
          </div>
        </div>

        <div>
          <h3 className="text-sm font-semibold text-gray-400 mb-3 uppercase tracking-wider">Evidence Timeline</h3>
          <div className="space-y-4 pl-2 border-l-2 border-gray-800 ml-2">
            {activeIncident.evidence.map((ev, i) => (
              <div key={i} className="relative pl-4">
                <div className="absolute -left-[21px] top-1 w-3 h-3 rounded-full bg-gray-700 border-2 border-gray-900" />
                <div className="text-xs text-gray-500 mb-1">{new Date(ev.timestamp).toLocaleTimeString()} - {ev.service}</div>
                <div className="text-sm text-gray-300">{ev.description}</div>
              </div>
            ))}
          </div>
        </div>

        <div>
          <h3 className="text-sm font-semibold text-gray-400 mb-2 uppercase tracking-wider">Recommended Actions</h3>
          <ul className="space-y-2">
            {activeIncident.recommended_actions.map((act, i) => (
              <li key={i} className="flex items-start text-sm text-gray-300 bg-gray-800/30 p-2 rounded border border-gray-800/50">
                <div className="w-5 h-5 rounded-full bg-blue-900/50 text-blue-400 flex items-center justify-center text-xs mr-3 mt-0.5 shrink-0">
                  {i + 1}
                </div>
                {act}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};
