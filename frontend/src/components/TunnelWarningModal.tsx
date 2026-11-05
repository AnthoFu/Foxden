import React from 'react';
import { Globe, AlertTriangle, Play, X, ShieldAlert } from 'lucide-react';

interface TunnelWarningModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirmServerOnly: () => void;
  onConfirmBoth: () => void;
  loading: boolean;
}

export const TunnelWarningModal: React.FC<TunnelWarningModalProps> = ({
  isOpen,
  onClose,
  onConfirmServerOnly,
  onConfirmBoth,
  loading,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fadeIn">
      <div className="bg-dark-800 border border-dark-700 max-w-lg w-full rounded-2xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="px-6 pt-6 pb-4 flex items-start justify-between gap-4 border-b border-dark-700/60">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-500/15 border border-amber-500/30 flex items-center justify-center text-amber-400">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-white">¿Iniciar sin conexión pública?</h3>
              </div>
              <span className="text-[11px] font-semibold tracking-wider uppercase text-amber-400 bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded-full inline-block mt-1">
                Túnel Playit.gg Desactivado
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={loading}
            className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-dark-700 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-4">
          <div className="bg-dark-750/70 border border-dark-700 rounded-xl p-4 text-xs text-slate-300 leading-relaxed space-y-2">
            <p className="flex items-start gap-2 text-slate-200 font-medium">
              <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              <span>
                Si estás jugando en <strong>GitHub Codespaces</strong> o en la nube, <strong>nadie podrá entrar a tu servidor</strong> a menos que el túnel de Playit esté encendido.
              </span>
            </p>
            <p className="text-slate-400 text-[11px] pl-6">
              El túnel genera una dirección IP pública y segura para que vos y tus amigos puedan conectarse desde Minecraft sin abrir puertos en el router.
            </p>
          </div>

          <p className="text-xs text-slate-400">
            ¿Cómo preferís iniciar el servidor?
          </p>

          {/* Action buttons */}
          <div className="space-y-2.5 pt-1">
            <button
              onClick={onConfirmBoth}
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 active:scale-[0.98] text-white font-semibold text-xs shadow-lg transition-all group"
            >
              <Globe className="w-4 h-4 text-emerald-200 group-hover:scale-110 transition-transform" />
              <span>Iniciar Servidor y Túnel (Recomendado para jugar con amigos)</span>
            </button>

            <button
              onClick={onConfirmServerOnly}
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-dark-700 hover:bg-dark-650 active:scale-[0.98] text-slate-300 hover:text-white font-semibold text-xs border border-dark-600 transition-all"
            >
              <Play className="w-3.5 h-3.5 text-slate-400" />
              <span>Iniciar solo Servidor (Uso Local / Sin amigos)</span>
            </button>

            <button
              onClick={onClose}
              disabled={loading}
              className="w-full text-center py-2 text-xs font-semibold text-slate-400 hover:text-slate-200 transition-colors"
            >
              Cancelar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
