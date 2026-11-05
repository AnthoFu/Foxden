import React from 'react';
import { AlertTriangle, ArrowRight } from 'lucide-react';

interface AlertBannerProps {
  onGoToInstaller: () => void;
}

export const AlertBanner: React.FC<AlertBannerProps> = ({ onGoToInstaller }) => {
  return (
    <div className="bg-gradient-to-r from-amber-500/15 to-amber-500/5 border border-amber-500/30 border-l-4 border-l-amber-500 rounded-xl p-4 my-4 flex items-center justify-between gap-4 animate-fadeIn">
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-amber-500/20 text-amber-400">
          <AlertTriangle className="w-5 h-5" />
        </div>
        <div>
          <h4 className="font-semibold text-amber-300 text-sm">Aún no has instalado un motor de Minecraft</h4>
          <p className="text-xs text-slate-400 mt-0.5">
            Debes descargar e instalar al menos una versión oficial (Vanilla, NeoForge, Forge o Fabric) antes de poder iniciar el servidor.
          </p>
        </div>
      </div>

      <button
        onClick={onGoToInstaller}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 text-xs font-semibold transition-all hover:scale-105 active:scale-95 whitespace-nowrap"
      >
        <span>Ir a Versiones e Instalador</span>
        <ArrowRight className="w-3.5 h-3.5" />
      </button>
    </div>
  );
};
