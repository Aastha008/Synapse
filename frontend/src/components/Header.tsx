import React from 'react';
import { Activity, AlertTriangle, RefreshCw } from 'lucide-react';
import { triggerScenario, resetScenario } from '../services/api';

interface HeaderProps {
  isConnected: boolean;
}

export const Header: React.FC<HeaderProps> = ({ isConnected }) => {
  return (
    <header className="flex justify-between items-center p-4 border-b border-gray-800 bg-gray-900 shadow-md">
      <div className="flex items-center space-x-3">
        <Activity className="text-blue-500 w-8 h-8" />
        <div>
          <h1 className="text-xl font-bold tracking-tight">Synapse</h1>
          <p className="text-xs text-gray-400">AI Observability & Root Cause Intelligence</p>
        </div>
      </div>
      <div className="flex items-center space-x-6">
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]' : 'bg-red-500'}`} />
          <span className="text-sm font-medium text-gray-300">
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
        <div className="flex space-x-3">
          <button 
            onClick={() => triggerScenario('db_connection_exhaustion')}
            className="flex items-center px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-md text-sm transition-colors shadow-lg shadow-red-900/20 cursor-pointer"
          >
            <AlertTriangle className="w-4 h-4 mr-2" />
            Trigger Incident
          </button>
          <button 
            onClick={() => resetScenario()}
            className="flex items-center px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-md text-sm transition-colors cursor-pointer"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Reset
          </button>
        </div>
      </div>
    </header>
  );
};
