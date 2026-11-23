"""
Punto de entrada de la aplicación FastAPI para Foxden.
Monta las rutas de la API, el manejador de WebSocket y sirve los activos estáticos del frontend web.
"""

from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router as api_router, configurar_rutas, detectar_informacion_software
from app.api.websocket import router as ws_router, configurar_websocket_consola
from app.core.auth import AuthManager
from app.core.config import ConfigManager
from app.core.discord import DiscordNotifier
from app.core.installer import ServerInstaller
from app.core.modrinth import ModrinthClient
from app.core.mods import ModManager
from app.core.process import MinecraftProcess
from app.core.settings import SettingsManager
from app.core.tunnel import PlayitTunnelManager
from app.version import __version__

DIRECTORIO_BASE = Path(__file__).resolve().parent.parent
DIRECTORIO_SERVIDOR = DIRECTORIO_BASE / "servidor_minecraft"
DIRECTORIO_ESTATICO = DIRECTORIO_BASE / "app" / "static"
DIST_FRONTEND = DIRECTORIO_BASE / "frontend" / "dist"

# Alias para compatibilidad
BASE_DIR = DIRECTORIO_BASE
SERVER_DIR = DIRECTORIO_SERVIDOR
STATIC_DIR = DIRECTORIO_ESTATICO
FRONTEND_DIST = DIST_FRONTEND

app = FastAPI(title="Foxden - Gestor Autónomo de Servidor Minecraft", version=__version__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instancias únicas del núcleo (Singletons)
administrador_auth = AuthManager(base_dir=DIRECTORIO_BASE)
administrador_proceso = MinecraftProcess(server_dir=DIRECTORIO_SERVIDOR)
administrador_configuracion = ConfigManager(server_dir=DIRECTORIO_SERVIDOR)
instalador = ServerInstaller(server_dir=DIRECTORIO_SERVIDOR)
administrador_mods = ModManager(server_dir=DIRECTORIO_SERVIDOR)
cliente_modrinth = ModrinthClient(server_dir=DIRECTORIO_SERVIDOR)
administrador_tunel = PlayitTunnelManager(base_dir=DIRECTORIO_BASE)
administrador_ajustes = SettingsManager(base_dir=DIRECTORIO_BASE)
notificador_discord = DiscordNotifier(
    webhook_url=administrador_ajustes.obtener("discord_webhook_url"),
    show_ip=administrador_ajustes.obtener("discord_show_ip", True),
    enabled=administrador_ajustes.obtener("discord_enabled", True),
    avatar_url=administrador_ajustes.obtener("discord_avatar_url"),
)

# Alias para compatibilidad
auth_manager = administrador_auth
process_manager = administrador_proceso
config_manager = administrador_configuracion
installer = instalador
tunnel_manager = administrador_tunel
settings_manager = administrador_ajustes
discord_notifier = notificador_discord


def formatear_tiempo_activo(segundos: float) -> str:
    """Convierte segundos en una cadena legible de tiempo activo (ej. 2h 15m)."""
    s = int(segundos)
    m = s // 60
    h = m // 60
    if h > 0:
        return f"{h}h {m % 60}m"
    if m > 0:
        return f"{m}m {s % 60}s"
    return f"{s}s"


# Alias para compatibilidad
format_uptime = formatear_tiempo_activo


async def al_estar_servidor_listo():
    """Callback ejecutado cuando Minecraft finaliza la carga y queda listo para recibir jugadores."""
    objetivo = administrador_ajustes.obtener("target_jar", "server.jar")
    info = detectar_informacion_software(instalador.server_dir, objetivo)
    propiedades = administrador_configuracion.leer_propiedades()
    motd = propiedades.get("motd", "A Minecraft Server")
    ip = administrador_tunel.public_address or administrador_ajustes.obtener("public_ip_alias")

    if administrador_tunel.state != "RUNNING":
        aviso = (
            "[Foxden] ------------------------------------------------------------------\n"
            "[Foxden] ⚠️ AVISO: El servidor de Minecraft está listo, pero el TÚNEL PÚBLICO (Playit.gg) está APAGADO.\n"
            "[Foxden] 👉 Si estás en GitHub Codespaces o en la nube, nadie podrá conectarse hasta activar el túnel desde el panel.\n"
            "[Foxden] ------------------------------------------------------------------"
        )
        administrador_proceso._transmitir_registro(aviso)

    await notificador_discord.notificar_servidor_en_linea(
        nombre_software=info["name"],
        version=administrador_ajustes.obtener("installed_version", "26.3"),
        ip_publica=ip,
        motd=motd,
        tipo_motor=info.get("type", "vanilla"),
    )


# Alias para compatibilidad
handle_server_ready = al_estar_servidor_listo


async def al_detenerse_servidor(segundos_actividad: float, codigo_retorno: int):
    """Callback ejecutado cuando el proceso de Minecraft finaliza."""
    tiempo_str = formatear_tiempo_activo(segundos_actividad)
    fue_caida = (codigo_retorno != 0)
    objetivo = administrador_ajustes.obtener("target_jar", "server.jar")
    info = detectar_informacion_software(instalador.server_dir, objetivo)
    await notificador_discord.notificar_servidor_detenido(
        tiempo_activo_str=tiempo_str,
        fue_caida=fue_caida,
        codigo_salida=codigo_retorno,
        tipo_motor=info.get("type", "vanilla"),
    )


# Alias para compatibilidad
handle_server_stopped = al_detenerse_servidor

administrador_proceso.on_server_ready = al_estar_servidor_listo
administrador_proceso.on_server_stopped = al_detenerse_servidor

# Middleware de autenticación y seguridad para /api/*
@app.middleware("http")
async def verificar_autenticacion_middleware(request: Request, call_next):
    """Protege endpoints /api/* verificando tokens de sesión activos."""
    if request.method == "OPTIONS":
        return await call_next(request)

    ruta = request.url.path
    if ruta.startswith("/api"):
        rutas_publicas = [
            "/api/auth/status",
            "/api/auth/setup",
            "/api/auth/login",
            "/api/version",
        ]
        if any(ruta == p or ruta.startswith(p + "/") for p in rutas_publicas):
            return await call_next(request)

        if administrador_auth.esta_configurado():
            auth_header = request.headers.get("Authorization", "")
            token = None
            if auth_header.startswith("Bearer "):
                token = auth_header[7:].strip()
            elif request.query_params.get("token"):
                token = request.query_params.get("token")

            if not administrador_auth.validar_token(token):
                return JSONResponse(status_code=401, content={"detail": "No autenticado. Inicie sesión."})
        else:
            return JSONResponse(
                status_code=401,
                content={"detail": "Configuración inicial de administrador requerida."},
            )

    return await call_next(request)


# Enlazar rutas y WebSocket
configurar_rutas(
    api_router,
    administrador_proceso,
    config_mgr=administrador_configuracion,
    installer=instalador,
    tunnel_mgr=administrador_tunel,
    settings_mgr=administrador_ajustes,
    discord_notifier=notificador_discord,
    mod_mgr=administrador_mods,
    modrinth_client=cliente_modrinth,
    auth_mgr=administrador_auth,
)
configurar_websocket_consola(ws_router, administrador_proceso, auth_mgr=administrador_auth)

app.include_router(api_router)
app.include_router(ws_router)

# Montar activos estáticos del frontend React compilado
if (DIST_FRONTEND / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(DIST_FRONTEND / "assets")), name="assets")

