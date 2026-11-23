"""
Manejador de WebSocket para la consola en vivo del servidor de Minecraft.
Transmite registros en tiempo real y recibe comandos desde la interfaz web.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Any, Optional, Set
from app.core.process import MinecraftProcess

router = APIRouter()


class AdministradorConexiones:
    """Gestiona el conjunto de conexiones activas por WebSocket."""

    def __init__(self) -> None:
        self.conexiones_activas: Set[WebSocket] = set()

    async def conectar(self, websocket: WebSocket) -> None:
        """Acepta y registra una nueva conexión WebSocket."""
        await websocket.accept()
        self.conexiones_activas.add(websocket)

    def desconectar(self, websocket: WebSocket) -> None:
        """Elimina una conexión WebSocket que se ha cerrado."""
        self.conexiones_activas.discard(websocket)

    async def transmitir(self, mensaje: str) -> None:
        """Difunde un mensaje de texto a todas las conexiones WebSocket conectadas."""
        for conexion in list(self.conexiones_activas):
            try:
                await conexion.send_text(mensaje)
            except Exception:
                self.desconectar(conexion)

    # Alias en inglés para compatibilidad
    connect = conectar
    disconnect = desconectar
    broadcast = transmitir


# Alias de clase para compatibilidad
ConnectionManager = AdministradorConexiones
admin_conexiones = AdministradorConexiones()
ws_manager = admin_conexiones


def configurar_websocket_consola(
    enrutador_app: APIRouter,
    proceso: MinecraftProcess,
    auth_mgr: Optional[Any] = None,
) -> None:
    """Configura la ruta /ws/console y suscribe la transmisión de logs en vivo."""
    import asyncio

    def al_recibir_linea_log(linea: str) -> None:
        # Enviar broadcast al bucle de eventos en ejecución
        try:
            bucle = asyncio.get_running_loop()
            bucle.create_task(admin_conexiones.transmitir(linea))
        except RuntimeError:
            pass

    proceso.suscribir(al_recibir_linea_log)

    @enrutador_app.websocket("/ws/console")
    async def websocket_consola(websocket: WebSocket) -> None:
        """Endpoint de WebSocket para la consola interactiva de Minecraft."""
        token = websocket.query_params.get("token")
        if auth_mgr and auth_mgr.esta_configurado():
            if not auth_mgr.validar_token(token):
                await websocket.close(code=1008, reason="No autorizado")
                return

        await admin_conexiones.conectar(websocket)
        try:
            # Enviar historial inicial de logs acumulados
            for linea_log in list(proceso.log_history):
                await websocket.send_text(linea_log)

            # Escuchar comandos enviados por el usuario desde la terminal web
            while True:
                datos = await websocket.receive_text()
                if datos:
                    await proceso.enviar_comando(datos)
        except WebSocketDisconnect:
            admin_conexiones.desconectar(websocket)
        except Exception:
            admin_conexiones.desconectar(websocket)


# Alias en inglés para compatibilidad
setup_console_websocket = configurar_websocket_consola
