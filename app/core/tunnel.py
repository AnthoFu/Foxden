"""
Playit.gg tunnel manager.
Automates downloading the standalone playit binary, managing the tunnel process,
extracting claim URLs, and surfacing public connection IPs via daemon and CLI query.
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
    PLAYIT_RELEASES_URL = "https://github.com/playit-cloud/playit-agent/releases/download/v0.15.26"

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

    @property
    def binary_path(self) -> Path:
        return self.bin_dir / "playit"

    async def ensure_binary_installed(self) -> Path:
        """Downloads playit binary if not already present."""
        if self.binary_path.exists() and os.access(str(self.binary_path), os.X_OK):
            return self.binary_path

        self.bin_dir.mkdir(parents=True, exist_ok=True)
        arch = platform.machine().lower()
        asset_name = "playit-linux-aarch64" if "arm" in arch or "aarch64" in arch else "playit-linux-amd64"
        download_url = f"{self.PLAYIT_RELEASES_URL}/{asset_name}"

        self.logs.append(f"[PLAYIT] Downloading playit agent from {download_url}...")
        async with httpx.AsyncClient(timeout=45.0, follow_redirects=True) as client:
            async with client.stream("GET", download_url) as res:
                res.raise_for_status()
                with open(self.binary_path, "wb") as f:
                    async for chunk in res.aiter_bytes(65536):
                        f.write(chunk)

        os.chmod(str(self.binary_path), 0o755)
        self.logs.append("[PLAYIT] Playit binary installed successfully.")
        return self.binary_path

    async def start(self) -> bool:
        """Starts the playit tunnel process."""
        if self.state in ("RUNNING", "WAITING_CLAIM") and self.process:
            return True

        try:
            bin_path = await self.ensure_binary_installed()
        except Exception as e:
            self.logs.append(f"[PLAYIT] Failed to install binary: {e}")
            return False

        self.state = "STARTING"
        self.claim_url = None
        self.public_address = None
        self._refresh_attempted = False
        self.logs.append(f"[PLAYIT] Starting tunnel process with config: {self.config_file}")

        cmd = [str(bin_path), "--secret_path", str(self.config_file), "--stdout", "start"]
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
            self.logs.append(f"[PLAYIT] Failed to launch process: {e}")
            return False

        self._reader_task = asyncio.create_task(self._read_tunnel_output())
        return True

    async def _read_tunnel_output(self) -> None:
        if not self.process or not self.process.stdout:
            return

        while True:
            line_bytes = await self.process.stdout.readline()
            if not line_bytes:
                break

            line = line_bytes.decode("utf-8", errors="replace").rstrip("\r\n")
            clean_line = re.sub(r"\x1b\[[0-9;]*m", "", line)
            self.logs.append(clean_line)

            # Detect claim URL (e.g. https://playit.gg/claim/108ac57d95)
            claim_match = re.search(r"https://playit\.gg/claim/[a-zA-Z0-9]+", clean_line)
            if claim_match:
                self.claim_url = claim_match.group(0)
                self.state = "WAITING_CLAIM"

            # Detect public tunnel address from stdout if present
            addr_match = re.search(r"([a-zA-Z0-9\-\.]+\.(?:ply\.gg|playit\.gg)(?::\d+)?)", clean_line)
            if addr_match:
                self.public_address = addr_match.group(1)
                self.state = "RUNNING"
                self.claim_url = None

            if "tunnel running" in clean_line.lower() or "connection established" in clean_line.lower():
                self.state = "RUNNING"
                self.claim_url = None
                # Query tunnels list once with slight delay if public_address is not yet found
                if not self.public_address and not self._refresh_attempted:
                    self._refresh_attempted = True
                    asyncio.create_task(self._delayed_refresh_address())

        await self.process.wait()
        self.state = "STOPPED"
        self.process = None
        self.logs.append("[PLAYIT] Tunnel process exited.")

    async def _delayed_refresh_address(self) -> None:
        """Waits briefly for tunnel registration before querying tunnels list once."""
        await asyncio.sleep(4.0)
        await self.refresh_public_address()

    async def refresh_public_address(self) -> Optional[str]:
        """Queries playit tunnels list to resolve public address."""
        if not self.config_file.exists() or not self.binary_path.exists() or self._refreshing_addr:
            return self.public_address

        self._refreshing_addr = True
        try:
            proc = await asyncio.create_subprocess_exec(
                str(self.binary_path),
                "--secret_path",
                str(self.config_file),
                "tunnels",
                "list",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.base_dir),
            )
            stdout, _ = await proc.communicate()
            output = stdout.decode("utf-8", errors="replace").strip()
            for line in output.splitlines():
                m = re.search(r"([a-zA-Z0-9\-\.]+\.(?:ply\.gg|playit\.gg)(?::\d+)?)", line)
                if m:
                    self.public_address = m.group(1)
                    self.state = "RUNNING"
                    return self.public_address
                parts = line.strip().split()
                if len(parts) >= 4 and ("." in parts[-1] or ":" in parts[-1]):
                    self.public_address = parts[-1]
                    self.state = "RUNNING"
                    return self.public_address
        except Exception:
            pass
        finally:
            self._refreshing_addr = False

        return self.public_address

    async def stop(self) -> bool:
        """Stops the playit tunnel process."""
        if self.state == "STOPPED" or not self.process:
            return False

        self.state = "STOPPING"
        try:
            self.process.terminate()
            await asyncio.wait_for(self.process.wait(), timeout=5.0)
        except Exception:
            if self.process:
                self.process.kill()

        self.state = "STOPPED"
        self.process = None
        return True

    def get_status(self) -> dict:
        return {
            "state": self.state,
            "claim_url": self.claim_url,
            "public_address": self.public_address,
            "has_config": self.config_file.exists(),
            "recent_logs": list(self.logs)[-25:],
        }
