"""
Módulo de gestión del proceso del servidor de Minecraft.
Maneja la ejecución asíncrona, enrutamiento de comandos vía stdin,
transmisión de logs en vivo y monitoreo de recursos del sistema (CPU y RAM).
"""

import asyncio
import os
import signal
import time
from collections import deque
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Deque, Dict, List, Optional, Set
import psutil


class ProcessState(str, Enum):
    """Estados del ciclo de vida del proceso de Minecraft."""
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"


class MinecraftProcess:
    """Controlador y supervisor del proceso del servidor de Minecraft."""

    def __init__(
        self,
        server_dir: Path,
        launch_command: Optional[List[str]] = None,
        max_log_history: int = 1500,
    ) -> None:
        self.server_dir = Path(server_dir).resolve()
        self.launch_command = launch_command or ["java", "-Xms2G", "-Xmx4G", "-jar", "server.jar", "nogui"]
        self.state: ProcessState = ProcessState.STOPPED
        self.process: Optional[asyncio.subprocess.Process] = None
        self.start_time: Optional[float] = None
        self.log_history: Deque[str] = deque(maxlen=max_log_history)
        self._subscribers: Set[Callable[[str], None]] = set()
        self._reader_task: Optional[asyncio.Task] = None
        self.on_server_ready: Optional[Callable[[], Any]] = None
        self.on_server_stopped: Optional[Callable[[float, int], Any]] = None

    def suscribir(self, callback: Callable[[str], None]) -> None:
        """Registra un observador para recibir cada nueva línea de log."""
        self._subscribers.add(callback)

    def desuscribir(self, callback: Callable[[str], None]) -> None:
        """Elimina un observador registrado."""
        self._subscribers.discard(callback)

    def _transmitir_registro(self, linea: str) -> None:
        """Agrega la línea al historial en memoria y la transmite a los suscriptores."""
        self.log_history.append(linea)
        for cb in list(self._subscribers):
            try:
                cb(linea)
            except Exception:
                pass

    async def iniciar(self, env: Optional[Dict[str, str]] = None) -> bool:
        """Inicia el proceso hijo de Minecraft de forma asíncrona."""
        if self.state != ProcessState.STOPPED:
            return False

        if not self.server_dir.exists():
            self.server_dir.mkdir(parents=True, exist_ok=True)

        self.state = ProcessState.STARTING
        self.start_time = time.time()
        self._transmitir_registro(f"[FOXDEN] Iniciando servidor en {self.server_dir}...")
        self._transmitir_registro(f"[FOXDEN] Comando ejecutado: {' '.join(self.launch_command)}")

        try:
            self.process = await asyncio.create_subprocess_exec(
                *self.launch_command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=str(self.server_dir),
                env=env,
            )
        except Exception as e:
            self.state = ProcessState.STOPPED
            self._transmitir_registro(f"[FOXDEN] Error al iniciar el proceso del servidor: {e}")
            return False

        self._reader_task = asyncio.create_task(self._leer_salida())
        return True

    async def _leer_salida(self) -> None:
        """Lee continuamente la salida estándar y de error del proceso de Minecraft."""
        if not self.process or not self.process.stdout:
            return

        while True:
            line_bytes = await self.process.stdout.readline()
            if not line_bytes:
                break

            linea = line_bytes.decode("utf-8", errors="replace").rstrip("\r\n")
            self._transmitir_registro(linea)

            # Detectar señal de servidor listo
            if self.state == ProcessState.STARTING:
                if 'Done (' in linea and ')! For help, type "help"' in linea or "Timings Reset" in linea:
                    self.state = ProcessState.RUNNING
                    self._transmitir_registro("[FOXDEN] ¡El servidor está EN LÍNEA y listo para recibir jugadores!")
                    if self.on_server_ready:
                        try:
                            res = self.on_server_ready()
                            if asyncio.iscoroutine(res):
                                asyncio.create_task(res)
                        except Exception as cb_err:
                            self._transmitir_registro(f"[FOXDEN] Error en callback de servidor listo: {cb_err}")

        codigo_retorno = await self.process.wait()
        tiempo_activo = time.time() - self.start_time if self.start_time else 0.0
        self.state = ProcessState.STOPPED
        self.process = None
        self._transmitir_registro(f"[FOXDEN] El proceso del servidor finalizó con código {codigo_retorno}.")
        if self.on_server_stopped:
            try:
                res = self.on_server_stopped(tiempo_activo, codigo_retorno)
                if asyncio.iscoroutine(res):
                    asyncio.create_task(res)
            except Exception as cb_err:
                self._transmitir_registro(f"[FOXDEN] Error en callback de servidor detenido: {cb_err}")

    async def enviar_comando(self, comando: str) -> bool:
        """Escribe un comando en la consola estándar (stdin) del servidor de Minecraft."""
        if not self.process or self.process.returncode is not None or not self.process.stdin:
            return False

        comando_limpio = comando.strip()
        if not comando_limpio:
            return False

        try:
            self.process.stdin.write(f"{comando_limpio}\n".encode("utf-8"))
            await self.process.stdin.drain()
            self._transmitir_registro(f"> {comando_limpio}")
            return True
        except Exception as e:
            self._transmitir_registro(f"[FOXDEN] Error al enviar comando: {e}")
            return False

    async def detener(self, timeout: float = 25.0) -> bool:
        """Detiene el servidor enviando el comando seguro 'stop' y esperando su cierre."""
        if self.state in (ProcessState.STOPPED, ProcessState.STOPPING) or not self.process:
            return False

        self.state = ProcessState.STOPPING
        self._transmitir_registro("[FOXDEN] Deteniendo el servidor de forma segura (enviando 'stop')...")
        await self.enviar_comando("stop")

        # Esperar apagado limpio
        inicio_espera = time.time()
        while self.process and self.process.returncode is None:
            if time.time() - inicio_espera > timeout:
                self._transmitir_registro("[FOXDEN] Tiempo de espera agotado para el cierre seguro. Forzando detención del proceso...")
                try:
                    self.process.terminate()
                except ProcessLookupError:
                    pass
                break
            await asyncio.sleep(0.5)

        self.state = ProcessState.STOPPED
        return True

    async def reiniciar(self) -> bool:
        """Detiene y vuelve a iniciar el servidor de Minecraft."""
        if self.state != ProcessState.STOPPED:
            await self.detener()
            while self.state != ProcessState.STOPPED:
                await asyncio.sleep(0.5)
        return await self.iniciar()

    def obtener_metricas(self) -> dict:
        """Calcula el consumo actual de CPU, memoria RAM y tiempo en línea."""
        tiempo_activo = 0.0
        if self.start_time and self.state in (ProcessState.STARTING, ProcessState.RUNNING):
            tiempo_activo = round(time.time() - self.start_time, 1)

        porcentaje_cpu = 0.0
        memoria_mb = 0.0
        porcentaje_memoria = 0.0

        if self.process and self.process.pid and self.state != ProcessState.STOPPED:
            try:
                proc = psutil.Process(self.process.pid)
                # Incluir subprocesos hijos (hilos o procesos Java)
                procesos = [proc] + proc.children(recursive=True)
                porcentaje_cpu = sum(p.cpu_percent(interval=None) for p in procesos)
                total_rss = sum(p.memory_info().rss for p in procesos)
                memoria_mb = round(total_rss / (1024 * 1024), 1)
                memoria_sistema = psutil.virtual_memory().total
                porcentaje_memoria = round((total_rss / memoria_sistema) * 100, 1) if memoria_sistema else 0.0
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        return {
            "state": self.state.value,
            "pid": self.process.pid if self.process else None,
            "uptime_seconds": tiempo_activo,
            "cpu_percent": porcentaje_cpu,
            "memory_mb": memoria_mb,
            "memory_percent": porcentaje_memoria,
            "server_dir": str(self.server_dir),
        }

    # Alias en inglés para compatibilidad
    subscribe = suscribir
    unsubscribe = desuscribir
    _broadcast_log = _transmitir_registro
    start = iniciar
    stop = detener
    restart = reiniciar
    send_command = enviar_comando
    get_metrics = obtener_metricas
    _read_output = _leer_salida
