"""
Suite de pruebas integral para Foxden.
Verifica el correcto funcionamiento de todas las funciones y módulos en español:
config, settings, discord, jdk, process, tunnel, rutas REST y frontend.
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.core.config import ConfigManager
from app.core.discord import DiscordNotifier
from app.core.installer import ServerInstaller
from app.core.jdk import JdkManager
from app.core.process import MinecraftProcess
from app.core.settings import SettingsManager
from app.core.tunnel import PlayitTunnelManager
from app.api.routes import detectar_informacion_software
from app.main import app, formatear_tiempo_activo
from run import puerto_en_uso, liberar_puerto


class TestFoxdenCore(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name)
        self.server_path = self.base_path / "servidor_minecraft"
        self.server_path.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_settings_manager_funciones_espanol(self):
        """Verifica que SettingsManager opere correctamente con nombres en español y alias."""
        mgr = SettingsManager(base_dir=self.base_path)
        # Valores por defecto
        self.assertEqual(mgr.obtener("min_ram_gb"), 2)
        self.assertEqual(mgr.get("max_ram_gb"), 4)

        # Establecer y obtener
        mgr.establecer("min_ram_gb", 6)
        self.assertEqual(mgr.obtener("min_ram_gb"), 6)
        self.assertEqual(mgr.get("min_ram_gb"), 6)

        # Actualizar
        mgr.actualizar({"max_ram_gb": 8, "discord_enabled": False})
        self.assertEqual(mgr.obtener("max_ram_gb"), 8)
        self.assertFalse(mgr.obtener("discord_enabled"))

        # Diccionario
        d = mgr.a_diccionario()
        self.assertIsInstance(d, dict)
        self.assertEqual(d["min_ram_gb"], 6)

    def test_config_manager_funciones_espanol(self):
        """Verifica la lectura, actualización y eula en ConfigManager."""
        cfg = ConfigManager(server_dir=self.server_path)

        # Asegurar eula
        cfg.asegurar_eula_aceptado()
        self.assertTrue(cfg.ruta_eula.exists())
        self.assertIn("eula=true", cfg.ruta_eula.read_text())

        # Actualizar y leer propiedades
        cfg.actualizar_propiedades({"motd": "Servidor de Prueba", "server-port": "25565", "max-players": "50"})
        props = cfg.leer_propiedades()
        self.assertEqual(props.get("motd"), "Servidor de Prueba")
        self.assertEqual(props.get("server-port"), "25565")
        self.assertEqual(props.get("max-players"), "50")

        # Resumen de ajustes
        resumen = cfg.obtener_resumen_ajustes()
        self.assertEqual(resumen["motd"], "Servidor de Prueba")
        self.assertEqual(resumen["server_port"], 25565)
        self.assertEqual(resumen["max_players"], 50)

    def test_discord_notifier_funciones_espanol(self):
        """Verifica la validación y formato de notificaciones en Discord."""
        # Sin webhook
        notif = DiscordNotifier(webhook_url="", enabled=True)
        self.assertFalse(notif.esta_configurado())

        # Con webhook inválido
        notif_invalido = DiscordNotifier(webhook_url="https://google.com", enabled=True)
        self.assertFalse(notif_invalido.esta_configurado())

        # Con webhook válido pero deshabilitado
        notif_deshab = DiscordNotifier(webhook_url="https://discord.com/api/webhooks/123/abc", enabled=False)
        self.assertFalse(notif_deshab.esta_configurado())

        # Con webhook oficial activo
        notif_activo = DiscordNotifier(webhook_url="https://discord.com/api/webhooks/123/abc", enabled=True)
        self.assertTrue(notif_activo.esta_configurado())
        self.assertTrue(notif_activo.is_configured())

    def test_jdk_manager_funciones_espanol(self):
        """Verifica el escaneo y selección inteligente de JDK."""
        jdk_mgr = JdkManager()
        jdks = jdk_mgr.listar_jdks_instalados()
        self.assertIsInstance(jdks, list)

        # Verificar selección según versión
        best_26 = jdk_mgr.obtener_mejor_jdk_para_version("26.2")
        self.assertIn("major", best_26)

        best_121 = jdk_mgr.obtener_mejor_jdk_para_version("1.21.4")
        self.assertIn("major", best_121)

        best_120 = jdk_mgr.obtener_mejor_jdk_para_version("1.20.1")
        self.assertIn("major", best_120)

        # Entorno
        env = jdk_mgr.construir_entorno_para_jdk(best_121)
        self.assertIsInstance(env, dict)

    def test_process_manager_metricas(self):
        """Verifica la inicialización y métricas de MinecraftProcess."""
        proc = MinecraftProcess(server_dir=self.server_path)
        metricas = proc.obtener_metricas()
        self.assertEqual(metricas["state"], "STOPPED")
        self.assertIsNone(metricas["pid"])
        self.assertEqual(metricas["uptime_seconds"], 0.0)

        # Suscripción a logs
        lineas = []
        cb = lambda l: lineas.append(l)
        proc.suscribir(cb)
        proc._transmitir_registro("Prueba de log")
        self.assertIn("Prueba de log", lineas)
        proc.desuscribir(cb)

    def test_tunnel_manager_estado(self):
        """Verifica el estado inicial de PlayitTunnelManager."""
        tun = PlayitTunnelManager(base_dir=self.base_path)
        estado = tun.obtener_estado()
        self.assertEqual(estado["state"], "STOPPED")
        self.assertIsNone(estado["public_address"])
        self.assertFalse(estado["has_config"])

    def test_formatear_tiempo_activo(self):
        """Verifica la conversión de segundos a formato legible."""
        self.assertEqual(formatear_tiempo_activo(45), "45s")
        self.assertEqual(formatear_tiempo_activo(125), "2m 5s")
        self.assertEqual(formatear_tiempo_activo(3700), "1h 1m")

    def test_detectar_informacion_software(self):
        """Verifica la detección automática del tipo de motor instalado."""
        # Sin motor
        info = detectar_informacion_software(self.server_path, "server.jar")
        self.assertEqual(info["type"], "none")

        # Con server.jar vanilla
        (self.server_path / "server.jar").touch()
        info_vanilla = detectar_informacion_software(self.server_path, "server.jar")
        self.assertEqual(info_vanilla["type"], "vanilla")

        # Con run.sh de NeoForge
        (self.server_path / "run.sh").write_text("#!/bin/bash\nneoforged\n")
        info_neoforge = detectar_informacion_software(self.server_path, "run.sh")
        self.assertEqual(info_neoforge["type"], "neoforge")


class TestFoxdenAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_endpoint_inicio_html(self):
        """Verifica que GET / responda 200 y sirva el HTML del frontend."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("Foxden", res.text)
        self.assertIn("root", res.text)

    def test_endpoint_status(self):
        """Verifica que GET /api/status devuelva métricas y estado del servidor."""
        res = self.client.get("/api/status")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("state", data)
        self.assertIn("cpu_percent", data)
        self.assertIn("memory_mb", data)
        self.assertIn("tunnel", data)

    def test_endpoint_jdks(self):
        """Verifica que GET /api/jdks liste los entornos Java disponibles."""
        res = self.client.get("/api/jdks")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("jdks", data)
        self.assertIsInstance(data["jdks"], list)

    def test_endpoint_tunnel_status(self):
        """Verifica que GET /api/tunnel/status informe el estado del túnel."""
        res = self.client.get("/api/tunnel/status")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("state", data)

    def test_endpoint_config_obtener_y_actualizar(self):
        """Verifica que GET /api/config y POST /api/config operen sin fallos."""
        res_get = self.client.get("/api/config")
        self.assertEqual(res_get.status_code, 200)
        data = res_get.json()
        self.assertIn("summary", data)

        res_post = self.client.post("/api/config", json={
            "properties": {"motd": "Servidor Test API"},
            "min_ram_gb": 3,
        })
        self.assertEqual(res_post.status_code, 200)
        res_data = res_post.json()
        self.assertEqual(res_data["status"], "updated")
        self.assertEqual(res_data["config"]["min_ram_gb"], 3)


if __name__ == "__main__":
    unittest.main()
