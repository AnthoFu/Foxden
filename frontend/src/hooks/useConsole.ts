/**
 * Hook para la consola interactiva por WebSocket de Foxden.
 * Administra el buffer de logs, auto-scroll, historial de comandos y reconexión automática.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { api, obtenerToken } from '../services/api';

export function useConsola() {
  const [logs, setLogs] = useState<string[]>([]);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [autoscroll, setAutoscroll] = useState<boolean>(true);
  const [command, setCommand] = useState<string>('');
  const [history, setHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState<number>(-1);

  const wsRef = useRef<WebSocket | null>(null);
  const terminalEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    let montado = true;
    let tiempoReconexion: number;

    const conectarWebSocket = () => {
      const protocolo = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const token = obtenerToken();
      const queryToken = token ? `?token=${encodeURIComponent(token)}` : '';
      const urlWs = `${protocolo}//${window.location.host}/ws/console${queryToken}`;

      const ws = new WebSocket(urlWs);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!montado) return;
        setIsConnected(true);
      };

      ws.onmessage = (evento) => {
        if (!montado) return;
        setLogs((prev) => {
          const siguiente = [...prev, evento.data];
          if (siguiente.length > 1500) {
            return siguiente.slice(siguiente.length - 1500);
          }
          return siguiente;
        });
      };

      ws.onclose = () => {
        if (!montado) return;
        setIsConnected(false);
        tiempoReconexion = window.setTimeout(conectarWebSocket, 3000);
      };

      ws.onerror = () => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.close();
        }
      };
    };

    conectarWebSocket();

    return () => {
      montado = false;
      clearTimeout(tiempoReconexion);
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

  const enviarComandoConsola = useCallback(
    async (cmdAEnviar?: string) => {
      const texto = (cmdAEnviar ?? command).trim();
      if (!texto) return;

      // Registrar en el historial para navegación con flechas
      setHistory((prev) => [...prev, texto]);
      setHistoryIndex(-1);
      setCommand('');

      try {
        await api.enviarComando(texto);
      } catch (err: any) {
        setLogs((prev) => [...prev, `[FOXDEN] Error al enviar comando: ${err.message}`]);
      }
    },
    [command]
  );

  const manejarTeclas = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (history.length === 0) return;
      const siguienteIndice = historyIndex === -1 ? history.length - 1 : Math.max(0, historyIndex - 1);
      setHistoryIndex(siguienteIndice);
      setCommand(history[siguienteIndice]);
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (history.length === 0 || historyIndex === -1) return;
      const siguienteIndice = historyIndex + 1;
      if (siguienteIndice >= history.length) {
        setHistoryIndex(-1);
        setCommand('');
      } else {
        setHistoryIndex(siguienteIndice);
        setCommand(history[siguienteIndice]);
      }
    }
  };

  const limpiarRegistros = () => setLogs([]);

  return {
    logs,
    isConnected,
    autoscroll,
    setAutoscroll,
    command,
    setCommand,
    terminalEndRef,
    enviarComandoConsola,
    manejarTeclas,
    limpiarRegistros,

    // Alias en inglés para compatibilidad
    sendConsoleCommand: enviarComandoConsola,
    handleKeyDown: manejarTeclas,
    clearLogs: limpiarRegistros,
  };
}

// Alias de compatibilidad
export const useConsole = useConsola;
