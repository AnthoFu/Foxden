"""
REST API routes for Minecraft server manager.
"""

from pathlib import Path
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import ConfigManager
from app.core.installer import ServerInstaller
from app.core.jdk import JdkManager
from app.core.process import MinecraftProcess
from app.core.tunnel import PlayitTunnelManager

router = APIRouter(prefix="/api")


class CommandRequest(BaseModel):
    command: str = Field(..., description="Minecraft console command")


class ConfigUpdateRequest(BaseModel):
    properties: Dict[str, str] = Field(default_factory=dict)
    min_ram_gb: Optional[int] = Field(default=None, ge=1, le=64)
    max_ram_gb: Optional[int] = Field(default=None, ge=1, le=64)
    target_jar: Optional[str] = Field(default=None)
    selected_jdk: Optional[str] = Field(default=None)


class DownloadVersionRequest(BaseModel):
    server_type: str = Field(default="vanilla", description="vanilla, fabric, purpur, or forge")
    version: str = Field(..., description="Minecraft version string, e.g. 26.2, 1.21.4")


def detect_software_info(server_dir: Path, target: str) -> dict:
    """Detects a friendly name and description for the active Minecraft server setup."""
    target_lower = target.lower()

    if target == "run.sh" or (server_dir / "run.sh").exists() or "forge" in target_lower:
        return {
            "name": "Minecraft Forge",
            "icon": "🔨",
            "type": "forge",
            "runner": target if target else "run.sh",
            "description": "Servidor con soporte para mods de Forge (ejecuta run.sh)",
        }
    if "fabric" in target_lower or (server_dir / ".fabric").exists():
        return {
            "name": "Fabric Loader",
            "icon": "🧵",
            "type": "fabric",
            "runner": target if target else "server.jar",
            "description": "Servidor con soporte para mods de Fabric",
        }
    if "purpur" in target_lower:
        return {
            "name": "Purpur (Paper fork)",
            "icon": "⚡",
            "type": "purpur",
            "runner": target if target else "server.jar",
            "description": "Servidor de alto rendimiento compatible con plugins",
        }
    return {
        "name": "Minecraft Vanilla (Oficial)",
        "icon": "🍦",
        "type": "vanilla",
        "runner": target if target else "server.jar",
        "description": "Servidor oficial de Mojang sin modificaciones",
    }


