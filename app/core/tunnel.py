"""
Módulo de gestión del túnel de Playit.gg.
Automatiza la descarga del binario de playit, gestiona el proceso en segundo plano,
detecta enlaces de vinculación y resuelve la dirección pública para multijugador.
"""

import asyncio
import os
import platform
import re
from pathlib import Path
from typing import Deque, List, Optional
from collections import deque
import httpx


class PlayitTunnelManager:
    """Administrador del túnel de red Playit.gg."""

    URL_RELEASES_PLAYIT = "https://github.com/playit-cloud/playit-agent/releases/download/v0.15.26"
    PLAYIT_RELEASES_URL = URL_RELEASES_PLAYIT

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = Path(base_dir).resolve()
        self.bin_dir = self.base_dir / "bin"
        self.config_file = self.base_dir / "playit.toml"
        self.process: Optional[asyncio.subprocess.Process] = None
        self.state: str = "STOPPED"
        self.claim_url: Optional[str] = None
        self.public_address: Optional[str] = None
        self.logs: Deque[str] = deque(maxlen=200)
        self._reader_task: Optional[asyncio.Task] = None
        self._refreshing_addr: bool = False
        self._refresh_attempted: bool = False
        self._lock = asyncio.Lock()

    @property
    def ruta_binario(self) -> Path:
        """Ruta al ejecutable local de Playit."""
        return self.bin_dir / "playit"

    # Alias de compatibilidad
    binary_path = ruta_binario

    async def asegurar_binario_instalado(self) -> Path:
        """Descarga e instala el binario oficial de playit si aún no está presente."""
        if self.ruta_binario.exists() and os.access(str(self.ruta_binario), os.X_OK):
            return self.ruta_binario

        self.bin_dir.mkdir(parents=True, exist_ok=True)
        arquitectura = platform.machine().lower()
        nombre_recurso = "playit-linux-aarch64" if "arm" in arquitectura or "aarch64" in arquitectura else "playit-linux-amd64"
        url_descarga = f"{self.URL_RELEASES_PLAYIT}/{nombre_recurso}"

        self.logs.append(f"[PLAYIT] Descargando agente Playit desde {url_descarga}...")
        async with httpx.AsyncClient(timeout=45.0, follow_redirects=True) as cliente:
            async with cliente.stream("GET", url_descarga) as res:
                res.raise_for_status()
                with open(self.ruta_binario, "wb") as f:
                    async for bloque in res.aiter_bytes(65536):
                        f.write(bloque)

        os.chmod(str(self.ruta_binario), 0o755)
        self.logs.append("[PLAYIT] Agente Playit instalado correctamente.")
        return self.ruta_binario

    async def iniciar(self) -> bool:
        """Inicia el proceso del túnel de Playit."""
        async with self._lock:
            if self.state in ("RUNNING", "WAITING_CLAIM", "STARTING") and self.process and self.process.returncode is None:
                return True

            if self._reader_task and not self._reader_task.done():
                self._reader_task.cancel()
                try:
                    await asyncio.wait_for(self._reader_task, timeout=1.0)
                except Exception:
                    pass
                self._reader_task = None

            try:
                ruta_bin = await self.asegurar_binario_instalado()
            except Exception as e:
                self.logs.append(f"[PLAYIT] Error al instalar el binario: {e}")
                return False

            self.state = "STARTING"
            self.claim_url = None
            self.public_address = None
            self._refresh_attempted = False
            self.logs.append(f"[PLAYIT] Iniciando proceso de túnel con configuración: {self.config_file}")

            cmd = [str(ruta_bin), "--secret_path", str(self.config_file), "--stdout", "start"]
            try:
                self.process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                    cwd=str(self.base_dir),
                )
            except Exception as e:
                self.state = "STOPPED"
                self.logs.append(f"[PLAYIT] Error al iniciar el proceso: {e}")
                return False

            self._reader_task = asyncio.create_task(self._leer_salida_tunel())
            return True

    async def _leer_salida_tunel(self) -> None:
        """Lee la salida estándar del túnel para capturar URLs de vinculación y direcciones IP."""
        proc = self.process
        if not proc or not proc.stdout:
            return

        try:
            while True:
                line_bytes = await proc.stdout.readline()
                if not line_bytes:
                    break

                linea = line_bytes.decode("utf-8", errors="replace").rstrip("\r\n")
                linea_limpia = re.sub(r"\x1b\[[0-9;]*m", "", linea)
                self.logs.append(linea_limpia)

                # Detectar enlace de vinculación
                match_claim = re.search(r"https://playit\.gg/claim/[a-zA-Z0-9]+", linea_limpia)
                if match_claim:
                    self.claim_url = match_claim.group(0)
                    self.state = "WAITING_CLAIM"

                # Detectar dirección pública en la salida
                match_dir = re.search(r"([a-zA-Z0-9\-\.]+\.(?:ply\.gg|playit\.gg)(?::\d+)?)", linea_limpia)
                if match_dir:
                    self.public_address = match_dir.group(1)
                    self.state = "RUNNING"
                    self.claim_url = None

                if "tunnel running" in linea_limpia.lower() or "connection established" in linea_limpia.lower():
                    self.state = "RUNNING"
                    self.claim_url = None
                    if not self.public_address and not self._refresh_attempted:
                        self._refresh_attempted = True
                        asyncio.create_task(self._refrescar_direccion_demorado())
        except (asyncio.CancelledError, RuntimeError):
            pass
        finally:
            try:
                await proc.wait()
            except Exception:
                pass
            if self.process is proc:
                self.state = "STOPPED"
                self.process = None
                self.logs.append("[PLAYIT] El proceso del túnel se detuvo.")

    async def _refrescar_direccion_demorado(self) -> None:
        """Espera unos segundos para consultar la lista de túneles si no apareció en stdout."""
        await asyncio.sleep(4.0)
        await self.refrescar_direccion_publica()

    async def refrescar_direccion_publica(self) -> Optional[str]:
        """Ejecuta 'playit tunnels list' para resolver la dirección pública asignada."""
        if not self.config_file.exists() or not self.ruta_binario.exists() or self._refreshing_addr:
            return self.public_address

        self._refreshing_addr = True
        try:
            proc = await asyncio.create_subprocess_exec(
                str(self.ruta_binario),
                "--secret_path",
                str(self.config_file),
                "tunnels",
                "list",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.base_dir),
            )
            stdout, _ = await proc.communicate()
            salida = stdout.decode("utf-8", errors="replace").strip()
            for linea in salida.splitlines():
                m = re.search(r"([a-zA-Z0-9\-\.]+\.(?:ply\.gg|playit\.gg)(?::\d+)?)", linea)
                if m:
                    self.public_address = m.group(1)
                    self.state = "RUNNING"
                    return self.public_address
                partes = linea.strip().split()
                if len(partes) >= 4 and ("." in partes[-1] or ":" in partes[-1]):
                    self.public_address = partes[-1]
                    self.state = "RUNNING"
                    return self.public_address
        except Exception:
            pass
        finally:
            self._refreshing_addr = False

        return self.public_address

    async def detener(self) -> bool:
        """Detiene el proceso del túnel de Playit."""
        async with self._lock:
            if self.state == "STOPPED" or not self.process:
                return False

            self.state = "STOPPING"
            if self._reader_task and not self._reader_task.done():
                self._reader_task.cancel()
                try:
                    await asyncio.wait_for(self._reader_task, timeout=1.0)
                except Exception:
                    pass
                self._reader_task = None

            try:
                self.process.terminate()
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except Exception:
                if self.process:
                    self.process.kill()

            self.state = "STOPPED"
            self.process = None
            return True

    def obtener_estado(self) -> dict:
        """Devuelve el estado estructurado del túnel para la API y el panel."""
        return {
            "state": self.state,
            "claim_url": self.claim_url,
            "public_address": self.public_address,
            "has_config": self.config_file.exists(),
            "recent_logs": list(self.logs)[-25:],
        }

    # Alias en inglés para compatibilidad
    ensure_binary_installed = asegurar_binario_instalado
    start = iniciar
    stop = detener
    get_status = obtener_estado
    refresh_public_address = refrescar_direccion_publica
    _read_tunnel_output = _leer_salida_tunel
    _delayed_refresh_address = _refrescar_direccion_demorado
