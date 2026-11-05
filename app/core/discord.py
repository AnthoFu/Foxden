"""
Discord webhook notifier for Foxden.
Sends rich embed notifications for server events (online, stopped, crash, test).
"""

from datetime import datetime, timezone
from typing import List, Optional
import httpx

FOX_AVATAR_URL = "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f98a.png"
GREEN_DOT_ICON = "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f7e2.png"
RED_DOT_ICON = "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f534.png"
GRAY_DOT_ICON = "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/26aa.png"
TEST_TUBE_ICON = "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f9ea.png"


class DiscordNotifier:
    def __init__(
        self,
        webhook_url: Optional[str] = None,
        show_ip: bool = True,
        enabled: bool = True,
    ) -> None:
        self.webhook_url = webhook_url.strip() if webhook_url else None
        self.show_ip = bool(show_ip)
        self.enabled = bool(enabled)

    def is_configured(self) -> bool:
        if not self.enabled or not self.webhook_url:
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
        thumbnail_url: Optional[str] = None,
        custom_webhook: Optional[str] = None,
    ) -> bool:
        url = custom_webhook or self.webhook_url
        if not url:
            return False

        embed = {
            "author": {
                "name": "Foxden • Minecraft Server Manager",
                "icon_url": FOX_AVATAR_URL,
            },
            "title": title,
            "description": description,
            "color": color,
            "fields": fields or [],
            "footer": {
                "text": "Foxden 🦊 • Servidor de Minecraft",
                "icon_url": FOX_AVATAR_URL,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if thumbnail_url:
            embed["thumbnail"] = {"url": thumbnail_url}

        payload = {
            "username": "Foxden 🦊",
            "avatar_url": FOX_AVATAR_URL,
            "embeds": [embed],
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
            {"name": "🎮 Motor / Cargador", "value": f"**{software_name}**", "inline": True},
            {"name": "📦 Versión de Minecraft", "value": f"**{version}**", "inline": True},
        ]
        if motd:
            fields.append({"name": "📜 Mensaje del Día (MOTD)", "value": f"*{motd}*", "inline": False})

        if self.show_ip and public_ip:
            fields.append({
                "name": "🌐 Dirección IP para Conectarse",
                "value": f"```ini\n[ Dirección IP ]\n{public_ip}\n```\n👉 *Pega esta dirección en Minecraft > Multijugador > Conexión Directa*",
                "inline": False,
            })
        elif not self.show_ip:
            fields.append({
                "name": "🌐 Conexión al Servidor",
                "value": "🔒 *La dirección IP pública se encuentra oculta por configuración de privacidad.*",
                "inline": False,
            })

        return await self.send_embed(
            title="🟢 ¡Servidor de Minecraft En Línea!",
            description="El servidor ha iniciado con éxito y ya está listo para recibir jugadores.",
            color=0x22C55E,  # Emerald Green
            fields=fields,
            thumbnail_url=GREEN_DOT_ICON,
        )

    async def notify_server_stopped(
        self,
        uptime_str: str,
        was_crash: bool = False,
        return_code: Optional[int] = None,
    ) -> bool:
        if not self.is_configured():
            return False

        if was_crash:
            code_str = f"Código {return_code}" if return_code is not None else "Inesperado"
            return await self.send_embed(
                title="💥 Servidor Caído / Detenido Inesperadamente",
                description="⚠️ El proceso del servidor de Minecraft finalizó de manera anormal. Revisa la consola en el panel para ver el registro del error.",
                color=0xEF4444,  # Vivid Red
                fields=[
                    {"name": "⏱️ Tiempo en línea previo", "value": f"**{uptime_str}**", "inline": True},
                    {"name": "🚨 Estado de Salida", "value": f"**{code_str}**", "inline": True},
                ],
                thumbnail_url=RED_DOT_ICON,
            )

        return await self.send_embed(
            title="🛑 Servidor de Minecraft Detenido",
            description="El servidor se ha detenido y guardado de forma segura.",
            color=0x64748B,  # Slate Gray
            fields=[
                {"name": "⏱️ Tiempo total de actividad", "value": f"**{uptime_str}**", "inline": True},
                {"name": "📊 Estado", "value": "`Cerrado con éxito`", "inline": True},
            ],
            thumbnail_url=GRAY_DOT_ICON,
        )

    async def send_test_message(
        self,
        public_ip: Optional[str] = None,
        custom_webhook: Optional[str] = None,
        custom_show_ip: Optional[bool] = None,
    ) -> bool:
        show_ip = self.show_ip if custom_show_ip is None else custom_show_ip
        fields = [
            {"name": "🔔 Estado de Alertas", "value": "✅ Conexión con Discord establecida exitosamente.", "inline": True},
            {
                "name": "🔒 Privacidad de IP",
                "value": "🌐 Visible en alertas" if show_ip else "🔒 Oculta en alertas",
                "inline": True,
            },
        ]
        if show_ip and public_ip:
            fields.append({
                "name": "🔍 Ejemplo de formato de IP",
                "value": f"```ini\n[ Dirección IP ]\n{public_ip}\n```",
                "inline": False,
            })

        return await self.send_embed(
            title="🧪 Prueba de Notificación de Foxden",
            description="¡Excelente! Las notificaciones de tu servidor **Foxden** están listas y configuradas correctamente.",
            color=0x06B6D4,  # Cyan
            fields=fields,
            thumbnail_url=TEST_TUBE_ICON,
            custom_webhook=custom_webhook,
        )
