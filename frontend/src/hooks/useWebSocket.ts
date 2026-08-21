import { useState, useEffect, useRef } from 'react';
import { SystemHealthSnapshot, Incident, LogEvent } from '../types';

export function useWebSocket(url: string) {
  const [lastHealthUpdate, setLastHealthUpdate] = useState<SystemHealthSnapshot | null>(null);
  const [lastIncident, setLastIncident] = useState<Incident | null>(null);
  const [lastLog, setLastLog] = useState<LogEvent | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    let timeoutId: ReturnType<typeof setTimeout>;

    const connect = () => {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => setIsConnected(true);
      
      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          if (message.type === 'health_update') {
            setLastHealthUpdate(message.data);
          } else if (message.type === 'new_incident' || message.type === 'incident_update') {
            setLastIncident(message.data);
          } else if (message.type === 'log_event') {
            setLastLog(message.data);
          }
        } catch (e) {
          console.error('Error parsing WS message', e);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        timeoutId = setTimeout(connect, 3000);
      };

      ws.onerror = () => {
        ws.close();
      };
    };

    connect();

    return () => {
      if (timeoutId) clearTimeout(timeoutId);
      if (wsRef.current) wsRef.current.close();
    };
  }, [url]);

  return { lastHealthUpdate, lastIncident, lastLog, isConnected };
}
