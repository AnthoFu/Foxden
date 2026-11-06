/**
 * Componente principal de la aplicación Foxden.
 * Controla la navegación por pestañas, modales de advertencia y consumo de estado del servidor.
 */

import React, { useState } from 'react';
import { Terminal, Sliders, Package, Globe } from 'lucide-react';
import { Header } from './components/Header';
import { AlertBanner } from './components/AlertBanner';
import { TunnelWarningModal } from './components/TunnelWarningModal';
import { TunnelWarningBanner } from './components/TunnelWarningBanner';
import { ConsoleTab } from './components/tabs/ConsoleTab';
import { ConfigTab } from './components/tabs/ConfigTab';
import { VersionsTab } from './components/tabs/VersionsTab';
import { TunnelTab } from './components/tabs/TunnelTab';
import { useEstadoServidor } from './hooks/useServerStatus';

export const App: React.FC = () => {
  const [pestanaActiva, setPestanaActiva] = useState<'console' | 'config' | 'versions' | 'tunnel'>('console');
  const [mostrarModalTunel, setMostrarModalTunel] = useState<boolean>(false);

  const {
    status,
    loading,
    actionLoading,
    error,
    limpiarError,
    actualizarEstado,
    iniciarServidor,
    detenerServidor,
    reiniciarServidor,
    iniciarTunel,
    iniciarServidoryTunel,
  } = useEstadoServidor();

  const estaInstalado = status?.is_installed ?? false;

  const manejarClicIniciar = () => {
    // Si el túnel no está en línea, solicitar confirmación con el modal preventivo
    if (status?.tunnel?.state !== 'RUNNING') {
      setMostrarModalTunel(true);
    } else {
      iniciarServidor();
    }
  };

  const pestanas = [
    { id: 'console', label: 'Consola en Vivo', icon: Terminal },
    { id: 'config', label: 'Configuración', icon: Sliders },
    { id: 'versions', label: 'Versiones e Instalador', icon: Package },
    { id: 'tunnel', label: 'Conexión Pública (Playit)', icon: Globe },
  ] as const;

  return (
    <div className="flex flex-col min-h-screen bg-dark-900 text-slate-100">
      {/* Encabezado Superior */}
      <Header
        status={status}
        loading={loading}
        actionLoading={actionLoading}
        onStart={manejarClicIniciar}
        onStop={detenerServidor}
        onRestart={reiniciarServidor}
      />

      {/* Modal de Advertencia de Túnel */}
      <TunnelWarningModal
        isOpen={mostrarModalTunel}
        onClose={() => setMostrarModalTunel(false)}
        onConfirmServerOnly={() => {
          setMostrarModalTunel(false);
          iniciarServidor();
        }}
        onConfirmBoth={async () => {
          setMostrarModalTunel(false);
          await iniciarServidoryTunel();
        }}
        loading={actionLoading !== null}
      />

      {/* Contenedor Principal */}
      <div className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-4 flex flex-col">
        {/* Banner de notificación de error si existiera */}
        {error && (
          <div className="bg-rose-500/15 border border-rose-500/30 text-rose-300 rounded-xl p-3.5 mb-4 text-xs font-semibold flex items-center justify-between">
            <span>⚠️ {error}</span>
            <button onClick={limpiarError} className="text-slate-400 hover:text-white underline ml-4">
              Cerrar
            </button>
          </div>
        )}

        {/* Pestañas de Navegación */}
        <nav className="flex items-center gap-1 border-b border-dark-700 mb-5 overflow-x-auto select-none">
          {pestanas.map((pestana) => {
            const Icono = pestana.icon;
            const estaActiva = pestanaActiva === pestana.id;
            return (
              <button
                key={pestana.id}
                onClick={() => setPestanaActiva(pestana.id)}
                className={`flex items-center gap-2 px-4 py-2.5 text-xs font-bold transition-all border-b-2 whitespace-nowrap ${
                  estaActiva
                    ? 'border-fox-500 text-fox-400 bg-fox-500/5'
                    : 'border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-600'
                }`}
              >
                <Icono className={`w-4 h-4 ${estaActiva ? 'text-fox-400' : 'text-slate-400'}`} />
                <span>{pestana.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Aviso de Motor No Instalado */}
        {!estaInstalado && pestanaActiva !== 'versions' && (
          <AlertBanner onGoToInstaller={() => setPestanaActiva('versions')} />
        )}

        {/* Banner de Servidor en Ejecución Sin Túnel Activo */}
        {(status?.state === 'RUNNING' || status?.state === 'STARTING') &&
          status?.tunnel?.state !== 'RUNNING' &&
          pestanaActiva !== 'tunnel' && (
            <TunnelWarningBanner
              tunnelState={status?.tunnel?.state}
              onStartTunnel={iniciarTunel}
              onGoToTunnelTab={() => setPestanaActiva('tunnel')}
              loading={actionLoading === 'tunnel'}
            />
        )}

        {/* Contenido de la Pestaña Activa */}
        <main className="flex-1">
          {pestanaActiva === 'console' && <ConsoleTab />}
          {pestanaActiva === 'config' && <ConfigTab />}
          {pestanaActiva === 'versions' && <VersionsTab status={status} onInstalled={actualizarEstado} />}
          {pestanaActiva === 'tunnel' && <TunnelTab status={status} onRefresh={actualizarEstado} />}
        </main>
      </div>

      {/* Pie de Página */}
      <footer className="border-t border-dark-800 py-3 text-center text-xs text-slate-500 select-none">
        Foxden 🦊 • Creado con ❤️ por <a href="https://github.com/AnthoFu" target="_blank" rel="noreferrer" className="text-fox-400 hover:underline">AnthoFu</a>
      </footer>
    </div>
  );
};

export default App;
