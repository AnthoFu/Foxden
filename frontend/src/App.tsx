import React, { useState } from 'react';
import { Terminal, Sliders, Package, Globe } from 'lucide-react';
import { Header } from './components/Header';
import { AlertBanner } from './components/AlertBanner';
import { ConsoleTab } from './components/tabs/ConsoleTab';
import { ConfigTab } from './components/tabs/ConfigTab';
import { VersionsTab } from './components/tabs/VersionsTab';
import { TunnelTab } from './components/tabs/TunnelTab';
import { useServerStatus } from './hooks/useServerStatus';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'console' | 'config' | 'versions' | 'tunnel'>('console');
  const { status, loading, actionLoading, error, clearError, refreshStatus, startServer, stopServer, restartServer } =
    useServerStatus();

  const isInstalled = status?.is_installed ?? false;

  const tabs = [
    { id: 'console', label: 'Consola en Vivo', icon: Terminal },
    { id: 'config', label: 'Configuración', icon: Sliders },
    { id: 'versions', label: 'Versiones e Instalador', icon: Package },
    { id: 'tunnel', label: 'Conexión Pública (Playit)', icon: Globe },
  ] as const;

  return (
    <div className="flex flex-col min-h-screen bg-dark-900 text-slate-100">
      {/* Top Header */}
      <Header
        status={status}
        loading={loading}
        actionLoading={actionLoading}
        onStart={startServer}
        onStop={stopServer}
        onRestart={restartServer}
      />

      {/* Main Container */}
      <div className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-4 flex flex-col">
        {/* Error notification banner if any */}
        {error && (
          <div className="bg-rose-500/15 border border-rose-500/30 text-rose-300 rounded-xl p-3.5 mb-4 text-xs font-semibold flex items-center justify-between">
            <span>⚠️ {error}</span>
            <button onClick={clearError} className="text-slate-400 hover:text-white underline ml-4">
              Cerrar
            </button>
          </div>
        )}

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1 border-b border-dark-700 mb-5 overflow-x-auto select-none">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2.5 text-xs font-bold transition-all border-b-2 whitespace-nowrap ${
                  isActive
                    ? 'border-fox-500 text-fox-400 bg-fox-500/5'
                    : 'border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-600'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-fox-400' : 'text-slate-400'}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Not Installed Banner Alert */}
        {!isInstalled && activeTab !== 'versions' && (
          <AlertBanner onGoToInstaller={() => setActiveTab('versions')} />
        )}

        {/* Tab Content */}
        <main className="flex-1">
          {activeTab === 'console' && <ConsoleTab />}
          {activeTab === 'config' && <ConfigTab />}
          {activeTab === 'versions' && <VersionsTab status={status} onInstalled={refreshStatus} />}
          {activeTab === 'tunnel' && <TunnelTab status={status} onRefresh={refreshStatus} />}
        </main>
      </div>

      {/* Footer */}
      <footer className="border-t border-dark-800 py-3 text-center text-xs text-slate-500 select-none">
        Foxden 🦊 • Creado con ❤️ por <a href="https://github.com/AnthoFu" target="_blank" rel="noreferrer" className="text-fox-400 hover:underline">AnthoFu</a>
      </footer>
    </div>
  );
};

export default App;
