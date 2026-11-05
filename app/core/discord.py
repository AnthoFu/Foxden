"""
Discord webhook notifier for Foxden.
Sends rich embed notifications for server events (online, stopped, crash, test).
"""

from datetime import datetime, timezone
from typing import List, Optional
import httpx


class DiscordNotifier:
    def __init__(self, webhook_url: Optional[str] = None, show_ip: bool = True) -> None:
        self.webhook_url = webhook_url.strip() if webhook_url else None
        self.show_ip = bool(show_ip)

    def is_configured(self) -> bool:
        if not self.webhook_url:
            return False
        return (
            self.webhook_url.startswith("https://discord.com/api/webhooks/")
            or self.webhook_url.startswith("https://discordapp.com/api/webhooks/")
        )

    async def send_embed(
        self,
        title: str,
        description: str,
        color: int,
        fields: Optional[List[dict]] = None,
        custom_webhook: Optional[str] = None,
    ) -> bool:
        url = custom_webhook or self.webhook_url
        if not url:
            return False

        payload = {
            "username": "Foxden 🦊",
            "avatar_url": "https://raw.githubusercontent.com/AnthoFu/foxden/main/app/static/images/foxden_icon.png",
            "embeds": [
                {
                    "title": title,
                    "description": description,
                    "color": color,
                    "fields": fields or [],
                    "footer": {
                        "text": "Foxden • Autonomous Minecraft Server Manager",
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ],
        }

        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                res = await client.post(url, json=payload)
                return res.status_code in (200, 204)
        except Exception:
            return False

    async def notify_server_online(
        self,
        software_name: str,
        version: str,
        public_ip: Optional[str] = None,
        motd: Optional[str] = None,
    ) -> bool:
        if not self.is_configured():
            return False

        fields = [
            {"name": "🎮 Motor / Versión", "value": f"`{software_name} ({version})`", "inline": True},
        ]
        if motd:
            fields.append({"name": "📜 Mensaje (MOTD)", "value": f"*{motd}*", "inline": True})

        if self.show_ip and public_ip:
            fields.append({"name": "🌐 Dirección IP para unirse", "value": f"```{public_ip}```", "inline": False})
        elif not self.show_ip:
            fields.append({"name": "🌐 Dirección IP", "value": "*Oculta por configuración de privacidad*", "inline": False})

        return await self.send_embed(
            title="🦊 ¡Servidor de Minecraft En Línea!",
            description="El servidor ha iniciado correctamente y ya está listo para recibir jugadores.",
            color=0x10B981,  # Emerald Green
            fields=fields,
        )

    async def notify_server_stopped(
        self,
        uptime_str: str,
        was_crash: bool = False,
    ) -> bool:
        if not self.is_configured():
            return False

        if was_crash:
            return await self.send_embed(
                title="⚠️ Servidor Detenido Inesperadamente",
                description="El proceso del servidor de Minecraft se cerró de forma imprevista.",
                color=0xEF4444,  # Red
                fields=[
                    {"name": "⏱️ Tiempo de actividad previo", "value": f"`{uptime_str}`", "inline": True},
                ],
            )

        return await self.send_embed(
            title="🛑 Servidor de Minecraft Detenido",
            description="El servidor se ha detenido de forma segura.",
            color=0x6B7280,  # Gray
            fields=[
                {"name": "⏱️ Tiempo total de actividad", "value": f"`{uptime_str}`", "inline": True},
            ],
        )

    async def send_test_message(
        self,
        public_ip: Optional[str] = None,
        custom_webhook: Optional[str] = None,
        custom_show_ip: Optional[bool] = None,
    ) -> bool:
        show_ip = self.show_ip if custom_show_ip is None else custom_show_ip
        fields = [
            {"name": "⚙️ Estado", "value": "Conexión con Discord establecida exitosamente.", "inline": True},
            {
                "name": "🌐 Mostrar IP en alertas",
                "value": "✅ Activado" if show_ip else "🔒 Desactivado (Privado)",
                "inline": True,
            },
        ]
        if show_ip and public_ip:
            fields.append({"name": "🔍 Ejemplo de visualización de IP", "value": f"```{public_ip}```", "inline": False})

        return await self.send_embed(
            title="🦊 ¡Prueba de Notificación de Foxden!",
            description="Si estás leyendo este mensaje, tu webhook de Discord está configurado y funcionando correctamente.",
            color=0x38BDF8,  # Sky Blue
            fields=fields,
            custom_webhook=custom_webhook,
        )
