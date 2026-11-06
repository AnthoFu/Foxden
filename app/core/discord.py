"""
Módulo de notificaciones vía Webhook de Discord para Foxden.
Envía mensajes enriquecidos (embeds) para eventos del servidor:
encendido, apagado, caída inesperada y mensaje de prueba.
"""

from datetime import datetime, timezone
from typing import List, Optional
import httpx

URL_AVATAR_ZORRO = "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f98a.png"
ICONO_PUNTO_VERDE = "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f7e2.png"
ICONO_PUNTO_ROJO = "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f534.png"
ICONO_PUNTO_GRIS = "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/26aa.png"
ICONO_TUBO_ENSAYO = "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f9ea.png"

# Alias para compatibilidad
FOX_AVATAR_URL = URL_AVATAR_ZORRO
GREEN_DOT_ICON = ICONO_PUNTO_VERDE
RED_DOT_ICON = ICONO_PUNTO_ROJO
GRAY_DOT_ICON = ICONO_PUNTO_GRIS
TEST_TUBE_ICON = ICONO_TUBO_ENSAYO


class DiscordNotifier:
    """Administrador de notificaciones y alertas en Discord."""

    def __init__(
        self,
        webhook_url: Optional[str] = None,
        show_ip: bool = True,
        enabled: bool = True,
    ) -> None:
        self.webhook_url = webhook_url.strip() if webhook_url else None
        self.show_ip = bool(show_ip)
        self.enabled = bool(enabled)

    def esta_configurado(self) -> bool:
        """Comprueba si el webhook de Discord está activo y configurado con una URL válida."""
        if not self.enabled or not self.webhook_url:
            return False
        return (
            self.webhook_url.startswith("https://discord.com/api/webhooks/")
            or self.webhook_url.startswith("https://discordapp.com/api/webhooks/")
        )

    async def enviar_embed(
        self,
        titulo: str,
        descripcion: str,
        color: int,
        campos: Optional[List[dict]] = None,
        url_miniatura: Optional[str] = None,
        webhook_personalizado: Optional[str] = None,
    ) -> bool:
        """Construye y despacha un mensaje embebido enriquecido a la API de Discord."""
        url = webhook_personalizado or self.webhook_url
        if not url:
            return False

        embed = {
            "author": {
                "name": "Foxden • Minecraft Server Manager",
                "icon_url": URL_AVATAR_ZORRO,
            },
            "title": titulo,
            "description": descripcion,
            "color": color,
            "fields": campos or [],
            "footer": {
                "text": "Foxden 🦊 • Servidor de Minecraft",
                "icon_url": URL_AVATAR_ZORRO,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if url_miniatura:
            embed["thumbnail"] = {"url": url_miniatura}

        carga = {
            "username": "Foxden 🦊",
            "avatar_url": URL_AVATAR_ZORRO,
            "embeds": [embed],
        }

        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as cliente:
                res = await cliente.post(url, json=carga)
                return res.status_code in (200, 204)
        except Exception:
            return False

    async def notificar_servidor_en_linea(
        self,
        nombre_software: str,
        version: str,
        ip_publica: Optional[str] = None,
        motd: Optional[str] = None,
    ) -> bool:
        """Envía notificación de servidor encendido y listo para jugar."""
        if not self.esta_configurado():
            return False

        campos = [
            {"name": "🎮 Motor / Cargador", "value": f"**{nombre_software}**", "inline": True},
            {"name": "📦 Versión de Minecraft", "value": f"**{version}**", "inline": True},
        ]
        if motd:
            campos.append({"name": "📜 Mensaje del Día (MOTD)", "value": f"*{motd}*", "inline": False})

        if self.show_ip and ip_publica:
            campos.append({
                "name": "🌐 Dirección IP para Conectarse",
                "value": f"```ini\n[ Dirección IP ]\n{ip_publica}\n```\n👉 *Pega esta dirección en Minecraft > Multijugador > Conexión Directa*",
                "inline": False,
            })
        elif not self.show_ip:
            campos.append({
                "name": "🌐 Conexión al Servidor",
                "value": "🔒 *La dirección IP pública se encuentra oculta por configuración de privacidad.*",
                "inline": False,
            })

        return await self.enviar_embed(
            titulo="🟢 ¡Servidor de Minecraft En Línea!",
            descripcion="El servidor ha iniciado con éxito y ya está listo para recibir jugadores.",
            color=0x22C55E,  # Verde esmeralda
            campos=campos,
            url_miniatura=ICONO_PUNTO_VERDE,
        )

    async def notificar_servidor_detenido(
        self,
        tiempo_activo_str: str,
        fue_caida: bool = False,
        codigo_salida: Optional[int] = None,
    ) -> bool:
        """Envía notificación de servidor detenido de forma normal o por caída inesperada."""
        if not self.esta_configurado():
            return False

        if fue_caida:
            str_codigo = f"Código {codigo_salida}" if codigo_salida is not None else "Inesperado"
            return await self.enviar_embed(
                titulo="💥 Servidor Caído / Detenido Inesperadamente",
                descripcion="⚠️ El proceso del servidor de Minecraft finalizó de manera anormal. Revisa la consola en el panel para ver el registro del error.",
                color=0xEF4444,  # Rojo
                campos=[
                    {"name": "⏱️ Tiempo en línea previo", "value": f"**{tiempo_activo_str}**", "inline": True},
                    {"name": "🚨 Estado de Salida", "value": f"**{str_codigo}**", "inline": True},
                ],
                url_miniatura=ICONO_PUNTO_ROJO,
            )

        return await self.enviar_embed(
            titulo="🛑 Servidor de Minecraft Detenido",
            descripcion="El servidor se ha detenido y guardado de forma segura.",
            color=0x64748B,  # Gris
            campos=[
                {"name": "⏱️ Tiempo total de actividad", "value": f"**{tiempo_activo_str}**", "inline": True},
                {"name": "📊 Estado", "value": "`Cerrado con éxito`", "inline": True},
            ],
            url_miniatura=ICONO_PUNTO_GRIS,
        )

    async def enviar_mensaje_prueba(
        self,
        ip_publica: Optional[str] = None,
        webhook_personalizado: Optional[str] = None,
        mostrar_ip_personalizado: Optional[bool] = None,
    ) -> bool:
        """Envía un mensaje de prueba al webhook para verificar la integración."""
        mostrar_ip = self.show_ip if mostrar_ip_personalizado is None else mostrar_ip_personalizado
        campos = [
            {"name": "🔔 Estado de Alertas", "value": "✅ Conexión con Discord establecida exitosamente.", "inline": True},
            {
                "name": "🔒 Privacidad de IP",
                "value": "🌐 Visible en alertas" if mostrar_ip else "🔒 Oculta en alertas",
                "inline": True,
            },
        ]
        if mostrar_ip and ip_publica:
            campos.append({
                "name": "🔍 Ejemplo de formato de IP",
                "value": f"```ini\n[ Dirección IP ]\n{ip_publica}\n```",
                "inline": False,
            })

        return await self.enviar_embed(
            titulo="🧪 Prueba de Notificación de Foxden",
            descripcion="¡Excelente! Las notificaciones de tu servidor **Foxden** están listas y configuradas correctamente.",
            color=0x06B6D4,  # Cian
            campos=campos,
            url_miniatura=ICONO_TUBO_ENSAYO,
            webhook_personalizado=webhook_personalizado,
        )

    # Alias en inglés para compatibilidad
    is_configured = esta_configurado
    send_embed = enviar_embed
    notify_server_online = notificar_servidor_en_linea
    notify_server_stopped = notificar_servidor_detenido
    send_test_message = enviar_mensaje_prueba
