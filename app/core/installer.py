"""
Server installer and JAR downloader.
Fetches official builds from Mojang (Vanilla), Fabric (Mods),
Minecraft Forge, and NeoForge.
"""

import asyncio
import os
import re
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional
import httpx

from app.core.jdk import JdkManager


class ServerInstaller:
    MOJANG_MANIFEST_URL = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
    FABRIC_META_URL = "https://meta.fabricmc.net/v2/versions"
    FORGE_PROMOS_URL = "https://files.minecraftforge.net/net/minecraftforge/forge/promotions_slim.json"
    FORGE_MAVEN_BASE = "https://maven.minecraftforge.net/net/minecraftforge/forge"
    NEOFORGE_MAVEN_META = "https://maven.neoforged.net/releases/net/neoforged/neoforge/maven-metadata.xml"
    NEOFORGE_MAVEN_BASE = "https://maven.neoforged.net/releases/net/neoforged/neoforge"
    NEOFORGE_LEGACY_1201_BASE = "https://maven.neoforged.net/releases/net/neoforged/forge"

    def __init__(self, server_dir: Path, jdk_manager: Optional[JdkManager] = None) -> None:
        self.server_dir = Path(server_dir).resolve()
        self.jdk_manager = jdk_manager or JdkManager()
        self._mojang_manifest_cache: Optional[dict] = None
        self._forge_promos_cache: Optional[dict] = None
        self._neoforge_manifest_cache: Optional[Dict[str, str]] = None

    async def get_mojang_manifest(self) -> dict:
        if self._mojang_manifest_cache is None:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(self.MOJANG_MANIFEST_URL)
                res.raise_for_status()
                self._mojang_manifest_cache = res.json()
        return self._mojang_manifest_cache

    async def get_forge_promos(self) -> dict:
        if self._forge_promos_cache is None:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(self.FORGE_PROMOS_URL)
                res.raise_for_status()
                self._forge_promos_cache = res.json()
        return self._forge_promos_cache

    async def get_neoforge_manifest(self) -> Dict[str, str]:
        """
        Fetches and caches NeoForge maven metadata, mapping Minecraft versions to latest stable NeoForge builds.
        Maps Minecraft versions (e.g. 1.21.4, 1.21.1, 1.20.4, 1.20.1) to NeoForge release versions.
        """
        if self._neoforge_manifest_cache is not None:
            return self._neoforge_manifest_cache

        mapping: Dict[str, str] = {}
        # 1.20.1 is hosted under legacy net.neoforged:forge
        mapping["1.20.1"] = "1.20.1-47.1.106"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(self.NEOFORGE_MAVEN_META)
                if res.status_code == 200:
                    root = ET.fromstring(res.text)
                    raw_versions = [v.text for v in root.findall(".//version") if v.text]
                    for v in raw_versions:
                        m = re.match(r"^(\d+)\.(\d+)(?:\.(\d+))?(?:\.(\d+))?(-.*)?$", v)
                        if not m:
                            continue
                        major = int(m.group(1))
                        minor = int(m.group(2))
                        tag = (m.group(5) or "").lower()

                        # Exclude alpha, snapshot, pre-releases to guarantee stability
                        if "alpha" in tag or "snapshot" in tag or "pre" in tag:
                            continue

                        if major in (20, 21):
                            mc_ver = f"1.{major}.{minor}" if minor > 0 else f"1.{major}"
                        elif major >= 26:
                            mc_ver = f"{major}.{minor}"
                        else:
                            continue

                        current = mapping.get(mc_ver)
                        if not current or ("beta" in current and "beta" not in tag) or ("beta" not in tag):
                            mapping[mc_ver] = v

        except Exception:
            pass

        # Fallback catalog if Maven metadata is temporarily unreachable
        if not mapping or len(mapping) <= 1:
            mapping.update({
                "26.3": "26.3.0.101",
                "26.2": "26.2.0.93",
                "26.1": "26.1.2.126",
                "1.21.4": "21.4.161",
                "1.21.3": "21.3.100",
                "1.21.1": "21.1.265",
                "1.21": "21.0.167",
                "1.20.6": "20.6.144",
                "1.20.4": "20.4.253",
                "1.20.2": "20.2.93",
                "1.20.1": "1.20.1-47.1.106",
            })

        self._neoforge_manifest_cache = mapping
        return self._neoforge_manifest_cache

    async def get_versions(self, server_type: str = "vanilla", include_snapshots: bool = False) -> List[str]:
        """Fetch available versions according to server type (vanilla, fabric, forge, neoforge)."""
        server_type = server_type.lower()
        try:
            if server_type == "vanilla":
                manifest = await self.get_mojang_manifest()
                versions = [
                    v["id"]
                    for v in manifest.get("versions", [])
                    if v.get("type") == "release" or (include_snapshots and v.get("type") == "snapshot")
                ]
                return versions

            elif server_type == "neoforge":
                mapping = await self.get_neoforge_manifest()

                def sort_mc_key(v: str):
                    parts = []
                    for p in v.split("."):
                        try:
                            parts.append(int(p))
                        except ValueError:
                            parts.append(0)
                    return parts

                return sorted(mapping.keys(), key=sort_mc_key, reverse=True)

            elif server_type == "fabric":
                async with httpx.AsyncClient(timeout=10.0) as client:
                    res = await client.get(f"{self.FABRIC_META_URL}/game")
                    if res.status_code == 200:
                        versions = [v["version"] for v in res.json() if v.get("stable")]
                        return versions

            elif server_type == "forge":
                data = await self.get_forge_promos()
                promos = data.get("promos", {})
                raw_versions = set()
                for k in promos.keys():
                    raw_versions.add(k.replace("-latest", "").replace("-recommended", ""))

                def sort_key(v: str):
                    parts = []
                    for p in v.split("."):
                        try:
                            parts.append(int(p))
                        except ValueError:
                            parts.append(0)
                    return parts

                return sorted(raw_versions, key=sort_key, reverse=True)

        except Exception:
            pass

        return ["26.3", "26.2", "26.1", "1.21.4", "1.21.3", "1.21.1", "1.20.4", "1.20.1", "1.19.4", "1.18.2", "1.16.5", "1.12.2"]

    async def download_server(self, server_type: str, version: str) -> Path:
        """Download server executable directly from the authoritative provider."""
        self.server_dir.mkdir(parents=True, exist_ok=True)
        server_type = server_type.lower()
        target_path = self.server_dir / "server.jar"

        async with httpx.AsyncClient(timeout=90.0, follow_redirects=True) as client:
            if server_type == "vanilla":
                manifest = await self.get_mojang_manifest()
                target_ver = next((v for v in manifest.get("versions", []) if v["id"] == version), None)
                if not target_ver:
                    raise RuntimeError(f"Version {version} not found in Mojang manifest.")

                ver_meta_res = await client.get(target_ver["url"])
                ver_meta_res.raise_for_status()
                ver_meta = ver_meta_res.json()
                server_download = ver_meta.get("downloads", {}).get("server")
                if not server_download or "url" not in server_download:
                    raise RuntimeError(f"No server jar available for vanilla version {version}")

                async with client.stream("GET", server_download["url"]) as response:
                    response.raise_for_status()
                    with open(target_path, "wb") as f:
                        async for chunk in response.aiter_bytes(chunk_size=65536):
                            f.write(chunk)
                return target_path

            elif server_type == "fabric":
                loader_res = await client.get(f"{self.FABRIC_META_URL}/loader")
                loader_res.raise_for_status()
                loader_version = loader_res.json()[0]["version"]

                installer_res = await client.get(f"{self.FABRIC_META_URL}/installer")
                installer_res.raise_for_status()
                installer_version = installer_res.json()[0]["version"]

                download_url = f"{self.FABRIC_META_URL}/loader/{version}/{loader_version}/{installer_version}/server/jar"
                async with client.stream("GET", download_url) as response:
                    response.raise_for_status()
                    with open(target_path, "wb") as f:
                        async for chunk in response.aiter_bytes(chunk_size=65536):
                            f.write(chunk)
                return target_path

            elif server_type == "forge":
                data = await self.get_forge_promos()
                promos = data.get("promos", {})
                forge_ver = promos.get(f"{version}-recommended") or promos.get(f"{version}-latest")
                if not forge_ver:
                    raise RuntimeError(f"No Forge build found for Minecraft {version}")

                installer_filename = f"forge-{version}-{forge_ver}-installer.jar"
                installer_url = f"{self.FORGE_MAVEN_BASE}/{version}-{forge_ver}/{installer_filename}"
                installer_path = self.server_dir / "forge-installer.jar"

                # Download installer
                async with client.stream("GET", installer_url) as response:
                    response.raise_for_status()
                    with open(installer_path, "wb") as f:
                        async for chunk in response.aiter_bytes(chunk_size=65536):
                            f.write(chunk)

                # Select best JDK for installer execution
                jdk_info = self.jdk_manager.get_best_jdk_for_version(version)
                java_bin = jdk_info.get("path", "java")
                env = self.jdk_manager.build_env_for_jdk(jdk_info)

                # Execute installer: java -jar forge-installer.jar --installServer
                installer_proc = await asyncio.create_subprocess_exec(
                    java_bin,
                    "-jar",
                    "forge-installer.jar",
                    "--installServer",
                    cwd=str(self.server_dir),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=env,
                )
                stdout, stderr = await installer_proc.communicate()

                # Clean up installer jar
                if installer_path.exists():
                    installer_path.unlink()

                # Check output target
                run_sh = self.server_dir / "run.sh"
                if run_sh.exists():
                    os.chmod(str(run_sh), 0o755)
                    return run_sh

                # Look for forge-*.jar if run.sh was not generated (older Forge)
                for jar in self.server_dir.glob("forge-*.jar"):
                    if not jar.name.endswith("installer.jar"):
                        return jar

                return target_path

            elif server_type == "neoforge":
                mapping = await self.get_neoforge_manifest()
                build_ver = mapping.get(version) or version

                installer_path = self.server_dir / "neoforge-installer.jar"

                # If 1.20.1 legacy, it is under net.neoforged:forge
                if version == "1.20.1" or "1.20.1" in build_ver:
                    installer_url = f"{self.NEOFORGE_LEGACY_1201_BASE}/{build_ver}/forge-{build_ver}-installer.jar"
                else:
                    installer_url = f"{self.NEOFORGE_MAVEN_BASE}/{build_ver}/neoforge-{build_ver}-installer.jar"

                # Download installer
                async with client.stream("GET", installer_url) as response:
                    response.raise_for_status()
                    with open(installer_path, "wb") as f:
                        async for chunk in response.aiter_bytes(chunk_size=65536):
                            f.write(chunk)

                # Select best JDK for installer execution
                jdk_info = self.jdk_manager.get_best_jdk_for_version(version)
                java_bin = jdk_info.get("path", "java")
                env = self.jdk_manager.build_env_for_jdk(jdk_info)

                # Execute installer: java -jar neoforge-installer.jar --installServer
                installer_proc = await asyncio.create_subprocess_exec(
                    java_bin,
                    "-jar",
                    "neoforge-installer.jar",
                    "--installServer",
                    cwd=str(self.server_dir),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=env,
                )
                stdout, stderr = await installer_proc.communicate()

                # Clean up installer jar
                if installer_path.exists():
                    installer_path.unlink()

                # Check output target
                run_sh = self.server_dir / "run.sh"
                if run_sh.exists():
                    os.chmod(str(run_sh), 0o755)
                    return run_sh

                # Fallback search for any generated jar
                for jar in self.server_dir.glob("neoforge-*.jar"):
                    if not jar.name.endswith("installer.jar"):
                        return jar

                for jar in self.server_dir.glob("forge-*.jar"):
                    if not jar.name.endswith("installer.jar"):
                        return jar

                return target_path

            else:
                raise ValueError(f"Unsupported server type: {server_type}")

    def list_installed_jars(self) -> List[str]:
        """List JAR or executable runner files in server directory."""
        if not self.server_dir.exists():
            return []
        files = []
        for p in self.server_dir.glob("*.jar"):
            files.append(p.name)
        for p in self.server_dir.glob("run.sh"):
            files.append(p.name)
        return sorted(files)
