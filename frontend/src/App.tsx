/**
 * Componente principal de la aplicación Foxden.
 * Controla la verificación de sesión, asistente de primer arranque (setup),
 * navegación por pestañas, modales de advertencia y consumo de estado del servidor.
 */

import React, { useState, useEffect } from 'react';
import { Terminal, Sliders, Package, Globe, Puzzle, Loader2 } from 'lucide-react';
import { Header } from './components/Header';
import { AlertBanner } from './components/AlertBanner';
import { TunnelWarningModal } from './components/TunnelWarningModal';
import { TunnelWarningBanner } from './components/TunnelWarningBanner';
import { AuthView } from './components/AuthView';
import { ConsoleTab } from './components/tabs/ConsoleTab';
import { ConfigTab } from './components/tabs/ConfigTab';
import { VersionsTab } from './components/tabs/VersionsTab';
import { ModsTab } from './components/tabs/ModsTab';
import { TunnelTab } from './components/tabs/TunnelTab';
import { useEstadoServidor } from './hooks/useServerStatus';
import { api } from './services/api';

interface DashboardProps {
  currentUser: string | null;
  onLogout: () => void;
}

const DashboardApp: React.FC<DashboardProps> = ({ currentUser, onLogout }) => {
  const [pestanaActiva, setPestanaActiva] = useState<'console' | 'config' | 'versions' | 'mods' | 'tunnel'>('console');
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
    { id: 'mods', label: 'Gestor de Mods', icon: Puzzle },
    { id: 'tunnel', label: 'Conexión Pública (Playit)', icon: Globe },
  ] as const;

  return (
    <div className="flex flex-col min-h-screen bg-dark-900 text-slate-100">
      {/* Encabezado Superior */}
      <Header
        status={status}
        loading={loading}
        actionLoading={actionLoading}
        currentUser={currentUser}
        onStart={manejarClicIniciar}
        onStop={detenerServidor}
        onRestart={reiniciarServidor}
        onLogout={onLogout}
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
          {pestanaActiva === 'mods' && <ModsTab status={status} onNavigateToInstaller={() => setPestanaActiva('versions')} />}
          {pestanaActiva === 'tunnel' && <TunnelTab status={status} onRefresh={actualizarEstado} />}
        </main>
      </div>

      {/* Pie de Página */}
      <footer className="border-t border-dark-800 py-3 text-center text-xs text-slate-500 select-none">
        Foxden v{status?.app_version || '1.0.4'} • Creado con ❤️ por <a href="https://github.com/AnthoFu" target="_blank" rel="noreferrer" className="text-fox-400 hover:underline">AnthoFu</a>
      </footer>
    </div>
  );
};

export const App: React.FC = () => {
  const [authState, setAuthState] = useState<{
    loading: boolean;
    setupRequired: boolean;
    authenticated: boolean;
    username: string | null;
  }>({
    loading: true,
    setupRequired: false,
    authenticated: false,
    username: null,
  });

  const verificarAutenticacion = async () => {
    try {
      const res = await api.obtenerEstadoAuth();
      setAuthState({
        loading: false,
        setupRequired: res.setup_required,
        authenticated: res.authenticated,
        username: res.username,
      });
    } catch (err) {
      console.error('Error verificando autenticación de Foxden:', err);
      setAuthState({
        loading: false,
        setupRequired: false,
        authenticated: false,
        username: null,
      });
    }
  };

  useEffect(() => {
    verificarAutenticacion();

    const alRecibirNoAutorizado = () => {
      setAuthState((prev) => ({
        ...prev,
        authenticated: false,
        username: null,
      }));
    };

    window.addEventListener('foxden:unauthorized', alRecibirNoAutorizado);
    return () => window.removeEventListener('foxden:unauthorized', alRecibirNoAutorizado);
  }, []);

  const manejarExitoAuth = (username: string) => {
    setAuthState({
      loading: false,
      setupRequired: false,
      authenticated: true,
      username,
    });
  };

  const manejarCierreSesion = async () => {
    try {
      await api.cerrarSesion();
    } catch {
      // Ignorar error de red al cerrar sesión
    }
    setAuthState({
      loading: false,
      setupRequired: false,
      authenticated: false,
      username: null,
    });
  };

  // Pantalla de carga mientras se verifica la sesión
  if (authState.loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-dark-900 text-slate-100 select-none">
        <div className="w-12 h-12 rounded-2xl bg-fox-500/10 border border-fox-500/20 p-2 flex items-center justify-center mb-4">
          <Loader2 className="w-6 h-6 text-fox-400 animate-spin" />
        </div>
        <p className="text-xs text-slate-400 font-medium tracking-wide">Iniciando Foxden...</p>
      </div>
    );
  }

  // Si no está autenticado o se requiere configuración inicial
  if (!authState.authenticated) {
    return (
      <AuthView
        setupRequired={authState.setupRequired}
        onAuthSuccess={manejarExitoAuth}
      />
    );
  }

  // Dashboard principal autenticado
  return (
    <DashboardApp
      currentUser={authState.username}
      onLogout={manejarCierreSesion}
    />
  );
};

export default App;
