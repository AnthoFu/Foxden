/**
 * Hook para monitoreo de estado y ejecución de acciones del servidor de Minecraft.
 */

import { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';
import { ServerStatus } from '../types';

export function useEstadoServidor() {
  const [status, setStatus] = useState<ServerStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const actualizarEstado = useCallback(async () => {
    try {
      const data = await api.obtenerEstado();
      setStatus(data);
      setError(null);
    } catch (err: any) {
      console.error('Error al obtener estado del servidor:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    actualizarEstado();

    // Sondeo más rápido durante transiciones de estado
    const tiempoIntervalo = status?.state === 'STARTING' || status?.state === 'STOPPING' ? 1200 : 2500;
    const intervalo = window.setInterval(actualizarEstado, tiempoIntervalo);

    return () => clearInterval(intervalo);
  }, [actualizarEstado, status?.state]);

  const iniciarServidor = async () => {
    setActionLoading('start');
    setError(null);
    try {
      await api.iniciarServidor();
      await actualizarEstado();
    } catch (err: any) {
      setError(err.message || 'Error al iniciar el servidor');
    } finally {
      setActionLoading(null);
    }
  };

  const detenerServidor = async () => {
    setActionLoading('stop');
    setError(null);
    try {
      await api.detenerServidor();
      await actualizarEstado();
    } catch (err: any) {
      setError(err.message || 'Error al detener el servidor');
    } finally {
      setActionLoading(null);
    }
  };

  const reiniciarServidor = async () => {
    setActionLoading('restart');
    setError(null);
    try {
      await api.reiniciarServidor();
      await actualizarEstado();
    } catch (err: any) {
      setError(err.message || 'Error al reiniciar el servidor');
    } finally {
      setActionLoading(null);
    }
  };

  const iniciarTunel = async () => {
    setActionLoading('tunnel');
    setError(null);
    try {
      await api.iniciarTunel();
      await actualizarEstado();
    } catch (err: any) {
      setError(err.message || 'Error al iniciar el túnel');
    } finally {
      setActionLoading(null);
    }
  };

  const iniciarServidoryTunel = async () => {
    setActionLoading('start');
    setError(null);
    try {
      // Iniciar el túnel en paralelo con tolerancia a fallas
      await api.iniciarTunel().catch((e) => console.warn('Aviso de inicio de túnel:', e));
      await api.iniciarServidor();
      await actualizarEstado();
    } catch (err: any) {
      setError(err.message || 'Error al iniciar servidor y túnel');
    } finally {
      setActionLoading(null);
    }
  };

  return {
    status,
    loading,
    actionLoading,
    error,
    limpiarError: () => setError(null),
    actualizarEstado,
    iniciarServidor,
    detenerServidor,
    reiniciarServidor,
    iniciarTunel,
    iniciarServidoryTunel,

    // Alias en inglés para compatibilidad
    clearError: () => setError(null),
    refreshStatus: actualizarEstado,
    startServer: iniciarServidor,
    stopServer: detenerServidor,
    restartServer: reiniciarServidor,
    startTunnel: iniciarTunel,
    startServerAndTunnel: iniciarServidoryTunel,
  };
}

// Alias de compatibilidad
export const useServerStatus = useEstadoServidor;
