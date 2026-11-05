"""
Process management module for Minecraft server.
Handles execution, stdin command routing, async log streaming, and resource monitoring.
"""

import asyncio
import os
import signal
import time
from collections import deque
from enum import Enum
from pathlib import Path
from typing import Callable, Deque, Dict, List, Optional, Set
import psutil


class ProcessState(str, Enum):
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"


class MinecraftProcess:
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

    def subscribe(self, callback: Callable[[str], None]) -> None:
        self._subscribers.add(callback)

    def unsubscribe(self, callback: Callable[[str], None]) -> None:
        self._subscribers.discard(callback)

    def _broadcast_log(self, line: str) -> None:
        self.log_history.append(line)
        for cb in list(self._subscribers):
            try:
                cb(line)
            except Exception:
                pass

    async def start(self, env: Optional[Dict[str, str]] = None) -> bool:
        if self.state != ProcessState.STOPPED:
            return False

        if not self.server_dir.exists():
            self.server_dir.mkdir(parents=True, exist_ok=True)

        self.state = ProcessState.STARTING
        self.start_time = time.time()
        self._broadcast_log(f"[FOXDEN] Starting server in {self.server_dir}...")
        self._broadcast_log(f"[FOXDEN] Command: {' '.join(self.launch_command)}")

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
            self._broadcast_log(f"[FOXDEN] Failed to spawn process: {e}")
            return False

        self._reader_task = asyncio.create_task(self._read_output())
        return True

    async def _read_output(self) -> None:
        if not self.process or not self.process.stdout:
            return

        while True:
            line_bytes = await self.process.stdout.readline()
            if not line_bytes:
                break

            line = line_bytes.decode("utf-8", errors="replace").rstrip("\r\n")
            self._broadcast_log(line)

            # Detect server ready signal
            if self.state == ProcessState.STARTING:
                if 'Done (' in line and ')! For help, type "help"' in line or "Timings Reset" in line:
                    self.state = ProcessState.RUNNING
                    self._broadcast_log("[FOXDEN] Server is now RUNNING and ready for players!")

        return_code = await self.process.wait()
        self.state = ProcessState.STOPPED
        self.process = None
        self._broadcast_log(f"[FOXDEN] Server process exited with code {return_code}.")

    async def send_command(self, command: str) -> bool:
        if not self.process or self.process.returncode is not None or not self.process.stdin:
            return False

        clean_cmd = command.strip()
        if not clean_cmd:
            return False

        try:
            self.process.stdin.write(f"{clean_cmd}\n".encode("utf-8"))
            await self.process.stdin.drain()
            self._broadcast_log(f"> {clean_cmd}")
            return True
        except Exception as e:
            self._broadcast_log(f"[FOXDEN] Error sending command: {e}")
            return False

    async def stop(self, timeout: float = 25.0) -> bool:
        if self.state in (ProcessState.STOPPED, ProcessState.STOPPING) or not self.process:
            return False

        self.state = ProcessState.STOPPING
        self._broadcast_log("[FOXDEN] Stopping server gracefully (sending 'stop')...")
        await self.send_command("stop")

        # Wait for graceful shutdown
        start_wait = time.time()
        while self.process and self.process.returncode is None:
            if time.time() - start_wait > timeout:
                self._broadcast_log("[FOXDEN] Graceful shutdown timed out. Terminating process...")
                try:
                    self.process.terminate()
                except ProcessLookupError:
                    pass
                break
            await asyncio.sleep(0.5)

        self.state = ProcessState.STOPPED
        return True

    async def restart(self) -> bool:
        if self.state != ProcessState.STOPPED:
            await self.stop()
            # wait until fully stopped
            while self.state != ProcessState.STOPPED:
                await asyncio.sleep(0.5)
        return await self.start()

    def get_metrics(self) -> dict:
        uptime = 0.0
        if self.start_time and self.state in (ProcessState.STARTING, ProcessState.RUNNING):
            uptime = round(time.time() - self.start_time, 1)

        cpu_percent = 0.0
        memory_mb = 0.0
        memory_percent = 0.0

        if self.process and self.process.pid and self.state != ProcessState.STOPPED:
            try:
                proc = psutil.Process(self.process.pid)
                # Include child processes (Java threads/helpers)
                procs = [proc] + proc.children(recursive=True)
                cpu_percent = sum(p.cpu_percent(interval=None) for p in procs)
                total_rss = sum(p.memory_info().rss for p in procs)
                memory_mb = round(total_rss / (1024 * 1024), 1)
                system_mem = psutil.virtual_memory().total
                memory_percent = round((total_rss / system_mem) * 100, 1) if system_mem else 0.0
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        return {
            "state": self.state.value,
            "pid": self.process.pid if self.process else None,
            "uptime_seconds": uptime,
            "cpu_percent": cpu_percent,
            "memory_mb": memory_mb,
            "memory_percent": memory_percent,
            "server_dir": str(self.server_dir),
        }
