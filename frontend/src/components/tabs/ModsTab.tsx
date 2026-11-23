/**
 * Pestaña de Gestión de Mods y Modpacks para Foxden.
 * Permite subir mods (.jar) y modpacks (.zip) mediante Drag & Drop,
 * visualizarlos con sus metadatos (nombre, versión, motor, tamaño),
 * activar/desactivar en caliente (.jar <-> .jar.disabled) y eliminarlos.
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
} from 'lucide-react';
import { api } from '../../services/api';
import { ModItem, ServerStatus } from '../../types';

interface ModsTabProps {
  status: ServerStatus | null;
  onNavigateToInstaller?: () => void;
}

export const ModsTab: React.FC<ModsTabProps> = ({ status, onNavigateToInstaller }) => {
  const [mods, setMods] = useState<ModItem[]>([]);
  const [cargando, setCargando] = useState<boolean>(true);
  const [subiendo, setSubiendo] = useState<boolean>(false);
  const [busqueda, setBusqueda] = useState<string>('');
  const [filtroEstado, setFiltroEstado] = useState<'todos' | 'activos' | 'desactivados'>('todos');
  const [arrastrando, setArrastrando] = useState<boolean>(false);
  const [modAEliminar, setModAEliminar] = useState<string | null>(null);
  const [accionEnCurso, setAccionEnCurso] = useState<string | null>(null);
  const [notificacion, setNotificacion] = useState<{ tipo: 'exito' | 'error'; mensaje: string } | null>(null);

  const inputArchivoRef = useRef<HTMLInputElement | null>(null);

  const motorActual = (
    status?.installed_engine ||
    (status?.software_info?.type !== 'none' ? status?.software_info?.type : 'vanilla') ||
    'vanilla'
  ).toLowerCase();

  const esMotorVanilla = motorActual === 'vanilla';

  const cargarMods = async () => {
    setCargando(true);
    try {
      const res = await api.obtenerMods();
      setMods(res.mods || []);
    } catch (err: any) {
      setNotificacion({
        tipo: 'error',
        mensaje: err.message || 'Error al cargar la lista de mods.',
      });
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargarMods();
  }, []);

  const limpiarNotificacion = () => setNotificacion(null);

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

  const modsFiltrados = useMemo(() => {
    return mods.filter((mod) => {
      // Filtro por estado
      if (filtroEstado === 'activos' && !mod.enabled) return false;
      if (filtroEstado === 'desactivados' && mod.enabled) return false;

      // Filtro por texto
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

      {/* Barra de Herramientas: Búsqueda, Filtros y Estadísticas */}
      <div className="bg-dark-800/60 border border-dark-700 rounded-2xl p-4 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
        {/* Buscador */}
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            placeholder="Buscar mod por nombre, archivo o descripción..."
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

        {/* Filtros de Estado */}
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

      {/* Lista de Mods */}
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
              ? 'Arrastrá tus archivos .jar o paquetes .zip a la zona superior para comenzar a jugar con mods.'
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
                {/* Cabecera de la Tarjeta */}
                <div className="flex items-start gap-3">
                  {/* Icono de Motor / Mod */}
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

                  {/* Nombre y Metadatos */}
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

                {/* Pie de la Tarjeta con Controles y Tamaño */}
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
                    {/* Botón Alternar Estado (Switch) */}
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

                    {/* Botón Eliminar con Confirmación */}
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
  );
};
