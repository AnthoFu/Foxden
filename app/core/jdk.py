"""
JDK discovery and version management for Minecraft.
Finds installed Java runtimes on the system and matches them with Minecraft version requirements.
"""

import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional


class JdkManager:
    def __init__(self) -> None:
        self._cached_jdks: Optional[List[Dict]] = None

    def list_installed_jdks(self) -> List[Dict]:
        """Scans the system for installed Java runtimes."""
        candidates = [
            Path("/usr/lib/jvm/java-25-openjdk/bin/java"),
            Path("/usr/lib/jvm/java-21-openjdk/bin/java"),
            Path("/usr/lib/jvm/java-17-temurin-jdk/bin/java"),
            Path("/usr/bin/java"),
        ]

        # Scan /usr/lib/jvm subdirectories
        jvm_dir = Path("/usr/lib/jvm")
        if jvm_dir.exists():
            for p in jvm_dir.glob("*/bin/java"):
                if p not in candidates:
                    candidates.append(p)

        found = []
        seen_paths = set()

        for bin_path in candidates:
            resolved = bin_path.resolve()
            if not resolved.exists() or str(resolved) in seen_paths:
                continue
            seen_paths.add(str(resolved))

            try:
                out = subprocess.check_output([str(resolved), "-version"], stderr=subprocess.STDOUT, text=True)
                m = re.search(r'version "(?:1\.)?(\d+)', out)
                if m:
                    major = int(m.group(1))
                    first_line = out.splitlines()[0] if out.splitlines() else f"Java {major}"
                    found.append({
                        "major": major,
                        "path": str(resolved),
                        "name": f"Java {major} ({first_line.split('(')[0].strip()})",
                        "home": str(resolved.parent.parent),
                    })
            except Exception:
                pass

        # Sort descending by major version
        found.sort(key=lambda x: x["major"], reverse=True)
        return found

    def get_best_jdk_for_version(self, mc_version: Optional[str] = None) -> Dict:
        """Finds the best installed JDK for a given Minecraft version string."""
        jdks = self.list_installed_jdks()
        if not jdks:
            return {"major": 0, "path": "java", "name": "System default java", "home": ""}

        # Determine required minimum Java version
        # Minecraft 26.x requires Java 25 (class file 69.0)
        # Minecraft 1.20.5 - 1.21.x requires Java 21 (class file 65.0)
        # Minecraft 1.18 - 1.20.4 requires Java 17 (class file 61.0)
        req_major = 17
        if mc_version:
            v_clean = mc_version.strip()
            if v_clean.startswith("26"):
                req_major = 25
            elif v_clean.startswith("1.21") or v_clean.startswith("1.20.5") or v_clean.startswith("1.20.6"):
                req_major = 21

        # Look for matching major JDK
        for jdk in jdks:
            if jdk["major"] == req_major:
                return jdk

        # If higher JDK is available, use it (newer Java can usually run older MC)
        for jdk in jdks:
            if jdk["major"] >= req_major:
                return jdk

        # Fallback to the highest available JDK
        return jdks[0]

    def build_env_for_jdk(self, jdk_info: Dict) -> dict:
        """Builds environment dictionary with JAVA_HOME and PATH pointing to selected JDK."""
        env = os.environ.copy()
        home = jdk_info.get("home")
        if home and Path(home).exists():
            env["JAVA_HOME"] = home
            bin_dir = str(Path(home) / "bin")
            env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
        return env
