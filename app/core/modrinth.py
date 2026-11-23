"""
Cliente para la API v2 de Modrinth (https://api.modrinth.com/v2).
Permite buscar mods filtrando por versión de Minecraft y cargador (Fabric/Forge/NeoForge),
verificar compatibilidad con el servidor, y descargar e instalar mods y sus dependencias requeridas.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import urllib.parse
import httpx

from app.version import VERSION_APP


class ModrinthClient:
    """Cliente HTTP asíncrono para interactuar con Modrinth API v2."""

    URL_BASE = "https://api.modrinth.com/v2"

    def __init__(self, server_dir: Path, user_agent: Optional[str] = None) -> None:
        self.server_dir = Path(server_dir).resolve()
        self.mods_dir = self.server_dir / "mods"
        self.mods_dir.mkdir(parents=True, exist_ok=True)
        self.user_agent = user_agent or f"AnthoFu/foxden/{VERSION_APP} (https://github.com/AnthoFu/foxden)"

    def _headers(self) -> Dict[str, str]:
        return {
            "User-Agent": self.user_agent,
            "Accept": "application/json",
        }

    async def buscar_mods(
        self,
        query: str = "",
        loader: Optional[str] = None,
        version: Optional[str] = None,
        solo_servidor: bool = True,
        sort: str = "relevance",
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Busca mods en Modrinth con filtros facetados estrictos.
        - project_type: mod
        - categories: loader (si loader != vanilla)
        - versions: version (si está definido)
        - server_side: required / optional (si solo_servidor es True, descarta client-only)
        """
        facets_list: List[List[str]] = [["project_type:mod"]]

        if loader and loader.lower() not in ("vanilla", "none", "desconocido"):
            facets_list.append([f"categories:{loader.lower()}"])

        if version and version.strip():
            facets_list.append([f"versions:{version.strip()}"])

        if solo_servidor:
            # Solo mods que funcionan en servidor (requerido u opcional, no 'unsupported')
            facets_list.append(["server_side:required", "server_side:optional"])

        params = {
            "query": query.strip(),
            "facets": json.dumps(facets_list),
            "index": sort,
            "limit": min(max(1, limit), 50),
            "offset": max(0, offset),
        }

        async with httpx.AsyncClient(timeout=15.0) as cliente:
            res = await cliente.get(
                f"{self.URL_BASE}/search",
                params=params,
                headers=self._headers(),
            )
            res.raise_for_status()
            return res.json()

    async def obtener_versiones(
        self,
        project_id_o_slug: str,
        loader: Optional[str] = None,
        version: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Obtiene las versiones disponibles de un proyecto filtradas por cargador y juego."""
        params: Dict[str, str] = {}
        if loader and loader.lower() not in ("vanilla", "none"):
            params["loaders"] = json.dumps([loader.lower()])
        if version and version.strip():
            params["game_versions"] = json.dumps([version.strip()])

        url = f"{self.URL_BASE}/project/{urllib.parse.quote(project_id_o_slug)}/version"
        async with httpx.AsyncClient(timeout=15.0) as cliente:
            res = await cliente.get(url, params=params, headers=self._headers())
            res.raise_for_status()
            return res.json()

    async def instalar_mod(
        self,
        project_id_o_slug: str,
        version_id: Optional[str] = None,
        loader: Optional[str] = None,
        game_version: Optional[str] = None,
        instalar_dependencias: bool = True,
        visitados: Optional[Set[str]] = None,
    ) -> Dict[str, Any]:
        """
        Descarga e instala el mod en servidor_minecraft/mods/.
        Si instalar_dependencias=True, descarga también las dependencias obligatorias.
        """
        if visitados is None:
            visitados = set()

        if project_id_o_slug in visitados:
            return {"status": "skipped", "reason": "already_visited"}
        visitados.add(project_id_o_slug)

        # 1. Obtener información de la versión adecuada
        version_info = None
        if version_id:
            url_v = f"{self.URL_BASE}/version/{urllib.parse.quote(version_id)}"
            async with httpx.AsyncClient(timeout=15.0) as cliente:
                res = await cliente.get(url_v, headers=self._headers())
                res.raise_for_status()
                version_info = res.json()
        else:
            versiones = await self.obtener_versiones(project_id_o_slug, loader, game_version)
            if not versiones:
                raise ValueError(
                    f"No se encontró una versión compatible para '{project_id_o_slug}' "
                    f"con cargador '{loader}' y versión '{game_version}'."
                )
            version_info = versiones[0]

        # 2. Encontrar el archivo .jar primario
        archivos = version_info.get("files", [])
        if not archivos:
            raise ValueError(f"La versión seleccionada de '{project_id_o_slug}' no tiene archivos descargables.")

        archivo_objetivo = next((f for f in archivos if f.get("primary") and f.get("filename", "").endswith(".jar")), None)
        if not archivo_objetivo:
            archivo_objetivo = next((f for f in archivos if f.get("filename", "").endswith(".jar")), archivos[0])

        url_descarga = archivo_objetivo.get("url")
        nombre_archivo = archivo_objetivo.get("filename", f"{project_id_o_slug}.jar")
        if not url_descarga:
            raise ValueError(f"No se encontró URL de descarga para el archivo {nombre_archivo}.")

        # 3. Descargar el archivo a servidor_minecraft/mods/
        destino = self.mods_dir / nombre_archivo
        async with httpx.AsyncClient(timeout=90.0, follow_redirects=True) as cliente:
            async with cliente.stream("GET", url_descarga, headers=self._headers()) as respuesta:
                respuesta.raise_for_status()
                with open(destino, "wb") as f:
                    async for chunk in respuesta.aiter_bytes(chunk_size=32768):
                        f.write(chunk)

        archivos_instalados = [nombre_archivo]
        dependencias_instaladas: List[str] = []

        # 4. Resolver dependencias obligatorias
        if instalar_dependencias:
            dependencias = version_info.get("dependencies", [])
            for dep in dependencias:
                if dep.get("dependency_type") == "required":
                    dep_proj = dep.get("project_id")
                    dep_ver = dep.get("version_id")
                    if dep_proj and dep_proj not in visitados:
                        try:
                            res_dep = await self.instalar_mod(
                                project_id_o_slug=dep_proj,
                                version_id=dep_ver,
                                loader=loader,
                                game_version=game_version,
                                instalar_dependencias=True,
                                visitados=visitados,
                            )
                            if res_dep.get("status") == "success":
                                archivos_instalados.extend(res_dep.get("installed_files", []))
                                dependencias_instaladas.append(res_dep.get("installed_file", dep_proj))
                        except Exception as e:
                            print(f"[Modrinth] No se pudo instalar dependencia requerida {dep_proj}: {e}")

        return {
            "status": "success",
            "installed_file": nombre_archivo,
            "installed_files": archivos_instalados,
            "dependencies_installed": dependencias_instaladas,
            "version_number": version_info.get("version_number", ""),
        }
