"""
Módulo de autenticación y seguridad para Foxden.
Maneja el registro inicial del administrador, verificación de credenciales
con PBKDF2-HMAC-SHA256 y gestión de tokens de sesión activos.
"""

import hashlib
import json
import os
import secrets
import time
from pathlib import Path
from typing import Any, Dict, Optional


class AuthManager:
    """Administra la autenticación del administrador y la validación de tokens de sesión."""

    ITERACIONES = 100_000

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = Path(base_dir).resolve()
        self.auth_file = self.base_dir / "foxden_auth.json"
        self.tokens_activos: Dict[str, Dict[str, Any]] = {}  # token -> {"username": str, "created_at": float}
        self._credenciales: Optional[Dict[str, Any]] = None
        self.cargar()

    def esta_configurado(self) -> bool:
        """Indica si el sistema ya tiene un usuario administrador configurado."""
        return self._credenciales is not None and bool(self._credenciales.get("password_hash"))

    def cargar(self) -> None:
        """Carga las credenciales del archivo JSON si existe y es válido."""
        if not self.auth_file.exists():
            self._credenciales = None
            return

        try:
            contenido = self.auth_file.read_text(encoding="utf-8")
            datos = json.loads(contenido)
            if datos.get("username") and datos.get("password_hash") and datos.get("salt"):
                self._credenciales = datos
            else:
                self._credenciales = None
        except Exception:
            self._credenciales = None

    def hash_password(self, password: str, salt: bytes) -> str:
        """Deriva el hash criptográfico de la contraseña usando PBKDF2-HMAC-SHA256."""
        derivado = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            self.ITERACIONES,
        )
        return derivado.hex()

    def configurar_admin(self, username: str, password: str) -> str:
        """Registra el administrador por primera vez y devuelve un token de sesión."""
        if self.esta_configurado():
            raise RuntimeError("El administrador ya ha sido configurado previamente.")

        usr_limpio = username.strip()
        if not usr_limpio or len(usr_limpio) < 3:
            raise ValueError("El nombre de usuario debe contener al menos 3 caracteres.")
        if not password or len(password) < 4:
            raise ValueError("La contraseña debe tener al menos 4 caracteres.")

        salt = secrets.token_bytes(16)
        pwd_hash = self.hash_password(password, salt)
        datos = {
            "username": usr_limpio,
            "salt": salt.hex(),
            "password_hash": pwd_hash,
            "created_at": time.time(),
        }

        self.auth_file.write_text(json.dumps(datos, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        try:
            os.chmod(self.auth_file, 0o600)
        except Exception:
            pass

        self._credenciales = datos
        return self.crear_token(usr_limpio)

    def verificar_credenciales(self, username: str, password: str) -> bool:
        """Comprueba que el nombre de usuario y la contraseña coincidan con los guardados."""
        if not self.esta_configurado() or not self._credenciales:
            return False

        if username.strip() != self._credenciales["username"]:
            return False

        salt = bytes.fromhex(self._credenciales["salt"])
        hash_calculado = self.hash_password(password, salt)
        return secrets.compare_digest(hash_calculado, self._credenciales["password_hash"])

    def crear_token(self, username: str) -> str:
        """Genera un nuevo token seguro de sesión."""
        token = secrets.token_urlsafe(32)
        self.tokens_activos[token] = {
            "username": username,
            "created_at": time.time(),
        }
        return token

    def validar_token(self, token: Optional[str]) -> bool:
        """Verifica si un token de sesión es válido y no ha expirado."""
        if not token:
            return False

        info = self.tokens_activos.get(token)
        if not info:
            return False

        # Sesión válida por 30 días
        if time.time() - info["created_at"] > 30 * 86400:
            self.invalidar_token(token)
            return False

        return True

    def invalidar_token(self, token: str) -> None:
        """Cierra la sesión revocando el token provisto."""
        self.tokens_activos.pop(token, None)

    def obtener_usuario_de_token(self, token: Optional[str]) -> Optional[str]:
        """Obtiene el nombre de usuario asociado a un token activo."""
        if not token:
            return None
        info = self.tokens_activos.get(token)
        return info["username"] if info else None

    # Alias en inglés para compatibilidad
    is_setup_completed = esta_configurado
    setup_admin = configurar_admin
    verify_credentials = verificar_credenciales
    create_token = crear_token
    validate_token = validar_token
    invalidate_token = invalidar_token
    get_user_from_token = obtener_usuario_de_token
