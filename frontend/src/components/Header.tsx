import React from 'react';
import { Play, RotateCw, Square, Cpu, HardDrive, Clock, Globe } from 'lucide-react';
import { ServerStatus } from '../types';
import { formatUptime } from '../utils/format';

interface HeaderProps {
  status: ServerStatus | null;
  loading: boolean;
  actionLoading: string | null;
  onStart: () => void;
  onStop: () => void;
  onRestart: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  status,
  actionLoading,
  onStart,
  onStop,
  onRestart,
}) => {
  const state = status?.state || 'STOPPED';
  const isInstalled = status?.is_installed ?? false;

  const getStatusBadge = () => {
    switch (state) {
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

  const badge = getStatusBadge();
  const tunnelRunning = status?.tunnel?.state === 'RUNNING';
  const tunnelWaiting = status?.tunnel?.state === 'WAITING_CLAIM';

  const canStart = isInstalled && state === 'STOPPED' && !actionLoading;
  const canRestart = isInstalled && state === 'RUNNING' && !actionLoading;
  const canStop = (state === 'RUNNING' || state === 'STARTING') && !actionLoading;

  return (
    <header className="bg-dark-800 border-b border-dark-700 px-6 py-4 flex flex-wrap items-center justify-between gap-4">
      {/* Brand */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-fox-500/10 border border-fox-500/20 flex items-center justify-center text-2xl shadow-inner">
          🦊
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-tight text-white">Foxden</h1>
            <span className="text-[10px] font-semibold uppercase tracking-wider bg-fox-500/20 text-fox-400 border border-fox-500/30 px-1.5 py-0.5 rounded">
              Manager
            </span>
          </div>
          <p className="text-xs text-slate-400">Panel Autónomo de Minecraft</p>
        </div>
      </div>

      {/* Metrics Center */}
      <div className="flex items-center gap-3 flex-wrap">
        {/* Status Chip */}
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-bold tracking-wider ${badge.bg}`}>
          <span className={`w-2 h-2 rounded-full ${badge.dot}`} />
          {badge.text}
        </div>

        {/* CPU */}
        <div className="flex items-center gap-2 bg-dark-750 border border-dark-700 px-3 py-1 rounded-lg text-xs">
          <Cpu className="w-3.5 h-3.5 text-blue-400" />
          <span className="text-slate-400 font-medium">CPU</span>
          <span className="font-mono font-semibold text-slate-200">{status ? `${status.cpu_percent}%` : '0%'}</span>
        </div>

        {/* RAM */}
        <div className="flex items-center gap-2 bg-dark-750 border border-dark-700 px-3 py-1 rounded-lg text-xs">
          <HardDrive className="w-3.5 h-3.5 text-amber-400" />
          <span className="text-slate-400 font-medium">RAM</span>
          <span className="font-mono font-semibold text-slate-200">{status ? `${status.memory_mb} MB` : '0 MB'}</span>
        </div>

        {/* UPTIME */}
        <div className="flex items-center gap-2 bg-dark-750 border border-dark-700 px-3 py-1 rounded-lg text-xs">
          <Clock className="w-3.5 h-3.5 text-emerald-400" />
          <span className="text-slate-400 font-medium">UPTIME</span>
          <span className="font-mono font-semibold text-slate-200">{status ? formatUptime(status.uptime_seconds) : '0s'}</span>
        </div>

        {/* TUNNEL */}
        <div className="flex items-center gap-2 bg-dark-750 border border-dark-700 px-3 py-1 rounded-lg text-xs">
          <Globe className="w-3.5 h-3.5 text-purple-400" />
          <span className="text-slate-400 font-medium">TÚNEL</span>
          <span
            className={`font-semibold ${
              tunnelRunning ? 'text-emerald-400' : tunnelWaiting ? 'text-amber-400' : 'text-slate-400'
            }`}
          >
            {tunnelRunning ? 'ONLINE' : tunnelWaiting ? 'VINCULAR' : 'OFFLINE'}
          </span>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center gap-2">
        <button
          onClick={onStart}
          disabled={!canStart}
          title={!isInstalled ? 'Primero debes instalar una versión de Minecraft' : ''}
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
          disabled={!canRestart}
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg font-semibold text-sm transition-all bg-dark-700 hover:bg-dark-750 active:scale-95 text-amber-400 border border-dark-700 hover:border-amber-500/30 disabled:opacity-30 disabled:cursor-not-allowed disabled:active:scale-100"
        >
          <RotateCw className={`w-4 h-4 ${actionLoading === 'restart' ? 'animate-spin' : ''}`} />
          <span>Reiniciar</span>
        </button>

        <button
          onClick={onStop}
          disabled={!canStop}
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
