/**
 * Pestaña de Gestión de Mods y Modpacks para Foxden.
 * - Sub-pestaña "Mis Mods Locales": drag & drop, switch activo/desactivado (.jar <-> .jar.disabled), eliminar.
 * - Sub-pestaña "Explorar Modrinth": buscador facetado contextual por motor y versión de Minecraft,
 *   instalación en 1 clic y resolución automática de dependencias obligatorias.
 */

import React, { useState, useEffect, useRef, useMemo } from 'react';
import {
  UploadCloud,
  Puzzle,
  Trash2,
  Search,
  RotateCw,
  AlertTriangle,
  FolderArchive,
  CheckCircle2,
  X,
  FileCode,
  Info,
  Users,
  Compass,
  Download,
  Check,
  HardDrive,
  SlidersHorizontal,
} from 'lucide-react';
import { api } from '../../services/api';
import { ModItem, ModrinthHit, ServerStatus } from '../../types';

interface ModsTabProps {
  status: ServerStatus | null;
  onNavigateToInstaller?: () => void;
}

function formatearNumero(num: number): string {
  if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(1)}M`;
  if (num >= 1_000) return `${(num / 1_000).toFixed(1)}K`;
  return num.toString();
}

export const ModsTab: React.FC<ModsTabProps> = ({ status, onNavigateToInstaller }) => {
  const [subpestana, setSubpestana] = useState<'locales' | 'modrinth'>('locales');

  // Estado de mods locales
  const [mods, setMods] = useState<ModItem[]>([]);
  const [cargando, setCargando] = useState<boolean>(true);
  const [subiendo, setSubiendo] = useState<boolean>(false);
  const [busqueda, setBusqueda] = useState<string>('');
  const [filtroEstado, setFiltroEstado] = useState<'todos' | 'activos' | 'desactivados'>('todos');
  const [arrastrando, setArrastrando] = useState<boolean>(false);
  const [modAEliminar, setModAEliminar] = useState<string | null>(null);
  const [accionEnCurso, setAccionEnCurso] = useState<string | null>(null);
  const [notificacion, setNotificacion] = useState<{ tipo: 'exito' | 'error'; mensaje: string } | null>(null);

  // Estado de Modrinth
  const [modrinthQuery, setModrinthQuery] = useState<string>('');
  const [modrinthResultados, setModrinthResultados] = useState<ModrinthHit[]>([]);
  const [modrinthTotal, setModrinthTotal] = useState<number>(0);
  const [modrinthCargando, setModrinthCargando] = useState<boolean>(false);
  const [modrinthSort, setModrinthSort] = useState<string>('relevance');
  const [filtrarCompatibilidad, setFiltrarCompatibilidad] = useState<boolean>(true);
  const [instalandoModId, setInstalandoModId] = useState<string | null>(null);

  const inputArchivoRef = useRef<HTMLInputElement | null>(null);

  const motorActual = (
    status?.installed_engine ||
    (status?.software_info?.type !== 'none' ? status?.software_info?.type : 'vanilla') ||
    'vanilla'
  ).toLowerCase();

  const versionActual = status?.installed_version || '';
  const esMotorVanilla = motorActual === 'vanilla';

  const cargarMods = async () => {
    setCargando(true);
    try {
      const res = await api.obtenerMods();
      setMods(res.mods || []);
    } catch (err: any) {
      setNotificacion({
        tipo: 'error',
        mensaje: err.message || 'Error al cargar la lista de mods locales.',
      });
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargarMods();
  }, []);

  const limpiarNotificacion = () => setNotificacion(null);

  // Búsqueda en Modrinth
  const buscarEnModrinth = async (consulta?: string, orden?: string, compat?: boolean) => {
    setModrinthCargando(true);
    limpiarNotificacion();
    const q = consulta !== undefined ? consulta : modrinthQuery;
    const s = orden !== undefined ? orden : modrinthSort;
    const c = compat !== undefined ? compat : filtrarCompatibilidad;

    try {
      const loaderParam = c && !esMotorVanilla ? motorActual : undefined;
      const versionParam = c && versionActual ? versionActual : undefined;
      const res = await api.buscarModrinth(
        q,
        loaderParam,
        versionParam,
        s,
        0,
        24,
        true // Solo mods con soporte de servidor
      );
      setModrinthResultados(res.hits || []);
      setModrinthTotal(res.total_hits || 0);
    } catch (err: any) {
      setNotificacion({
        tipo: 'error',
        mensaje: err.message || 'Error al conectar con la API de Modrinth.',
      });
    } finally {
      setModrinthCargando(false);
    }
  };

  // Cargar catálogo popular al abrir la pestaña de Modrinth por primera vez
  useEffect(() => {
    if (subpestana === 'modrinth' && modrinthResultados.length === 0 && !modrinthCargando) {
      buscarEnModrinth('', 'downloads');
    }
  }, [subpestana]);

  const procesarArchivos = async (archivos: FileList | File[]) => {
    const lista = Array.from(archivos).filter((archivo) => {
      const nombre = archivo.name.toLowerCase();
      return nombre.endsWith('.jar') || nombre.endsWith('.zip');
    });

    if (lista.length === 0) {
      setNotificacion({
        tipo: 'error',
        mensaje: 'Solo se admiten archivos .jar de mods o .zip de modpacks.',
      });
      return;
    }

    setSubiendo(true);
    limpiarNotificacion();
    try {
      const res = await api.subirMods(lista);
      const exitosos = res.uploaded.filter((u: any) => u.status === 'success');
      const fallidos = res.uploaded.filter((u: any) => u.status === 'error');

      if (fallidos.length === 0) {
        setNotificacion({
          tipo: 'exito',
          mensaje: `Se ${exitosos.length === 1 ? 'instaló 1 archivo' : `instalaron ${exitosos.length} archivos`} correctamente.`,
        });
      } else {
        setNotificacion({
          tipo: 'error',
          mensaje: `${exitosos.length} instalados, ${fallidos.length} con error: ${fallidos.map((f: any) => `${f.filename} (${f.error})`).join(', ')}`,
        });
      }
      setMods(res.mods || []);
    } catch (err: any) {
      setNotificacion({
        tipo: 'error',
        mensaje: err.message || 'Error al subir los archivos.',
      });
    } finally {
      setSubiendo(false);
    }
  };

  const manejarDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!arrastrando) setArrastrando(true);
  };

  const manejarDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setArrastrando(false);
  };

  const manejarDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setArrastrando(false);
    if (e.dataTransfer?.files && e.dataTransfer.files.length > 0) {
      procesarArchivos(e.dataTransfer.files);
    }
  };

  const manejarCambioInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      procesarArchivos(e.target.files);
      e.target.value = '';
    }
  };

  const manejarAlternar = async (mod: ModItem) => {
    setAccionEnCurso(mod.filename);
    try {
      const res = await api.alternarMod(mod.filename, !mod.enabled);
      setMods((prev) =>
        prev.map((m) =>
          m.filename === mod.filename
            ? { ...m, ...res.mod, filename: res.mod.filename, enabled: res.mod.enabled }
            : m
        )
      );
    } catch (err: any) {
      setNotificacion({
        tipo: 'error',
        mensaje: err.message || 'Error al cambiar el estado del mod.',
      });
      cargarMods();
    } finally {
      setAccionEnCurso(null);
    }
  };

  const manejarEliminar = async (filename: string) => {
    setAccionEnCurso(filename);
    try {
      await api.eliminarMod(filename);
      setMods((prev) => prev.filter((m) => m.filename !== filename));
      setModAEliminar(null);
      setNotificacion({
        tipo: 'exito',
        mensaje: `Mod ${filename} eliminado con éxito.`,
      });
    } catch (err: any) {
      setNotificacion({
        tipo: 'error',
        mensaje: err.message || 'Error al eliminar el archivo.',
      });
    } finally {
      setAccionEnCurso(null);
    }
  };

  const manejarInstalarModrinth = async (hit: ModrinthHit) => {
    setInstalandoModId(hit.project_id);
    limpiarNotificacion();
    try {
      const res = await api.instalarModModrinth(
        hit.project_id,
        !esMotorVanilla ? motorActual : undefined,
        versionActual || undefined
      );
      if (res.mods) {
        setMods(res.mods);
      } else {
        cargarMods();
      }
      const deps = res.result?.dependencies_installed || [];
      const msgDeps = deps.length > 0 ? ` (y ${deps.length} dependencia${deps.length > 1 ? 's' : ''} requerida${deps.length > 1 ? 's' : ''})` : '';
      setNotificacion({
        tipo: 'exito',
        mensaje: `¡${hit.title} instalado correctamente${msgDeps}!`,
      });
    } catch (err: any) {
      setNotificacion({
        tipo: 'error',
        mensaje: err.message || `No se pudo instalar ${hit.title} desde Modrinth.`,
      });
    } finally {
      setInstalandoModId(null);
    }
  };

  const estaInstaladoLocalmente = (hit: ModrinthHit): boolean => {
    const slug = (hit.slug || '').toLowerCase().replace(/[^a-z0-9]/g, '');
    const title = (hit.title || '').toLowerCase().replace(/[^a-z0-9]/g, '');
    return mods.some((m) => {
      const nom = (m.name || '').toLowerCase().replace(/[^a-z0-9]/g, '');
      const file = (m.filename || '').toLowerCase().replace(/[^a-z0-9]/g, '');
      return (
        (slug && (file.includes(slug) || nom.includes(slug))) ||
        (title && nom.includes(title))
      );
    });
  };

  const modsFiltrados = useMemo(() => {
    return mods.filter((mod) => {
      if (filtroEstado === 'activos' && !mod.enabled) return false;
      if (filtroEstado === 'desactivados' && mod.enabled) return false;
      if (!busqueda.trim()) return true;
      const q = busqueda.toLowerCase();
      return (
        (mod.name || '').toLowerCase().includes(q) ||
        (mod.filename || '').toLowerCase().includes(q) ||
        (mod.description || '').toLowerCase().includes(q) ||
        (mod.loader || '').toLowerCase().includes(q)
      );
    });
  }, [mods, busqueda, filtroEstado]);

  const totalActivos = mods.filter((m) => m.enabled).length;
  const totalDesactivados = mods.length - totalActivos;

  return (
    <div className="space-y-5 animate-in fade-in duration-200">
      {/* Sub-navegación: Locales vs Modrinth */}
      <div className="flex items-center justify-between border-b border-dark-700 pb-3">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setSubpestana('locales')}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold transition-all ${
              subpestana === 'locales'
                ? 'bg-fox-500 text-white shadow-sm'
                : 'bg-dark-800 text-slate-400 hover:text-white border border-dark-700'
            }`}
          >
            <HardDrive className="w-4 h-4" />
            <span>Mis Mods Locales</span>
            <span
              className={`px-1.5 py-0.2 rounded-md text-[10px] font-mono ${
                subpestana === 'locales' ? 'bg-black/20 text-white' : 'bg-dark-900 text-slate-400'
              }`}
            >
              {mods.length}
            </span>
          </button>

          <button
            onClick={() => setSubpestana('modrinth')}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold transition-all ${
              subpestana === 'modrinth'
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'bg-dark-800 text-slate-400 hover:text-white border border-dark-700'
            }`}
          >
            <Compass className="w-4 h-4" />
            <span>Explorar en Modrinth</span>
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          </button>
        </div>
      </div>

      {/* Alerta de Compatibilidad si el Motor es Vanilla */}
      {esMotorVanilla && (
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-2xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-amber-200">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" />
            <div className="text-xs">
              <span className="font-bold text-amber-300">Motor Vanilla en uso:</span> Minecraft Vanilla oficial no carga mods. Para jugar con mods, instalá un motor como <strong>Fabric</strong>, <strong>Forge</strong> o <strong>NeoForge</strong>.
            </div>
          </div>
          {onNavigateToInstaller && (
            <button
              onClick={onNavigateToInstaller}
              className="text-xs font-bold px-3 py-1.5 bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/40 rounded-xl transition-all whitespace-nowrap text-amber-200"
            >
              Cambiar de Motor
            </button>
          )}
        </div>
      )}

      {/* Notificación de Éxito / Error */}
      {notificacion && (
        <div
          className={`rounded-2xl p-3.5 text-xs font-semibold flex items-center justify-between border ${
            notificacion.tipo === 'exito'
              ? 'bg-emerald-500/15 border-emerald-500/30 text-emerald-300'
              : 'bg-rose-500/15 border-rose-500/30 text-rose-300'
          }`}
        >
          <div className="flex items-center gap-2">
            {notificacion.tipo === 'exito' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            ) : (
              <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
            )}
            <span>{notificacion.mensaje}</span>
          </div>
          <button onClick={limpiarNotificacion} className="text-slate-400 hover:text-white ml-3">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* ========================================================================= */}
      {/* VISTA 1: MIS MODS LOCALES                                                */}
      {/* ========================================================================= */}
      {subpestana === 'locales' && (
        <div className="space-y-5 animate-in fade-in duration-150">
          {/* Aviso Informativo de Compatibilidad (Mods de Servidor y Clientes) */}
          <div className="bg-sky-500/10 border border-sky-500/25 rounded-2xl p-4 text-xs text-sky-200">
            <div className="flex items-start gap-3">
              <Info className="w-5 h-5 text-sky-400 shrink-0 mt-0.5" />
              <div className="space-y-2 flex-1">
                <h4 className="font-bold text-sky-300 text-xs">
                  Aviso importante sobre compatibilidad de mods:
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-[11px] text-sky-200/90">
                  <div className="flex items-start gap-2 bg-dark-900/60 p-3 rounded-xl border border-sky-500/15">
                    <span className="text-amber-400 font-bold shrink-0 text-sm">⚠️</span>
                    <div>
                      <strong className="text-white block mb-0.5">Solo mods de servidor:</strong>
                      No subas mods exclusivos de cliente (ej. OptiFine, minimapas de cliente o shaders). Si el servidor intenta cargar librerías gráficas de cliente, fallará al iniciar.
                    </div>
                  </div>
                  <div className="flex items-start gap-2 bg-dark-900/60 p-3 rounded-xl border border-sky-500/15">
                    <Users className="w-4 h-4 text-sky-400 shrink-0 mt-0.5" />
                    <div>
                      <strong className="text-white block mb-0.5">Sincronización con jugadores:</strong>
                      Los usuarios que se conecten al servidor deben tener exactamente los mismos mods y versiones instalados en su juego local para poder ingresar.
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Zona de Subida Drag & Drop */}
          <div
            onDragOver={manejarDragOver}
            onDragLeave={manejarDragLeave}
            onDrop={manejarDrop}
            onClick={() => inputArchivoRef.current?.click()}
            className={`relative border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all ${
              arrastrando
                ? 'border-fox-500 bg-fox-500/15 scale-[1.01]'
                : 'border-dark-700 hover:border-fox-500/50 bg-dark-800/40 hover:bg-dark-800/70'
            }`}
          >
            <input
              ref={inputArchivoRef}
              type="file"
              multiple
              accept=".jar,.zip"
              onChange={manejarCambioInput}
              className="hidden"
            />

            <div className="flex flex-col items-center justify-center gap-3">
              <div className="w-14 h-14 rounded-2xl bg-fox-500/10 border border-fox-500/20 flex items-center justify-center text-fox-400">
                {subiendo ? (
                  <RotateCw className="w-7 h-7 animate-spin text-fox-400" />
                ) : (
                  <UploadCloud className="w-7 h-7 text-fox-400" />
                )}
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">
                  {subiendo ? 'Procesando e instalando mods...' : 'Arrastrá archivos .jar o .zip de modpacks aquí'}
                </h3>
                <p className="text-xs text-slate-400 mt-1">
                  O hacé clic para buscar en tu equipo. Los archivos <code className="text-fox-300 font-mono">.zip</code> se descomprimen automáticamente con sus configuraciones.
                </p>
              </div>
              <div className="flex items-center gap-3 text-[11px] text-slate-500 font-mono mt-1">
                <span className="flex items-center gap-1">
                  <FileCode className="w-3.5 h-3.5" /> Mod individual (.jar)
                </span>
                <span>•</span>
                <span className="flex items-center gap-1">
                  <FolderArchive className="w-3.5 h-3.5" /> Modpack (.zip)
                </span>
              </div>
            </div>
          </div>

          {/* Barra de Herramientas: Búsqueda y Filtros */}
          <div className="bg-dark-800/60 border border-dark-700 rounded-2xl p-4 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={busqueda}
                onChange={(e) => setBusqueda(e.target.value)}
                placeholder="Buscar mod local por nombre, archivo o descripción..."
                className="w-full bg-dark-900 border border-dark-700 rounded-xl pl-9 pr-8 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-fox-500 transition-colors"
              />
              {busqueda && (
                <button
                  onClick={() => setBusqueda('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>

            <div className="flex items-center gap-1.5 self-start md:self-auto">
              <button
                onClick={() => setFiltroEstado('todos')}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                  filtroEstado === 'todos'
                    ? 'bg-fox-500 text-white shadow-sm'
                    : 'bg-dark-900 border border-dark-700 text-slate-400 hover:text-white'
                }`}
              >
                Todos ({mods.length})
              </button>
              <button
                onClick={() => setFiltroEstado('activos')}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all flex items-center gap-1.5 ${
                  filtroEstado === 'activos'
                    ? 'bg-emerald-600 text-white shadow-sm'
                    : 'bg-dark-900 border border-dark-700 text-slate-400 hover:text-white'
                }`}
              >
                <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                Activos ({totalActivos})
              </button>
              <button
                onClick={() => setFiltroEstado('desactivados')}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all flex items-center gap-1.5 ${
                  filtroEstado === 'desactivados'
                    ? 'bg-slate-700 text-white shadow-sm'
                    : 'bg-dark-900 border border-dark-700 text-slate-400 hover:text-white'
                }`}
              >
                <span className="w-2 h-2 rounded-full bg-slate-400"></span>
                Desactivados ({totalDesactivados})
              </button>

              <button
                onClick={cargarMods}
                disabled={cargando}
                title="Recargar lista"
                className="p-2 ml-1 bg-dark-900 border border-dark-700 hover:border-slate-600 rounded-xl text-slate-400 hover:text-white transition-colors"
              >
                <RotateCw className={`w-3.5 h-3.5 ${cargando ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>

          {/* Lista de Mods Locales */}
          {cargando && mods.length === 0 ? (
            <div className="p-12 text-center text-slate-500 text-xs">
              <RotateCw className="w-6 h-6 animate-spin mx-auto mb-2 text-fox-400" />
              Cargando mods instalados...
            </div>
          ) : modsFiltrados.length === 0 ? (
            <div className="bg-dark-800/30 border border-dark-700/60 rounded-2xl p-12 text-center">
              <Puzzle className="w-10 h-10 text-slate-600 mx-auto mb-3" />
              <h4 className="text-sm font-bold text-slate-300">
                {mods.length === 0 ? 'No hay mods instalados' : 'No se encontraron mods coincidentes'}
              </h4>
              <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
                {mods.length === 0
                  ? 'Arrastrá tus archivos .jar o explorá el catálogo oficial de Modrinth para instalar mods con un clic.'
                  : 'Probá con otro término de búsqueda o cambiá el filtro de estado.'}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
              {modsFiltrados.map((mod) => {
                const estaProcesando = accionEnCurso === mod.filename;
                const loaderClean = (mod.loader || 'unknown').toLowerCase();
                const esLoaderConocido = ['fabric', 'forge', 'neoforge'].includes(loaderClean);
                const nombreMostrado = mod.name || mod.filename;

                return (
                  <div
                    key={mod.filename}
                    className={`bg-dark-800/80 border rounded-2xl p-4 transition-all flex flex-col justify-between gap-3 ${
                      mod.enabled
                        ? 'border-dark-700 hover:border-dark-600 shadow-sm'
                        : 'border-dark-700/50 bg-dark-800/40 opacity-75'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className="w-10 h-10 rounded-xl bg-dark-900 border border-dark-700 flex items-center justify-center p-1.5 shrink-0">
                        {esLoaderConocido ? (
                          <img
                            src={`/loaders/${loaderClean}.png`}
                            alt={mod.loader}
                            className="w-full h-full object-contain"
                          />
                        ) : (
                          <Puzzle className="w-5 h-5 text-fox-400" />
                        )}
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-bold text-xs text-white truncate max-w-[220px]" title={nombreMostrado}>
                            {nombreMostrado}
                          </span>
                          {mod.version && (
                            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-md bg-dark-900 border border-dark-700 text-slate-300">
                              v{mod.version}
                            </span>
                          )}
                          {esLoaderConocido && (
                            <span className="text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded-md bg-fox-500/10 text-fox-400 border border-fox-500/20">
                              {mod.loader}
                            </span>
                          )}
                        </div>

                        <div className="text-[11px] font-mono text-slate-500 truncate mt-0.5" title={mod.filename}>
                          {mod.filename}
                        </div>

                        {mod.description && (
                          <p className="text-[11px] text-slate-400 line-clamp-2 mt-1.5 leading-relaxed">
                            {mod.description}
                          </p>
                        )}
                      </div>
                    </div>

                    <div className="pt-2 border-t border-dark-700/60 flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2 text-[11px] text-slate-500">
                        <span>{(mod.size_mb ?? 0).toFixed(2)} MB</span>
                        <span>•</span>
                        <span
                          className={`font-semibold ${
                            mod.enabled ? 'text-emerald-400' : 'text-slate-500'
                          }`}
                        >
                          {mod.enabled ? 'Activo' : 'Desactivado'}
                        </span>
                      </div>

                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => manejarAlternar(mod)}
                          disabled={estaProcesando}
                          title={mod.enabled ? 'Desactivar mod' : 'Activar mod'}
                          className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                            mod.enabled ? 'bg-emerald-500' : 'bg-slate-700'
                          }`}
                        >
                          <span
                            className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                              mod.enabled ? 'translate-x-4' : 'translate-x-0'
                            }`}
                          />
                        </button>

                        {modAEliminar === mod.filename ? (
                          <div className="flex items-center gap-1 bg-rose-500/15 border border-rose-500/40 rounded-lg px-2 py-0.5">
                            <span className="text-[10px] font-bold text-rose-300">¿Eliminar?</span>
                            <button
                              onClick={() => manejarEliminar(mod.filename)}
                              disabled={estaProcesando}
                              className="text-[10px] font-bold text-rose-400 hover:text-rose-200 ml-1 underline"
                            >
                              Sí
                            </button>
                            <button
                              onClick={() => setModAEliminar(null)}
                              className="text-[10px] text-slate-400 hover:text-white ml-1"
                            >
                              No
                            </button>
                          </div>
                        ) : (
                          <button
                            onClick={() => setModAEliminar(mod.filename)}
                            disabled={estaProcesando}
                            title="Eliminar archivo del servidor"
                            className="p-1 text-slate-500 hover:text-rose-400 transition-colors rounded-lg hover:bg-dark-900"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* VISTA 2: EXPLORAR EN MODRINTH                                            */}
      {/* ========================================================================= */}
      {subpestana === 'modrinth' && (
        <div className="space-y-5 animate-in fade-in duration-150">
          {/* Barra de Filtros y Configuración Contextual de Modrinth */}
          <div className="bg-dark-800/60 border border-dark-700 rounded-2xl p-4 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
            {/* Campo de Búsqueda */}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                buscarEnModrinth();
              }}
              className="relative flex-1"
            >
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={modrinthQuery}
                onChange={(e) => setModrinthQuery(e.target.value)}
                placeholder="Buscar mods en Modrinth (ej. voice chat, lithium, appleskin)..."
                className="w-full bg-dark-900 border border-dark-700 rounded-xl pl-9 pr-20 py-2.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-colors"
              />
              <button
                type="submit"
                disabled={modrinthCargando}
                className="absolute right-1.5 top-1/2 -translate-y-1/2 px-3 py-1 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white rounded-lg text-xs font-bold transition-all"
              >
                {modrinthCargando ? <RotateCw className="w-3 h-3 animate-spin" /> : 'Buscar'}
              </button>
            </form>

            {/* Opciones de Filtro y Orden */}
            <div className="flex items-center gap-2 flex-wrap">
              {/* Selector de Orden */}
              <div className="flex items-center gap-1.5 bg-dark-900 border border-dark-700 rounded-xl px-2.5 py-1.5 text-xs">
                <SlidersHorizontal className="w-3.5 h-3.5 text-slate-400" />
                <select
                  value={modrinthSort}
                  onChange={(e) => {
                    setModrinthSort(e.target.value);
                    buscarEnModrinth(undefined, e.target.value);
                  }}
                  className="bg-transparent text-slate-200 text-xs focus:outline-none cursor-pointer"
                >
                  <option value="relevance" className="bg-dark-800">Relevancia</option>
                  <option value="downloads" className="bg-dark-800">Más descargados</option>
                  <option value="newest" className="bg-dark-800">Más recientes</option>
                  <option value="updated" className="bg-dark-800">Actualizados</option>
                </select>
              </div>

              {/* Interruptor de Filtro de Compatibilidad */}
              <button
                type="button"
                onClick={() => {
                  const nuevoCompat = !filtrarCompatibilidad;
                  setFiltrarCompatibilidad(nuevoCompat);
                  buscarEnModrinth(undefined, undefined, nuevoCompat);
                }}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all ${
                  filtrarCompatibilidad
                    ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                    : 'bg-dark-900 border-dark-700 text-slate-400 hover:text-white'
                }`}
                title="Filtra automáticamente por el motor y versión actual de Minecraft"
              >
                <span
                  className={`w-2 h-2 rounded-full ${
                    filtrarCompatibilidad ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.5)]' : 'bg-slate-500'
                  }`}
                />
                <span>
                  {filtrarCompatibilidad
                    ? `${!esMotorVanilla ? motorActual.toUpperCase() : 'Vanilla'} ${versionActual || 'Cualquiera'}`
                    : 'Todos los motores'}
                </span>
              </button>

              <button
                onClick={() => buscarEnModrinth()}
                disabled={modrinthCargando}
                title="Refrescar catálogo"
                className="p-2 bg-dark-900 border border-dark-700 hover:border-slate-600 rounded-xl text-slate-400 hover:text-white transition-colors"
              >
                <RotateCw className={`w-3.5 h-3.5 ${modrinthCargando ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>

          {/* Información contextual del filtro */}
          {filtrarCompatibilidad && (
            <div className="flex items-center justify-between text-[11px] text-slate-400 px-1">
              <span>
                Mostrando mods compatibles con <strong>{motorActual.toUpperCase()}</strong> en Minecraft <strong>{versionActual || 'todas las versiones'}</strong>. (Solo mods compatibles con servidor).
              </span>
              <span>{modrinthTotal} mods encontrados</span>
            </div>
          )}

          {/* Resultados de Modrinth */}
          {modrinthCargando && modrinthResultados.length === 0 ? (
            <div className="p-16 text-center text-slate-500 text-xs">
              <RotateCw className="w-7 h-7 animate-spin mx-auto mb-3 text-emerald-400" />
              Consultando catálogo oficial de Modrinth...
            </div>
          ) : modrinthResultados.length === 0 ? (
            <div className="bg-dark-800/30 border border-dark-700/60 rounded-2xl p-12 text-center">
              <Compass className="w-10 h-10 text-slate-600 mx-auto mb-3" />
              <h4 className="text-sm font-bold text-slate-300">No se encontraron mods</h4>
              <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
                Probá con otro término de búsqueda o desactivá el filtro de compatibilidad para explorar más versiones.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
              {modrinthResultados.map((hit) => {
                const yaInstalado = estaInstaladoLocalmente(hit);
                const instalandoEste = instalandoModId === hit.project_id;

                return (
                  <div
                    key={hit.project_id}
                    className="bg-dark-800/80 border border-dark-700 hover:border-dark-600 rounded-2xl p-4 transition-all flex flex-col justify-between gap-3 shadow-sm"
                  >
                    <div>
                      {/* Cabecera del Mod */}
                      <div className="flex items-start gap-3">
                        <div className="w-12 h-12 rounded-xl bg-dark-900 border border-dark-700 flex items-center justify-center p-1 shrink-0 overflow-hidden">
                          {hit.icon_url ? (
                            <img
                              src={hit.icon_url}
                              alt={hit.title}
                              className="w-full h-full object-cover rounded-lg"
                              loading="lazy"
                            />
                          ) : (
                            <Puzzle className="w-6 h-6 text-emerald-400" />
                          )}
                        </div>

                        <div className="flex-1 min-w-0">
                          <h4 className="font-bold text-xs text-white truncate" title={hit.title}>
                            {hit.title}
                          </h4>
                          <div className="text-[10px] text-slate-400 truncate mt-0.5">
                            por <span className="text-slate-300 font-semibold">{hit.author}</span>
                          </div>

                          <div className="flex items-center gap-1.5 mt-1.5 flex-wrap">
                            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-dark-900 text-slate-400 border border-dark-700 flex items-center gap-1">
                              <Download className="w-2.5 h-2.5 text-slate-400" />
                              {formatearNumero(hit.downloads)}
                            </span>
                            {hit.server_side && hit.server_side !== 'unsupported' && (
                              <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                                Servidor {hit.server_side === 'required' ? 'Req' : 'Opt'}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Descripción */}
                      <p className="text-[11px] text-slate-400 line-clamp-2 mt-3 leading-relaxed">
                        {hit.description}
                      </p>

                      {/* Categorías */}
                      {hit.display_categories && hit.display_categories.length > 0 && (
                        <div className="flex items-center gap-1 mt-2.5 flex-wrap">
                          {hit.display_categories.slice(0, 3).map((cat) => (
                            <span
                              key={cat}
                              className="text-[9px] font-mono uppercase tracking-wider px-1.5 py-0.5 rounded bg-dark-900 text-slate-400 border border-dark-700/60"
                            >
                              {cat}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Botón de Instalación en 1 Clic */}
                    <div className="pt-3 border-t border-dark-700/60 flex items-center justify-between">
                      <a
                        href={`https://modrinth.com/mod/${hit.slug}`}
                        target="_blank"
                        rel="noreferrer"
                        className="text-[10px] text-slate-500 hover:text-emerald-400 transition-colors"
                      >
                        Ver en Modrinth ↗
                      </a>

                      {yaInstalado ? (
                        <button
                          disabled
                          className="flex items-center gap-1 px-3 py-1.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-bold opacity-80 cursor-default"
                        >
                          <Check className="w-3.5 h-3.5" />
                          <span>Instalado</span>
                        </button>
                      ) : (
                        <button
                          onClick={() => manejarInstalarModrinth(hit)}
                          disabled={instalandoEste}
                          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 active:scale-95 disabled:opacity-60 text-white text-xs font-bold transition-all shadow-sm"
                        >
                          {instalandoEste ? (
                            <>
                              <RotateCw className="w-3.5 h-3.5 animate-spin" />
                              <span>Instalando...</span>
                            </>
                          ) : (
                            <>
                              <Download className="w-3.5 h-3.5" />
                              <span>Instalar</span>
                            </>
                          )}
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