def setup_routes(
    app_router: APIRouter,
    process: MinecraftProcess,
    config_mgr: ConfigManager,
    installer: ServerInstaller,
    tunnel_mgr: PlayitTunnelManager,
    launch_state: dict,
) -> None:
    jdk_manager = JdkManager()

    @app_router.get("/status")
    async def get_status():
        metrics = process.get_metrics()
        target = launch_state.get("target_jar", "server.jar")
        metrics["target_jar"] = target
        metrics["min_ram_gb"] = launch_state.get("min_ram_gb", 2)
        metrics["max_ram_gb"] = launch_state.get("max_ram_gb", 4)
        metrics["software_info"] = detect_software_info(installer.server_dir, target)
        metrics["installed_version"] = launch_state.get("installed_version", "")
        metrics["active_jdk"] = launch_state.get("selected_jdk", "auto")
        metrics["tunnel"] = tunnel_mgr.get_status()
        return metrics

    @app_router.get("/jdks")
    async def get_jdks():
        installed = jdk_manager.list_installed_jdks()
        return {"jdks": installed}

    @app_router.get("/tunnel/status")
    async def get_tunnel_status():
        return tunnel_mgr.get_status()

    @app_router.post("/tunnel/start")
    async def start_tunnel():
        success = await tunnel_mgr.start()
        if not success and tunnel_mgr.state != "RUNNING":
            raise HTTPException(status_code=400, detail="Failed to start Playit tunnel")
        return {"status": "started", "tunnel": tunnel_mgr.get_status()}

    @app_router.post("/tunnel/stop")
    async def stop_tunnel():
        success = await tunnel_mgr.stop()
        if not success:
            raise HTTPException(status_code=400, detail="Tunnel is not running")
        return {"status": "stopped", "tunnel": tunnel_mgr.get_status()}

    @app_router.post("/server/start")
    async def start_server():
        config_mgr.ensure_eula_accepted()

        min_ram = launch_state.get("min_ram_gb", 2)
        max_ram = launch_state.get("max_ram_gb", 4)
        target = launch_state.get("target_jar", "server.jar")
        installed_version = launch_state.get("installed_version", "")

        # Select best JDK
        selected_jdk_path = launch_state.get("selected_jdk")
        if selected_jdk_path and selected_jdk_path != "auto":
            jdks = jdk_manager.list_installed_jdks()
            jdk_info = next((j for j in jdks if j["path"] == selected_jdk_path), None)
            if not jdk_info:
                jdk_info = jdk_manager.get_best_jdk_for_version(installed_version)
        else:
            jdk_info = jdk_manager.get_best_jdk_for_version(installed_version)

        env = jdk_manager.build_env_for_jdk(jdk_info)
        java_bin = jdk_info.get("path", "java")

        # Auto-resolve target if run.sh exists and target is run.sh
        if (installer.server_dir / "run.sh").exists() and target == "run.sh":
            process.launch_command = ["bash", "run.sh"]
        elif target.endswith(".sh"):
            process.launch_command = ["bash", target]
        else:
            process.launch_command = [
                java_bin,
                f"-Xms{min_ram}G",
                f"-Xmx{max_ram}G",
                "-jar",
                target,
                "nogui",
            ]

        success = await process.start(env=env)
        if not success:
            raise HTTPException(status_code=400, detail="Server could not be started or is already running")
        return {"status": "started", "metrics": process.get_metrics(), "jdk_used": jdk_info}

    @app_router.post("/server/stop")
    async def stop_server():
        success = await process.stop()
        if not success:
            raise HTTPException(status_code=400, detail="Server is not running")
        return {"status": "stopped"}

    @app_router.post("/server/restart")
    async def restart_server():
        success = await process.restart()
        if not success:
            raise HTTPException(status_code=400, detail="Failed to restart server")
        return {"status": "restarted"}

    @app_router.post("/server/command")
    async def send_command(req: CommandRequest):
        success = await process.send_command(req.command)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to send command. Is server running?")
        return {"status": "command_sent"}

    @app_router.get("/config")
    async def get_config():
        summary = config_mgr.get_summary_settings()
        all_props = config_mgr.read_properties()
        target = launch_state.get("target_jar", "server.jar")
        return {
            "summary": summary,
            "all_properties": all_props,
            "min_ram_gb": launch_state.get("min_ram_gb", 2),
            "max_ram_gb": launch_state.get("max_ram_gb", 4),
            "target_jar": target,
            "selected_jdk": launch_state.get("selected_jdk", "auto"),
            "software_info": detect_software_info(installer.server_dir, target),
            "tunnel": tunnel_mgr.get_status(),
        }

    @app_router.post("/config")
    async def update_config(req: ConfigUpdateRequest):
        if req.properties:
            config_mgr.update_properties(req.properties)

        if req.min_ram_gb is not None:
            launch_state["min_ram_gb"] = req.min_ram_gb
        if req.max_ram_gb is not None:
            launch_state["max_ram_gb"] = req.max_ram_gb
        if req.target_jar is not None:
            launch_state["target_jar"] = req.target_jar
        if req.selected_jdk is not None:
            launch_state["selected_jdk"] = req.selected_jdk

        return {"status": "updated", "config": await get_config()}

    @app_router.get("/installer/versions")
    async def get_versions(
        server_type: str = Query("vanilla", description="vanilla, fabric, purpur, or forge"),
        include_snapshots: bool = Query(False, description="Include experimental snapshots")
    ):
        versions = await installer.get_versions(server_type=server_type, include_snapshots=include_snapshots)
        return {"server_type": server_type, "versions": versions}

    @app_router.get("/installer/installed-jars")
    async def get_installed_jars():
        jars = installer.list_installed_jars()
        return {"jars": jars}

    @app_router.post("/installer/download")
    async def download_version(req: DownloadVersionRequest):
        try:
            target_file = await installer.download_server(req.server_type, req.version)
            config_mgr.ensure_eula_accepted()
            launch_state["target_jar"] = target_file.name
            launch_state["installed_version"] = req.version
            software_info = detect_software_info(installer.server_dir, target_file.name)
            return {
                "status": "success",
                "message": f"{software_info['name']} ({req.version}) listo para iniciar",
                "target_jar": target_file.name,
                "installed_version": req.version,
                "software_info": software_info,
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
