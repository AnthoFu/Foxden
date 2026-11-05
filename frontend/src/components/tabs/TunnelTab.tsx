import React, { useState, useEffect } from 'react';
import { Globe, Copy, Check, ExternalLink, Play, Square, Terminal, ShieldCheck } from 'lucide-react';
import { api } from '../../services/api';
import { ServerStatus } from '../../types';

interface TunnelTabProps {
  status: ServerStatus | null;
  onRefresh: () => void;
}

export const TunnelTab: React.FC<TunnelTabProps> = ({ status, onRefresh }) => {
  const [loadingAction, setLoadingAction] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);
  const [customAlias, setCustomAlias] = useState<string>('');
  const [savingAlias, setSavingAlias] = useState<boolean>(false);

  const tunnel = status?.tunnel;
  const tunnelState = tunnel?.state || 'STOPPED';
  const isRunning = tunnelState === 'RUNNING';
  const isWaitingClaim = tunnelState === 'WAITING_CLAIM';

  useEffect(() => {
    const saved = localStorage.getItem('foxden_playit_alias') || '';
    setCustomAlias(saved);
  }, []);

  const handleStartTunnel = async () => {
    setLoadingAction(true);
    try {
      await api.startTunnel();
      onRefresh();
    } catch (err: any) {
      alert(`Error al iniciar túnel: ${err.message}`);
    } finally {
      setLoadingAction(false);
    }
  };

  const handleStopTunnel = async () => {
    setLoadingAction(true);
    try {
      await api.stopTunnel();
      onRefresh();
    } catch (err: any) {
      alert(`Error al detener túnel: ${err.message}`);
    } finally {
      setLoadingAction(false);
    }
  };

  const displayAddress = tunnel?.public_address || customAlias;

  const handleCopy = () => {
    if (!displayAddress) return;
    navigator.clipboard.writeText(displayAddress);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const handleSaveAlias = () => {
    setSavingAlias(true);
    localStorage.setItem('foxden_playit_alias', customAlias.trim());
    setTimeout(() => setSavingAlias(false), 1500);
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-12">
      {/* Tunnel Status Card */}
      <div className="bg-dark-800 border border-dark-700 rounded-xl p-6 shadow-md">
        <div className="border-b border-dark-700 pb-4 mb-6 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Globe className="w-5 h-5 text-purple-400" />
              Conexión Pública (Túnel Playit.gg)
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Permite que tus amigos se conecten a tu servidor desde cualquier parte del mundo sin abrir puertos en tu router.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleStartTunnel}
              disabled={isRunning || loadingAction}
              className="flex items-center gap-1.5 px-4 py-2 bg-purple-600 hover:bg-purple-500 disabled:opacity-30 text-white rounded-lg text-xs font-semibold shadow transition-all active:scale-95"
            >
              <Play className="w-3.5 h-3.5 fill-white" />
              <span>Iniciar Túnel</span>
            </button>

            <button
              onClick={handleStopTunnel}
              disabled={!isRunning || loadingAction}
              className="flex items-center gap-1.5 px-3 py-2 bg-dark-700 hover:bg-dark-750 disabled:opacity-30 text-slate-300 rounded-lg text-xs font-semibold border border-dark-700 transition-all active:scale-95"
            >
              <Square className="w-3.5 h-3.5 fill-slate-300" />
              <span>Detener Túnel</span>
            </button>
          </div>
        </div>

        {/* State Banner */}
        <div
          className={`p-4 rounded-xl border flex items-center justify-between gap-4 mb-6 ${
            isRunning
              ? 'bg-emerald-500/10 border-emerald-500/30'
              : isWaitingClaim
              ? 'bg-amber-500/10 border-amber-500/30'
              : 'bg-dark-750 border-dark-700'
          }`}
        >
          <div className="flex items-center gap-3">
            <span
              className={`w-3 h-3 rounded-full ${
                isRunning
                  ? 'bg-emerald-400 animate-pulse'
                  : isWaitingClaim
                  ? 'bg-amber-400 animate-ping'
                  : 'bg-slate-500'
              }`}
            />
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-slate-300">Estado del Agente</span>
              <h4
                className={`text-sm font-bold ${
                  isRunning ? 'text-emerald-400' : isWaitingClaim ? 'text-amber-400' : 'text-slate-400'
                }`}
              >
                {isRunning
                  ? '🟢 Túnel Conectado y Transmitiendo'
                  : isWaitingClaim
                  ? '🟡 Esperando Vinculación en Playit.gg'
                  : '⚪ Túnel Detenido'}
              </h4>
            </div>
          </div>

          <div className="flex items-center gap-1.5 text-xs text-slate-400 font-medium">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Encriptación TCP</span>
          </div>
        </div>

        {/* Waiting Claim Prompt */}
        {isWaitingClaim && tunnel?.claim_url && (
          <div className="bg-amber-500/15 border border-amber-500/40 rounded-xl p-5 mb-6 text-center space-y-3 animate-fadeIn">
            <h4 className="font-bold text-amber-300 text-sm">Vinculación de Cuenta Requerida (Solo la primera vez)</h4>
            <p className="text-xs text-slate-300 max-w-xl mx-auto">
              Haz clic en el botón a continuación para abrir playit.gg en una nueva pestaña y vincular este túnel con tu cuenta gratuita.
            </p>
            <a
              href={tunnel.claim_url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-dark-950 font-bold text-xs shadow-lg transition-transform hover:scale-105 active:scale-95"
            >
              <span>Vincular en Playit.gg</span>
              <ExternalLink className="w-4 h-4" />
            </a>
          </div>
        )}

        {/* Address Card */}
        {isRunning && (
          <div className="bg-dark-750 border border-emerald-500/30 rounded-xl p-5 space-y-3">
            <div className="flex items-center justify-between text-xs font-bold text-emerald-400 tracking-wider">
              <span>DIRECCIÓN PÚBLICA DE CONEXIÓN</span>
              <a
                href="https://playit.gg/manage/tunnels"
                target="_blank"
                rel="noreferrer"
                className="text-xs font-medium text-slate-400 hover:text-white flex items-center gap-1"
              >
                <span>Administrar en playit.gg</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>

            {displayAddress ? (
              <div className="flex items-center gap-2 bg-dark-900 border border-dark-700 rounded-lg p-2">
                <span className="flex-1 font-mono text-base font-bold text-sky-400 px-3 truncate select-all">
                  {displayAddress}
                </span>
                <button
                  type="button"
                  onClick={handleCopy}
                  className="flex items-center gap-1.5 px-3 py-2 bg-emerald-600 hover:bg-emerald-500 active:scale-95 text-white rounded-lg text-xs font-semibold shadow transition-all"
                >
                  {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copied ? '¡Copiado!' : 'Copiar'}</span>
                </button>
              </div>
            ) : (
              <div className="p-4 bg-dark-900/60 rounded-lg border border-dark-700 text-center space-y-2">
                <p className="text-xs text-slate-300">
                  El túnel está activo. Puedes consultar tu dirección pública en el panel de playit.gg:
                </p>
                <a
                  href="https://playit.gg/manage/tunnels"
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1.5 text-xs text-purple-400 hover:text-purple-300 font-semibold"
                >
                  <span>Abrir Tunnels en Playit.gg</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </div>
            )}
            <p className="text-[11px] text-slate-400">
              👉 Comparte esta dirección con tus amigos para que se conecten desde: <strong>Minecraft &gt; Multijugador &gt; Conexión Directa</strong>.
            </p>
          </div>
        )}

        {/* Custom Alias Config */}
        <div className="mt-6 pt-5 border-t border-dark-700">
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
            Guardar Alias o Dominio de Playit (Opcional)
          </label>
          <p className="text-xs text-slate-400 mb-2">
            Pega aquí la dirección fija que configuraste en Playit para tenerla siempre visible en este panel:
          </p>
          <div className="flex gap-2">
            <input
              type="text"
              value={customAlias}
              onChange={(e) => setCustomAlias(e.target.value)}
              placeholder="ejemplo: mi-servidor.gl.joinmc.link"
              className="flex-1 bg-dark-900 border border-dark-700 rounded-lg px-3.5 py-2 text-xs text-slate-100 font-mono focus:outline-none focus:border-fox-500"
            />
            <button
              type="button"
              onClick={handleSaveAlias}
              className="px-4 py-2 bg-dark-700 hover:bg-dark-750 text-slate-200 rounded-lg text-xs font-semibold border border-dark-700"
            >
              {savingAlias ? '✓ Guardado' : 'Guardar'}
            </button>
          </div>
        </div>

        {/* Background Logs */}
        {tunnel?.logs && tunnel.logs.length > 0 && (
          <details className="mt-5 border border-dark-700 rounded-lg bg-dark-900/40 text-xs">
            <summary className="p-3 font-semibold text-slate-400 hover:text-slate-200 cursor-pointer flex items-center gap-2 select-none">
              <Terminal className="w-4 h-4 text-purple-400" />
              <span>Ver registros del agente Playit</span>
            </summary>
            <div className="p-4 border-t border-dark-700 font-mono text-[11px] text-slate-400 max-h-48 overflow-y-auto space-y-1 bg-dark-950">
              {tunnel.logs.map((log, i) => (
                <div key={i}>{log}</div>
              ))}
            </div>
          </details>
        )}
      </div>
    </div>
  );
};
