import React from 'react';
import { Globe, AlertTriangle, ArrowRight, Play, RotateCw } from 'lucide-react';

interface TunnelWarningBannerProps {
  tunnelState?: string;
  onStartTunnel: () => void;
  onGoToTunnelTab: () => void;
  loading: boolean;
}

export const TunnelWarningBanner: React.FC<TunnelWarningBannerProps> = ({
  tunnelState = 'STOPPED',
  onStartTunnel,
  onGoToTunnelTab,
  loading,
}) => {
  const isWaitingClaim = tunnelState === 'WAITING_CLAIM';

  return (
    <div className="bg-gradient-to-r from-amber-500/15 via-fox-500/10 to-transparent border border-amber-500/30 border-l-4 border-l-amber-500 rounded-xl p-3.5 my-3 flex flex-wrap items-center justify-between gap-3 animate-fadeIn">
      <div className="flex items-center gap-3 min-w-[280px]">
        <div className="p-2 rounded-lg bg-amber-500/20 text-amber-400 shrink-0">
          {isWaitingClaim ? <Globe className="w-5 h-5 text-purple-400" /> : <AlertTriangle className="w-5 h-5" />}
        </div>
        <div>
          <h4 className="font-semibold text-amber-300 text-xs sm:text-sm">
            {isWaitingClaim
              ? 'Túnel pendiente de vinculación con tu cuenta Playit.gg'
              : 'Servidor encendido sin conexión pública (Túnel apagado)'}
          </h4>
          <p className="text-[11px] text-slate-400 mt-0.5">
            {isWaitingClaim
              ? 'Para recibir una dirección permanente gratuita y que tus amigos se unan, vinculá tu cuenta.'
              : 'Tus amigos no podrán conectarse desde internet hasta que inicies el túnel.'}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {isWaitingClaim ? (
          <button
            onClick={onGoToTunnelTab}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold transition-all shadow hover:scale-105 active:scale-95 whitespace-nowrap"
          >
            <span>Vincular Cuenta en Playit</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        ) : (
          <>
            <button
              onClick={onStartTunnel}
              disabled={loading}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition-all shadow hover:scale-105 active:scale-95 whitespace-nowrap disabled:opacity-50"
            >
              {loading ? (
                <RotateCw className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Play className="w-3.5 h-3.5 fill-white" />
              )}
              <span>Iniciar Túnel Ahora</span>
            </button>
            <button
              onClick={onGoToTunnelTab}
              className="px-2.5 py-1.5 rounded-lg text-slate-400 hover:text-slate-200 text-xs font-medium hover:bg-dark-700 transition-colors"
            >
              Ver Túnel
            </button>
          </>
        )}
      </div>
    </div>
  );
};
