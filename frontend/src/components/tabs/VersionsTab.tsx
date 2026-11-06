import React, { useState, useEffect } from 'react';
import { Download, Package, RotateCw, CheckCircle, AlertCircle, ChevronDown, Check } from 'lucide-react';
import { api } from '../../services/api';
import { ServerStatus } from '../../types';

interface VersionsTabProps {
  status: ServerStatus | null;
  onInstalled: () => void;
}

export const VersionsTab: React.FC<VersionsTabProps> = ({ status, onInstalled }) => {
  const motorDetectado = status?.installed_engine || (status?.software_info?.type !== 'none' ? status?.software_info?.type : 'vanilla') || 'vanilla';
  const [serverType, setServerType] = useState<string>(motorDetectado);
  const [versions, setVersions] = useState<string[]>([]);
  const [selectedVersion, setSelectedVersion] = useState<string>('');
  const [includeSnapshots, setIncludeSnapshots] = useState<boolean>(false);
  const [loadingVersions, setLoadingVersions] = useState<boolean>(false);
  const [downloading, setDownloading] = useState<boolean>(false);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; msg: string } | null>(null);

  // Sincronizar serverType inicial con el motor instalado
  useEffect(() => {
    if (status?.installed_engine) {
      setServerType(status.installed_engine);
    } else if (status?.software_info?.type && status.software_info.type !== 'none') {
      setServerType(status.software_info.type);
    }
  }, [status?.installed_engine, status?.software_info?.type]);

  // Manual jars
  const [installedJars, setInstalledJars] = useState<string[]>([]);
  const [manualJar, setManualJar] = useState<string>('');
  const [settingJar, setSettingJar] = useState<boolean>(false);

  // Cargar versiones cada vez que cambie serverType o includeSnapshots
  useEffect(() => {
    async function cargarCatalogo() {
      setLoadingVersions(true);
      try {
        const res = await api.obtenerVersiones(serverType, includeSnapshots);
        setVersions(res.versions || []);
        if (res.versions && res.versions.length > 0) {
          setSelectedVersion(res.versions[0]);
        }
      } catch (err) {
        console.error('Error al cargar catálogo de versiones:', err);
      } finally {
        setLoadingVersions(false);
      }
    }
    cargarCatalogo();
  }, [serverType, includeSnapshots]);

  // Cargar ejecutables instalados
  useEffect(() => {
    async function cargarJars() {
      try {
        const res = await api.obtenerJarsInstalados();
        setInstalledJars(res.jars || []);
        if (status?.target_jar) {
          setManualJar(status.target_jar);
        }
      } catch (err) {
        console.error('Error al cargar lista de JARs:', err);
      }
    }
    cargarJars();
  }, [status?.target_jar]);

  const manejarDescarga = async () => {
    if (!selectedVersion) return;
    setDownloading(true);
    setFeedback(null);

    try {
      const res = await api.descargarVersion(serverType, selectedVersion);
      setFeedback({
        type: 'success',
        msg: `✓ ¡${res.software_info?.name || serverType.toUpperCase()} ${selectedVersion} instalado con éxito y listo para iniciar!`,
      });
      onInstalled();
    } catch (err: any) {
      setFeedback({
        type: 'error',
        msg: `✗ Error en la instalación: ${err.message || 'Fallo de descarga'}`,
      });
    } finally {
      setDownloading(false);
    }
  };

  const manejarEstablecerJarManual = async () => {
    if (!manualJar) return;
    setSettingJar(true);
    try {
      await api.actualizarConfiguracion({ target_jar: manualJar });
      onInstalled();
      alert(`Ejecutable activo establecido en: ${manualJar}`);
    } catch (err: any) {
      alert(`Error al establecer ejecutable: ${err.message}`);
    } finally {
      setSettingJar(false);
    }
  };

  const isInstalled = status?.is_installed ?? false;
  const swInfo = status?.software_info;

  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-12">
      {/* Card 1: Active Software */}
      <div className="bg-dark-800 border border-dark-700 rounded-xl p-6 shadow-md">
        <div className="border-b border-dark-700 pb-4 mb-5">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Package className="w-5 h-5 text-fox-400" />
            Software y Ejecutable Activo
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Foxden detecta y configura automáticamente el archivo óptimo para iniciar tu servidor.
          </p>
        </div>

        <div className="bg-dark-750 border border-dark-700 rounded-xl p-4 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="text-3xl p-2 bg-dark-800 border border-dark-700 rounded-lg shadow-inner">
              {swInfo?.icon || '🎮'}
            </div>
            <div>
              <h3 className="text-base font-bold text-white">{swInfo?.name || 'Cargando software...'}</h3>
              <p className="text-xs text-slate-400 mt-0.5">{swInfo?.description || 'Detectando estado del servidor...'}</p>
            </div>
          </div>

          <span
            className={`px-3 py-1 rounded-full text-xs font-bold tracking-wider border ${
              isInstalled
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
            }`}
          >
            {isInstalled ? 'Listo para Iniciar' : 'Instalación Requerida'}
          </span>
        </div>

        {/* Advanced Accordion for manual jar */}
        <details className="mt-4 group border border-dark-700 rounded-lg bg-dark-900/50 overflow-hidden">
          <summary className="p-3 text-xs font-semibold text-slate-400 hover:text-slate-200 cursor-pointer flex items-center justify-between select-none">
            <span>⚙️ Opciones avanzadas (Selección manual de ejecutables)</span>
            <ChevronDown className="w-4 h-4 transition-transform group-open:rotate-180" />
          </summary>
          <div className="p-4 border-t border-dark-700 bg-dark-850 space-y-3">
            <p className="text-xs text-slate-400">
              Solo selecciona esto si deseas forzar un script <code>run.sh</code> o un <code>.jar</code> experimental específico.
            </p>
            <div className="flex gap-2">
              <select
                value={manualJar}
                onChange={(e) => setManualJar(e.target.value)}
                className="flex-1 bg-dark-900 border border-dark-700 rounded-lg px-3 py-2 text-xs text-slate-100 font-mono"
              >
                {installedJars.length === 0 ? (
                  <option value="">No hay archivos jar instalados</option>
                ) : (
                  installedJars.map((jar) => (
                    <option key={jar} value={jar}>
                      {jar}
                    </option>
                  ))
                )}
              </select>
              <button
                type="button"
                onClick={manejarEstablecerJarManual}
                disabled={settingJar || !manualJar}
                className="px-3 py-2 bg-dark-700 hover:bg-dark-750 text-slate-200 rounded-lg text-xs font-semibold border border-dark-700 disabled:opacity-40"
              >
                {settingJar ? 'Aplicando...' : 'Forzar Selección'}
              </button>
            </div>
          </div>
        </details>
      </div>

      {/* Card 2: Official Minecraft Installer */}
      <div className="bg-dark-800 border border-dark-700 rounded-xl p-6 shadow-md">
        <div className="border-b border-dark-700 pb-4 mb-6">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Download className="w-5 h-5 text-emerald-400" />
            Instalador Oficial de Versiones de Minecraft
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Descarga e instala cualquier versión oficial de Minecraft Java (Mojang Vanilla con todo su catálogo histórico y actual), NeoForge, Forge o Fabric con un solo clic.
          </p>
        </div>

        <div className="space-y-5">
          {/* Engine Selector */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
              Tipo de Motor / Cargador
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {[
                {
                  id: 'neoforge',
                  name: 'NeoForge',
                  icon: '🔥',
                  desc: 'Estándar moderno para mods en Minecraft 1.20.1+ y 1.21+',
                },
                {
                  id: 'vanilla',
                  name: 'Mojang Vanilla',
                  icon: '🍦',
                  desc: 'Minecraft oficial sin modificaciones de ningún tipo',
                },
                {
                  id: 'fabric',
                  name: 'Fabric Loader',
                  icon: '🧵',
                  desc: 'Ideal para optimización (Sodium, Iris) y mods ligeros',
                },
                {
                  id: 'forge',
                  name: 'Minecraft Forge',
                  icon: '🔨',
                  desc: 'Para paquetes de mods tradicionales y versiones legadas',
                },
              ].map((opt) => (
                <button
                  type="button"
                  key={opt.id}
                  onClick={() => setServerType(opt.id)}
                  className={`p-3.5 rounded-xl border text-left transition-all flex items-start gap-3 ${
                    serverType === opt.id
                      ? 'bg-fox-500/10 border-fox-500/50 shadow-md ring-1 ring-fox-500/30'
                      : 'bg-dark-750 border-dark-700 hover:border-slate-600'
                  }`}
                >
                  <span className="text-2xl p-1 bg-dark-800 rounded-lg shadow-inner">{opt.icon}</span>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-sm text-white">{opt.name}</span>
                      {serverType === opt.id && <Check className="w-4 h-4 text-fox-400" />}
                    </div>
                    <p className="text-xs text-slate-400 mt-1 leading-relaxed">{opt.desc}</p>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Version Selector */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
            <div className="sm:col-span-2">
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                Versión de Minecraft
              </label>
              <select
                value={selectedVersion}
                onChange={(e) => setSelectedVersion(e.target.value)}
                disabled={loadingVersions}
                className="w-full bg-dark-900 border border-dark-700 rounded-lg px-3.5 py-2.5 text-sm text-slate-100 font-mono focus:outline-none focus:border-fox-500 transition-colors disabled:opacity-50"
              >
                {loadingVersions ? (
                  <option value="">Consultando catálogo oficial...</option>
                ) : versions.length === 0 ? (
                  <option value="">No se encontraron versiones</option>
                ) : (
                  versions.map((v) => (
                    <option key={v} value={v}>
                      {serverType.toUpperCase()} {v}
                    </option>
                  ))
                )}
              </select>
            </div>

            <div className="flex items-end pb-1.5">
              <label className="flex items-center gap-2 cursor-pointer text-xs text-slate-300 hover:text-white select-none">
                <input
                  type="checkbox"
                  checked={includeSnapshots}
                  onChange={(e) => setIncludeSnapshots(e.target.checked)}
                  className="rounded bg-dark-900 border-dark-700 text-fox-500 focus:ring-fox-500 w-4 h-4"
                />
                <span>Incluir snapshots / betas</span>
              </label>
            </div>
          </div>

          {/* Download Button & Feedback */}
          <div className="pt-3 flex flex-col sm:flex-row sm:items-center gap-4">
            <button
              type="button"
              onClick={manejarDescarga}
              disabled={downloading || !selectedVersion || loadingVersions}
              className="flex items-center justify-center gap-2 px-6 py-3 rounded-lg bg-emerald-600 hover:bg-emerald-500 active:scale-95 text-white font-bold text-sm shadow-lg transition-all disabled:opacity-40 disabled:active:scale-100"
            >
              {downloading ? (
                <>
                  <RotateCw className="w-4 h-4 animate-spin" />
                  <span>Instalando {selectedVersion}...</span>
                </>
              ) : (
                <>
                  <Download className="w-4 h-4" />
                  <span>Descargar e Instalar {selectedVersion}</span>
                </>
              )}
            </button>

            {downloading && (
              <span className="text-xs text-amber-400 font-medium animate-pulse">
                ⏳ Descargando e instalando dependencias. Esto puede tomar unos momentos...
              </span>
            )}
          </div>

          {feedback && (
            <div
              className={`p-3.5 rounded-lg border text-xs font-semibold flex items-center gap-2 animate-fadeIn ${
                feedback.type === 'success'
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                  : 'bg-rose-500/10 border-rose-500/30 text-rose-400'
              }`}
            >
              {feedback.type === 'success' ? <CheckCircle className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
              <span>{feedback.msg}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
