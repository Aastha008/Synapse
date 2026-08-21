import React, { useEffect, useState, useRef } from 'react';
import { LogEvent } from '../types';
import { fetchLogs } from '../services/api';
import { Terminal, Pause, Play } from 'lucide-react';

export const LogViewer: React.FC<{ newLog: LogEvent | null }> = ({ newLog }) => {
  const [logs, setLogs] = useState<LogEvent[]>([]);
  const [isPaused, setIsPaused] = useState(false);
  const logsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchLogs(undefined, undefined, 50).then(setLogs).catch(console.error);
  }, []);

  useEffect(() => {
    if (newLog && !isPaused) {
      setLogs(prev => [...prev.slice(-49), newLog]);
    }
  }, [newLog, isPaused]);

  useEffect(() => {
    if (!isPaused) {
      logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, isPaused]);

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'INFO': return 'text-blue-400';
      case 'WARN': return 'text-yellow-400';
      case 'ERROR': return 'text-red-400';
      case 'CRITICAL': return 'text-red-500 font-bold bg-red-900/20 px-1 rounded';
      default: return 'text-gray-400';
    }
  };

  const formatTime = (ts: string) => {
    try {
      const d = new Date(ts);
      return d.toTimeString().split(' ')[0] + '.' + String(d.getMilliseconds()).padStart(3, '0');
    } catch {
      return ts;
    }
  };

  return (
    <div className="bg-[#0c0c0c] border border-gray-800 rounded-lg flex flex-col h-80 shadow-inner">
      <div className="flex justify-between items-center p-3 border-b border-gray-800 bg-gray-900 rounded-t-lg">
        <div className="flex items-center space-x-2 text-sm text-gray-400 font-mono">
          <Terminal className="w-4 h-4" />
          <span>Live Logs</span>
        </div>
        <button 
          onClick={() => setIsPaused(!isPaused)}
          className="text-gray-400 hover:text-white flex items-center space-x-1 text-xs bg-gray-800 px-2 py-1 rounded"
        >
          {isPaused ? <><Play className="w-3 h-3"/><span>Resume</span></> : <><Pause className="w-3 h-3"/><span>Pause</span></>}
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-3 font-mono text-xs space-y-1">
        {logs.map((log, i) => (
          <div key={i} className="flex hover:bg-gray-800/50 px-1 py-0.5 rounded break-all">
            <span className="text-gray-600 mr-3 shrink-0">{formatTime(log.timestamp)}</span>
            <span className={`w-16 shrink-0 ${getLevelColor(log.level)}`}>[{log.level}]</span>
            <span className="text-gray-500 w-32 shrink-0">{log.service}</span>
            <span className="text-gray-300">{log.message}</span>
          </div>
        ))}
        <div ref={logsEndRef} />
      </div>
    </div>
  );
};