if DIRECTORIO_ESTATICO.exists():
    app.mount("/static", StaticFiles(directory=str(DIRECTORIO_ESTATICO)), name="static")


@app.get("/")
async def servir_inicio():
    """Sirve la página de inicio del frontend React o la interfaz estática."""
    if (DIST_FRONTEND / "index.html").exists():
        return FileResponse(DIST_FRONTEND / "index.html")
    if (DIRECTORIO_ESTATICO / "index.html").exists():
        return FileResponse(DIRECTORIO_ESTATICO / "index.html")
    return {"message": "Foxden API en ejecución"}


# Alias para compatibilidad
serve_index = servir_inicio


@app.get("/{ruta_completa:path}")
async def servir_spa_alternativo(ruta_completa: str):
    """Manejador alternativo para enrutamiento SPA del frontend."""
    if ruta_completa.startswith("api") or ruta_completa.startswith("ws"):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="No encontrado")

    archivo = DIST_FRONTEND / ruta_completa
    if archivo.is_file():
        return FileResponse(archivo)

    if (DIST_FRONTEND / "index.html").exists():
        return FileResponse(DIST_FRONTEND / "index.html")
    if (DIRECTORIO_ESTATICO / "index.html").exists():
        return FileResponse(DIRECTORIO_ESTATICO / "index.html")

    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="No encontrado")


# Alias para compatibilidad
serve_spa_fallback = servir_spa_alternativo


@app.on_event("shutdown")
async def al_apagar():
    """Detiene ordenadamente los procesos activos antes de cerrar la aplicación."""
    if administrador_proceso.state != "STOPPED":
        await administrador_proceso.detener(timeout=10.0)
    if administrador_tunel.state != "STOPPED":
        await administrador_tunel.detener()


# Alias para compatibilidad
on_shutdown = al_apagar
