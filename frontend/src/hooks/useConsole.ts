import { useState, useEffect, useRef, useCallback } from 'react';
import { api } from '../services/api';

export function useConsole() {
  const [logs, setLogs] = useState<string[]>([]);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [autoscroll, setAutoscroll] = useState<boolean>(true);
  const [command, setCommand] = useState<string>('');
  const [history, setHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState<number>(-1);

  const wsRef = useRef<WebSocket | null>(null);
  const terminalEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    let isMounted = true;
    let reconnectTimeout: number;

    const connect = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/console`;

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!isMounted) return;
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        if (!isMounted) return;
        setLogs((prev) => {
          const next = [...prev, event.data];
          if (next.length > 1500) {
            return next.slice(next.length - 1500);
          }
          return next;
        });
      };

      ws.onclose = () => {
        if (!isMounted) return;
        setIsConnected(false);
        reconnectTimeout = window.setTimeout(connect, 3000);
      };

      ws.onerror = () => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.close();
        }
      };
    };

    connect();

    return () => {
      isMounted = false;
      clearTimeout(reconnectTimeout);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  useEffect(() => {
    if (autoscroll && terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoscroll]);

  const sendConsoleCommand = useCallback(
    async (cmdToSend?: string) => {
      const text = (cmdToSend ?? command).trim();
      if (!text) return;

      // Add to command history
      setHistory((prev) => [...prev, text]);
      setHistoryIndex(-1);
      setCommand('');

      try {
        await api.sendCommand(text);
      } catch (err: any) {
        setLogs((prev) => [...prev, `[FOXDEN] Error al enviar comando: ${err.message}`]);
      }
    },
    [command]
  );

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (history.length === 0) return;
      const nextIndex = historyIndex === -1 ? history.length - 1 : Math.max(0, historyIndex - 1);
      setHistoryIndex(nextIndex);
      setCommand(history[nextIndex]);
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (history.length === 0 || historyIndex === -1) return;
      const nextIndex = historyIndex + 1;
      if (nextIndex >= history.length) {
        setHistoryIndex(-1);
        setCommand('');
      } else {
        setHistoryIndex(nextIndex);
        setCommand(history[nextIndex]);
      }
    }
  };

  const clearLogs = () => setLogs([]);

  return {
    logs,
    isConnected,
    autoscroll,
    setAutoscroll,
    command,
    setCommand,
    terminalEndRef,
    sendConsoleCommand,
    handleKeyDown,
    clearLogs,
  };
}
