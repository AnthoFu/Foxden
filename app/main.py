"""
FastAPI application entry point.
Mounts API routes, WebSocket handler, and static assets for the web dashboard.
"""

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router as api_router, setup_routes, detect_software_info
from app.api.websocket import router as ws_router, setup_console_websocket
from app.core.config import ConfigManager
from app.core.discord import DiscordNotifier
from app.core.installer import ServerInstaller
from app.core.process import MinecraftProcess
from app.core.settings import SettingsManager
from app.core.tunnel import PlayitTunnelManager

BASE_DIR = Path(__file__).resolve().parent.parent
SERVER_DIR = BASE_DIR / "servidor_minecraft"
STATIC_DIR = BASE_DIR / "app" / "static"
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"

app = FastAPI(title="Foxden - Autonomous Minecraft Server Manager", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core singletons
process_manager = MinecraftProcess(server_dir=SERVER_DIR)
config_manager = ConfigManager(server_dir=SERVER_DIR)
installer = ServerInstaller(server_dir=SERVER_DIR)
tunnel_manager = PlayitTunnelManager(base_dir=BASE_DIR)
settings_manager = SettingsManager(base_dir=BASE_DIR)
discord_notifier = DiscordNotifier(
    webhook_url=settings_manager.get("discord_webhook_url"),
    show_ip=settings_manager.get("discord_show_ip", True),
    enabled=settings_manager.get("discord_enabled", True),
)


def format_uptime(seconds: float) -> str:
    s = int(seconds)
    m = s // 60
    h = m // 60
    if h > 0:
        return f"{h}h {m % 60}m"
    if m > 0:
        return f"{m}m {s % 60}s"
    return f"{s}s"


async def handle_server_ready():
    target = settings_manager.get("target_jar", "server.jar")
    info = detect_software_info(installer.server_dir, target)
    props = config_manager.read_properties()
    motd = props.get("motd", "A Minecraft Server")
    ip = tunnel_manager.public_address or settings_manager.get("public_ip_alias")

    if tunnel_manager.state != "RUNNING":
        notice = (
            "[Foxden] ------------------------------------------------------------------\n"
            "[Foxden] ⚠️ AVISO: El servidor de Minecraft está listo, pero el TÚNEL PÚBLICO (Playit.gg) está APAGADO.\n"
            "[Foxden] 👉 Si estás en GitHub Codespaces o en la nube, nadie podrá conectarse hasta activar el túnel desde el panel.\n"
            "[Foxden] ------------------------------------------------------------------"
        )
        process_manager._broadcast_log(notice)

    await discord_notifier.notify_server_online(
        software_name=info["name"],
        version=settings_manager.get("installed_version", "26.3"),
        public_ip=ip,
        motd=motd,
    )


async def handle_server_stopped(uptime_seconds: float, return_code: int):
    uptime_str = format_uptime(uptime_seconds)
    was_crash = (return_code != 0)
    await discord_notifier.notify_server_stopped(
        uptime_str=uptime_str,
        was_crash=was_crash,
        return_code=return_code,
    )


process_manager.on_server_ready = handle_server_ready
process_manager.on_server_stopped = handle_server_stopped

# Attach endpoints
setup_routes(
    api_router,
    process_manager,
    config_mgr=config_manager,
    installer=installer,
    tunnel_mgr=tunnel_manager,
    settings_mgr=settings_manager,
    discord_notifier=discord_notifier,
)
setup_console_websocket(ws_router, process_manager)

app.include_router(api_router)
app.include_router(ws_router)

# Mount static files & modern frontend assets
if (FRONTEND_DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def serve_index():
    if (FRONTEND_DIST / "index.html").exists():
        return FileResponse(FRONTEND_DIST / "index.html")
    if (STATIC_DIR / "index.html").exists():
        return FileResponse(STATIC_DIR / "index.html")
    return {"message": "Foxden API running"}


@app.get("/{full_path:path}")
async def serve_spa_fallback(full_path: str):
    if full_path.startswith("api") or full_path.startswith("ws"):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Not Found")

    file_path = FRONTEND_DIST / full_path
    if file_path.is_file():
        return FileResponse(file_path)

    if (FRONTEND_DIST / "index.html").exists():
        return FileResponse(FRONTEND_DIST / "index.html")
    if (STATIC_DIR / "index.html").exists():
        return FileResponse(STATIC_DIR / "index.html")
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="Not Found")


@app.on_event("shutdown")
async def on_shutdown():
    # Gracefully stop processes if running
    if process_manager.state != "STOPPED":
        await process_manager.stop(timeout=10.0)
    if tunnel_manager.state != "STOPPED":
        await tunnel_manager.stop()
