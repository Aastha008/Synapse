import { useEffect, useState } from 'react';
import { Header } from './components/Header';
import { SystemHealthPanel } from './components/SystemHealthPanel';
import { IncidentPanel } from './components/IncidentPanel';
import { ServiceMap } from './components/ServiceMap';
import { MetricsCharts } from './components/MetricsCharts';
import { LogViewer } from './components/LogViewer';
import { ErrorDistribution } from './components/ErrorDistribution';
import { useWebSocket } from './hooks/useWebSocket';
import { fetchHealth, fetchActiveIncidents } from './services/api';
import { SystemHealthSnapshot, Incident } from './types';

function App() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const defaultWsUrl = `${protocol}//${window.location.host}/ws`;
  const wsUrl = import.meta.env.VITE_WS_URL || defaultWsUrl;
  const { lastHealthUpdate, lastIncident, lastLog, isConnected } = useWebSocket(wsUrl);
  
  const [health, setHealth] = useState<SystemHealthSnapshot | null>(null);
  const [incidents, setIncidents] = useState<Incident[]>([]);

  // Initial load
  useEffect(() => {
    fetchHealth().then(setHealth).catch(console.error);
    fetchActiveIncidents().then(setIncidents).catch(console.error);
  }, []);

  // Polling for active incidents fallback
  useEffect(() => {
    const interval = setInterval(() => {
      fetchActiveIncidents().then(setIncidents).catch(console.error);
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  // Update state from websocket
  useEffect(() => {
    if (lastHealthUpdate) setHealth(lastHealthUpdate);
  }, [lastHealthUpdate]);

  useEffect(() => {
    if (lastIncident) {
      setIncidents(prev => {
        const filtered = prev.filter(i => i.id !== lastIncident.id);
        if (lastIncident.status === 'RESOLVED') return filtered;
        return [lastIncident, ...filtered];
      });
    }
  }, [lastIncident]);

  return (
    <div className="min-h-screen flex flex-col bg-gray-950 font-sans text-gray-100">
      <Header isConnected={isConnected} />
      
      <main className="flex-1 p-4 space-y-4 max-w-[1600px] mx-auto w-full">
        {/* Top bar: System Health Snapshot */}
        <SystemHealthPanel health={health} />
        
        {/* Middle row: Incidents & Map */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 h-auto lg:h-[450px]">
          <div className="lg:col-span-2">
            <IncidentPanel incidents={incidents} />
          </div>
          <div className="lg:col-span-1">
            <ServiceMap health={health} />
          </div>
        </div>

        {/* Charts row */}
        <div className="w-full">
          <MetricsCharts />
        </div>

        {/* Bottom row: Logs & Distribution */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2">
            <LogViewer newLog={lastLog} />
          </div>
          <div className="lg:col-span-1">
            <ErrorDistribution />
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
