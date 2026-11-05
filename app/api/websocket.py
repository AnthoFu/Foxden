"""
WebSocket handler for live Minecraft server console.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Set
from app.core.process import MinecraftProcess

router = APIRouter()


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.discard(websocket)

    async def broadcast(self, message: str) -> None:
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except Exception:
                self.disconnect(connection)


ws_manager = ConnectionManager()


def setup_console_websocket(app_router: APIRouter, process: MinecraftProcess) -> None:
    # Forward all process logs to active WebSocket connections
    import asyncio

    def on_log_line(line: str) -> None:
        # Schedule broadcast on running event loop
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(ws_manager.broadcast(line))
        except RuntimeError:
            pass

    process.subscribe(on_log_line)

    @app_router.websocket("/ws/console")
    async def console_ws(websocket: WebSocket) -> None:
        await ws_manager.connect(websocket)
        try:
            # Send initial history
            for log_line in list(process.log_history):
                await websocket.send_text(log_line)

            # Listen for incoming commands from user terminal
            while True:
                data = await websocket.receive_text()
                if data:
                    await process.send_command(data)
        except WebSocketDisconnect:
            ws_manager.disconnect(websocket)
        except Exception:
            ws_manager.disconnect(websocket)
