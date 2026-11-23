/**
 * Barra superior con métricas en tiempo real y controles de inicio/parada.
 */

import React from 'react';
import { Play, RotateCw, Square, Cpu, HardDrive, Clock, Globe } from 'lucide-react';
import { ServerStatus } from '../types';
import { formatearTiempoActivo } from '../utils/format';

interface PropiedadesEncabezado {
  status: ServerStatus | null;
  loading: boolean;
  actionLoading: string | null;
  onStart: () => void;
  onStop: () => void;
  onRestart: () => void;
}

export const Header: React.FC<PropiedadesEncabezado> = ({
  status,
  actionLoading,
  onStart,
  onStop,
  onRestart,
}) => {
  const estadoServidor = status?.state || 'STOPPED';
  const estaInstalado = status?.is_installed ?? false;

  const obtenerInsigniaEstado = () => {
    switch (estadoServidor) {
      case 'RUNNING':
        return {
          text: 'EN LÍNEA',
          bg: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400',
          dot: 'bg-emerald-500 animate-pulse',
        };
      case 'STARTING':
        return {
          text: 'INICIANDO...',
          bg: 'bg-amber-500/10 border-amber-500/30 text-amber-400',
          dot: 'bg-amber-500 animate-ping',
        };
      case 'STOPPING':
        return {
          text: 'DETENIENDO...',
          bg: 'bg-rose-500/10 border-rose-500/30 text-rose-400',
          dot: 'bg-rose-500',
        };
      default:
        return {
          text: 'DETENIDO',
          bg: 'bg-slate-500/10 border-slate-500/30 text-slate-400',
          dot: 'bg-slate-500',
        };
    }
  };

  const insignia = obtenerInsigniaEstado();
  const tunelEnLinea = status?.tunnel?.state === 'RUNNING';
  const tunelEsperandoVinculacion = status?.tunnel?.state === 'WAITING_CLAIM';

  const puedeIniciar = estaInstalado && estadoServidor === 'STOPPED' && !actionLoading;
  const puedeReiniciar = estaInstalado && estadoServidor === 'RUNNING' && !actionLoading;
  const puedeDetener = (estadoServidor === 'RUNNING' || estadoServidor === 'STARTING') && !actionLoading;

  return (
    <header className="bg-dark-800 border-b border-dark-700 px-6 py-4 flex flex-wrap items-center justify-between gap-4">
      {/* Logotipo y Título */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-fox-500/10 border border-fox-500/20 flex items-center justify-center p-1.5 shadow-inner">
          <img src="/logo.png" alt="Foxden Logo" className="w-full h-full object-contain drop-shadow" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-tight text-white">Foxden</h1>
            <span className="text-[10px] font-semibold uppercase tracking-wider bg-fox-500/20 text-fox-400 border border-fox-500/30 px-1.5 py-0.5 rounded">
              Manager
            </span>
            <span className="text-[10px] font-mono font-medium text-slate-400 bg-dark-750 border border-dark-700 px-1.5 py-0.5 rounded">
              v{status?.app_version || '1.0.0'}
            </span>
          </div>
          <p className="text-xs text-slate-400">Panel Autónomo de Minecraft</p>
        </div>
      </div>

      {/* Centro de Métricas */}
      <div className="flex items-center gap-3 flex-wrap">
        {/* Insignia de Estado */}
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-bold tracking-wider ${insignia.bg}`}>
          <span className={`w-2 h-2 rounded-full ${insignia.dot}`} />
          {insignia.text}
        </div>

        {/* CPU */}
        <div className="flex items-center gap-2 bg-dark-750 border border-dark-700 px-3 py-1 rounded-lg text-xs">
          <Cpu className="w-3.5 h-3.5 text-blue-400" />
          <span className="text-slate-400 font-medium">CPU</span>
          <span className="font-mono font-semibold text-slate-200">{status ? `${status.cpu_percent}%` : '0%'}</span>
        </div>

        {/* Memoria RAM */}
        <div className="flex items-center gap-2 bg-dark-750 border border-dark-700 px-3 py-1 rounded-lg text-xs">
          <HardDrive className="w-3.5 h-3.5 text-amber-400" />
          <span className="text-slate-400 font-medium">RAM</span>
          <span className="font-mono font-semibold text-slate-200">{status ? `${status.memory_mb} MB` : '0 MB'}</span>
        </div>

        {/* Tiempo de Actividad */}
        <div className="flex items-center gap-2 bg-dark-750 border border-dark-700 px-3 py-1 rounded-lg text-xs">
          <Clock className="w-3.5 h-3.5 text-emerald-400" />
          <span className="text-slate-400 font-medium">UPTIME</span>
          <span className="font-mono font-semibold text-slate-200">{status ? formatearTiempoActivo(status.uptime_seconds) : '0s'}</span>
        </div>

        {/* Túnel Playit */}
        <div className="flex items-center gap-2 bg-dark-750 border border-dark-700 px-3 py-1 rounded-lg text-xs">
          <Globe className="w-3.5 h-3.5 text-purple-400" />
          <span className="text-slate-400 font-medium">TÚNEL</span>
          <span
            className={`font-semibold ${
              tunelEnLinea ? 'text-emerald-400' : tunelEsperandoVinculacion ? 'text-amber-400' : 'text-slate-400'
            }`}
          >
            {tunelEnLinea ? 'ONLINE' : tunelEsperandoVinculacion ? 'VINCULAR' : 'OFFLINE'}
          </span>
        </div>
      </div>

      {/* Botones de Acción */}
      <div className="flex items-center gap-2">
        <button
          onClick={onStart}
          disabled={!puedeIniciar}
          title={!estaInstalado ? 'Primero debes instalar una versión de Minecraft' : ''}
          className="flex items-center gap-1.5 px-4 py-2 rounded-lg font-semibold text-sm transition-all shadow-md bg-emerald-600 hover:bg-emerald-500 active:scale-95 text-white disabled:opacity-40 disabled:cursor-not-allowed disabled:active:scale-100"
        >
          {actionLoading === 'start' ? (
            <RotateCw className="w-4 h-4 animate-spin" />
          ) : (
            <Play className="w-4 h-4 fill-white" />
          )}
          <span>Iniciar</span>
        </button>

        <button
          onClick={onRestart}
          disabled={!puedeReiniciar}
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg font-semibold text-sm transition-all bg-dark-700 hover:bg-dark-750 active:scale-95 text-amber-400 border border-dark-700 hover:border-amber-500/30 disabled:opacity-30 disabled:cursor-not-allowed disabled:active:scale-100"
        >
          <RotateCw className={`w-4 h-4 ${actionLoading === 'restart' ? 'animate-spin' : ''}`} />
          <span>Reiniciar</span>
        </button>

        <button
          onClick={onStop}
          disabled={!puedeDetener}
          className="flex items-center gap-1.5 px-4 py-2 rounded-lg font-semibold text-sm transition-all bg-rose-600/90 hover:bg-rose-500 active:scale-95 text-white disabled:opacity-30 disabled:cursor-not-allowed disabled:active:scale-100"
        >
          {actionLoading === 'stop' ? (
            <RotateCw className="w-4 h-4 animate-spin" />
          ) : (
            <Square className="w-4 h-4 fill-white" />
          )}
          <span>Detener</span>
        </button>
      </div>
    </header>
  );
};
