import { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';
import { ServerStatus } from '../types';

export function useServerStatus() {
  const [status, setStatus] = useState<ServerStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refreshStatus = useCallback(async () => {
    try {
      const data = await api.getStatus();
      setStatus(data);
      setError(null);
    } catch (err: any) {
      console.error('Failed to fetch server status:', err);
      // Keep previous status or show error
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshStatus();

    // Fast polling if starting or stopping, normal 2.5s interval otherwise
    const intervalTime = status?.state === 'STARTING' || status?.state === 'STOPPING' ? 1200 : 2500;
    const interval = window.setInterval(refreshStatus, intervalTime);

    return () => clearInterval(interval);
  }, [refreshStatus, status?.state]);

  const startServer = async () => {
    setActionLoading('start');
    setError(null);
    try {
      await api.startServer();
      await refreshStatus();
    } catch (err: any) {
      setError(err.message || 'Error al iniciar el servidor');
    } finally {
      setActionLoading(null);
    }
  };

  const stopServer = async () => {
    setActionLoading('stop');
    setError(null);
    try {
      await api.stopServer();
      await refreshStatus();
    } catch (err: any) {
      setError(err.message || 'Error al detener el servidor');
    } finally {
      setActionLoading(null);
    }
  };

  const restartServer = async () => {
    setActionLoading('restart');
    setError(null);
    try {
      await api.restartServer();
      await refreshStatus();
    } catch (err: any) {
      setError(err.message || 'Error al reiniciar el servidor');
    } finally {
      setActionLoading(null);
    }
  };

  return {
    status,
    loading,
    actionLoading,
    error,
    clearError: () => setError(null),
    refreshStatus,
    startServer,
    stopServer,
    restartServer,
  };
}
