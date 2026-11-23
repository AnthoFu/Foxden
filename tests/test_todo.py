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

from app.core.auth import AuthManager
from app.core.config import ConfigManager
from app.core.discord import DiscordNotifier
from app.core.installer import ServerInstaller
from app.core.jdk import JdkManager
from app.core.process import MinecraftProcess
from app.core.settings import SettingsManager
from app.core.tunnel import PlayitTunnelManager
from app.api.routes import detectar_informacion_software
from app.main import app, formatear_tiempo_activo, administrador_auth
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

        # Verificar que si existe Java 27 experimental, NO se elija para 1.21 o 1.20
        jdks_simulados = [
            {"major": 27, "path": "/usr/lib/jvm/java-27/bin/java", "name": "Java 27", "home": "/usr/lib/jvm/java-27"},
            {"major": 21, "path": "/usr/lib/jvm/java-21/bin/java", "name": "Java 21", "home": "/usr/lib/jvm/java-21"},
            {"major": 17, "path": "/usr/lib/jvm/java-17/bin/java", "name": "Java 17", "home": "/usr/lib/jvm/java-17"},
        ]
        with patch.object(jdk_mgr, "listar_jdks_instalados", return_value=jdks_simulados):
            elegido_121 = jdk_mgr.obtener_mejor_jdk_para_version("1.21.1")
            self.assertEqual(elegido_121["major"], 21)

            elegido_120 = jdk_mgr.obtener_mejor_jdk_para_version("1.20.1")
            self.assertEqual(elegido_120["major"], 17)

        # Si no hay Java 17 pero sí 21 y 27, para 1.20 debe preferir Java 21 antes que Java 27
        jdks_sin_17 = [
            {"major": 27, "path": "/usr/lib/jvm/java-27/bin/java", "name": "Java 27", "home": "/usr/lib/jvm/java-27"},
            {"major": 21, "path": "/usr/lib/jvm/java-21/bin/java", "name": "Java 21", "home": "/usr/lib/jvm/java-21"},
        ]
        with patch.object(jdk_mgr, "listar_jdks_instalados", return_value=jdks_sin_17):
            elegido_fallback = jdk_mgr.obtener_mejor_jdk_para_version("1.20.1")
            self.assertEqual(elegido_fallback["major"], 21)

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

    def test_auth_manager_hashing_y_sesiones(self):
        """Verifica la lógica criptográfica de contraseñas y sesiones en AuthManager."""
        auth = AuthManager(base_dir=self.base_path)
        self.assertFalse(auth.esta_configurado())

        # Validación de longitud mínima
        with self.assertRaises(ValueError):
            auth.configurar_admin("ad", "12345")
        with self.assertRaises(ValueError):
            auth.configurar_admin("admin", "12")

        # Configuración inicial exitosa
        token = auth.configurar_admin("operador", "secreto123")
        self.assertTrue(auth.esta_configurado())
        self.assertTrue(auth.validar_token(token))
        self.assertEqual(auth.obtener_usuario_de_token(token), "operador")

        # Comprobación de credenciales
        self.assertTrue(auth.verificar_credenciales("operador", "secreto123"))
        self.assertFalse(auth.verificar_credenciales("operador", "clave_incorrecta"))
        self.assertFalse(auth.verificar_credenciales("otro", "secreto123"))

        # Invalidez de tokens
        self.assertFalse(auth.validar_token("token_inexistente"))
        auth.invalidar_token(token)
        self.assertFalse(auth.validar_token(token))

        # Intento de reconfigurar administrador debe fallar
        with self.assertRaises(RuntimeError):
            auth.configurar_admin("nuevo", "otra_clave")

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

        # Caso crítico: residuos de NeoForge en disco pero con Vanilla instalado
        (self.server_path / "libraries" / "net" / "neoforged").mkdir(parents=True, exist_ok=True)
        info_con_residuos = detectar_informacion_software(
            self.server_path,
            "server.jar",
            motor_instalado="vanilla",
        )
        self.assertEqual(info_con_residuos["type"], "vanilla")
        self.assertEqual(info_con_residuos["name"], "Minecraft Vanilla (Oficial)")


class TestFoxdenAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.temp_auth_file = Path(cls.temp_dir.name) / "test_auth.json"

        # Aislar auth manager
        cls._orig_auth_file = administrador_auth.auth_file
        cls._orig_cred = administrador_auth._credenciales
        cls._orig_tokens = administrador_auth.tokens_activos.copy()

        administrador_auth.auth_file = cls.temp_auth_file
        administrador_auth._credenciales = None
        administrador_auth.tokens_activos.clear()

        cls.client = TestClient(app)
        cls.auth_headers = {}

    @classmethod
    def tearDownClass(cls):
        administrador_auth.auth_file = cls._orig_auth_file
        administrador_auth._credenciales = cls._orig_cred
        administrador_auth.tokens_activos = cls._orig_tokens
        cls.temp_dir.cleanup()

    def test_01_flujo_autenticacion_y_proteccion(self):
        """Verifica el flujo completo de primer arranque, login y rechazo de no autenticados."""
        # 1. Estado inicial: requiere setup
        res = self.client.get("/api/auth/status")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["setup_required"])
        self.assertFalse(res.json()["authenticated"])

        # 2. Endpoints protegidos devuelven 401 si no está configurado
        res_bloq = self.client.get("/api/status")
        self.assertEqual(res_bloq.status_code, 401)

        # 3. Primer arranque: configurar admin
        res_setup = self.client.post("/api/auth/setup", json={
            "username": "admin_test",
            "password": "clave_segura_123",
        })
        self.assertEqual(res_setup.status_code, 200)
        datos_setup = res_setup.json()
        self.assertEqual(datos_setup["status"], "success")
        self.assertIn("token", datos_setup)
        TestFoxdenAPI.auth_token = datos_setup["token"]
        TestFoxdenAPI.auth_headers = {"Authorization": f"Bearer {TestFoxdenAPI.auth_token}"}

        # 4. Intentar reconfigurar debe dar 409
        res_reconf = self.client.post("/api/auth/setup", json={
            "username": "otro",
            "password": "password",
        })
        self.assertEqual(res_reconf.status_code, 409)

        # 5. Login con clave errónea
        res_login_bad = self.client.post("/api/auth/login", json={
            "username": "admin_test",
            "password": "clave_equivocada",
        })
        self.assertEqual(res_login_bad.status_code, 401)

        # 6. Login exitoso
        res_login_ok = self.client.post("/api/auth/login", json={
            "username": "admin_test",
            "password": "clave_segura_123",
        })
        self.assertEqual(res_login_ok.status_code, 200)
        self.assertIn("token", res_login_ok.json())

        # 7. Validar estado con token activo
        res_auth_ok = self.client.get("/api/auth/status", headers=self.auth_headers)
        self.assertEqual(res_auth_ok.status_code, 200)
        self.assertFalse(res_auth_ok.json()["setup_required"])
        self.assertTrue(res_auth_ok.json()["authenticated"])
        self.assertEqual(res_auth_ok.json()["username"], "admin_test")

    def test_endpoint_inicio_html(self):
        """Verifica que GET / responda 200 y sirva el HTML del frontend."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("Foxden", res.text)
        self.assertIn("root", res.text)

    def test_endpoint_status(self):
        """Verifica que GET /api/status devuelva métricas y estado del servidor con auth."""
        res = self.client.get("/api/status", headers=self.auth_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("state", data)
        self.assertIn("cpu_percent", data)
        self.assertIn("memory_mb", data)
        self.assertIn("tunnel", data)

    def test_endpoint_jdks(self):
        """Verifica que GET /api/jdks liste los entornos Java disponibles."""
        res = self.client.get("/api/jdks", headers=self.auth_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("jdks", data)
        self.assertIsInstance(data["jdks"], list)

    def test_endpoint_tunnel_status(self):
        """Verifica que GET /api/tunnel/status informe el estado del túnel."""
        res = self.client.get("/api/tunnel/status", headers=self.auth_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("state", data)

    def test_endpoint_config_obtener_y_actualizar(self):
        """Verifica que GET /api/config y POST /api/config operen sin fallos."""
        res_get = self.client.get("/api/config", headers=self.auth_headers)
        self.assertEqual(res_get.status_code, 200)
        data = res_get.json()
        self.assertIn("summary", data)

        res_post = self.client.post("/api/config", headers=self.auth_headers, json={
            "properties": {"motd": "Servidor Test API"},
            "min_ram_gb": 3,
        })
        self.assertEqual(res_post.status_code, 200)
        res_data = res_post.json()
        self.assertEqual(res_data["status"], "updated")
        self.assertEqual(res_data["config"]["min_ram_gb"], 3)

    def test_endpoint_neoforge_builds(self):
        """Verifica que el endpoint /api/installer/neoforge-builds devuelva las compilaciones de Maven."""
        res = self.client.get("/api/installer/neoforge-builds?mc_version=1.21.1", headers=self.auth_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["mc_version"], "1.21.1")
        self.assertIn("builds", data)
        self.assertIsInstance(data["builds"], list)
        self.assertTrue(len(data["builds"]) > 0)
        # La build 21.1.218 debe figurar en el catálogo de 1.21.1
        self.assertIn("21.1.218", data["builds"])

    def test_zz_endpoint_auth_logout(self):
        """Verifica que cerrar sesión invalide el token inmediatamente."""
        res_logout = self.client.post("/api/auth/logout", headers=self.auth_headers)
        self.assertEqual(res_logout.status_code, 200)

        # Ahora el token revocado ya no permite acceder
        res_verif = self.client.get("/api/status", headers=self.auth_headers)
        self.assertEqual(res_verif.status_code, 401)


if __name__ == "__main__":
    unittest.main()
