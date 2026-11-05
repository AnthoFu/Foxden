"""
FastAPI application entry point.
Mounts API routes, WebSocket handler, and static assets for the web dashboard.
"""

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router as api_router, setup_routes
from app.api.websocket import router as ws_router, setup_console_websocket
from app.core.config import ConfigManager
from app.core.installer import ServerInstaller
from app.core.process import MinecraftProcess
from app.core.tunnel import PlayitTunnelManager

BASE_DIR = Path(__file__).resolve().parent.parent
SERVER_DIR = BASE_DIR / "servidor_minecraft"
STATIC_DIR = BASE_DIR / "app" / "static"

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

# In-memory launch settings
launch_state = {
    "min_ram_gb": 2,
    "max_ram_gb": 4,
    "target_jar": "server.jar" if (SERVER_DIR / "server.jar").exists() else ("run.sh" if (SERVER_DIR / "run.sh").exists() else "server.jar"),
    "installed_version": "26.3",
    "selected_jdk": "auto",
}

# Attach endpoints
setup_routes(api_router, process_manager, config_manager, installer, tunnel_manager, launch_state)
setup_console_websocket(ws_router, process_manager)

app.include_router(api_router)
app.include_router(ws_router)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def serve_index():
    return FileResponse(STATIC_DIR / "index.html")


@app.on_event("shutdown")
async def on_shutdown():
    # Gracefully stop processes if running
    if process_manager.state != "STOPPED":
        await process_manager.stop(timeout=10.0)
    if tunnel_manager.state != "STOPPED":
        await tunnel_manager.stop()
