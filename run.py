#!/usr/bin/env python3
"""
Script de lanzamiento del Gestor de Servidor Minecraft Foxden.
Ejecuta el servidor web FastAPI en http://localhost:8000 con recarga automática.
Instala dependencias automáticamente en entornos nuevos.
"""

import argparse
import socket
import subprocess
import sys
import time
from pathlib import Path

# Auto-instalación de dependencias en entornos nuevos (ej. GitHub Codespaces)
try:
    import fastapi
    import uvicorn
except ImportError:
    print("📦 Dependencias faltantes detectadas. Instalando requirements.txt automáticamente...")
    archivo_req = Path(__file__).resolve().parent / "requirements.txt"
    if archivo_req.exists():
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(archivo_req)])
        import fastapi
        import uvicorn
    else:
        print("❌ Error: No se encontró requirements.txt")
        sys.exit(1)


def puerto_en_uso(puerto: int, host: str = "127.0.0.1") -> bool:
    """Comprueba si un puerto TCP específico está siendo utilizado."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, puerto)) == 0


# Alias para compatibilidad
is_port_in_use = puerto_en_uso


def liberar_puerto(puerto: int) -> bool:
    """Intenta forzar la liberación del puerto cerrando el proceso colgado con fuser."""
    import shutil
    if shutil.which("fuser"):
        res = subprocess.run(["fuser", "-k", f"{puerto}/tcp"], capture_output=True)
        return res.returncode == 0
    return False


# Alias para compatibilidad
free_port = liberar_puerto


def asegurar_frontend():
    """Compila el frontend React si existe la carpeta de fuentes pero falta la carpeta dist."""
    dir_base = Path(__file__).resolve().parent
    dir_frontend = dir_base / "frontend"
    dist_frontend = dir_frontend / "dist"

    if dir_frontend.exists() and not (dist_frontend / "index.html").exists():
        import shutil
        npm_bin = shutil.which("npm")
        if npm_bin:
            print("📦 Compilando frontend React moderno por primera vez...")
            try:
                subprocess.check_call([npm_bin, "install"], cwd=str(dir_frontend))
                subprocess.check_call([npm_bin, "run", "build"], cwd=str(dir_frontend))
                print("✨ Frontend compilado con éxito.")
            except Exception as e:
                print(f"⚠️ Aviso: No se pudo compilar el frontend ({e}).")


# Alias para compatibilidad
ensure_frontend = asegurar_frontend


def principal():
    """Punto de entrada de línea de comandos para Foxden."""
    analizador = argparse.ArgumentParser(description="Foxden - Gestor Autónomo de Servidor Minecraft")
    analizador.add_argument("--host", default="0.0.0.0", help="Dirección IP de escucha (predeterminado: 0.0.0.0)")
    analizador.add_argument("--port", type=int, default=8000, help="Puerto de escucha (predeterminado: 8000)")
    analizador.add_argument("--no-reload", dest="reload", action="store_false", default=True, help="Desactivar recarga automática")
    analizador.add_argument("--kill", "--force", dest="kill", action="store_true", help="Forzar la liberación del puerto si está ocupado")
    args = analizador.parse_args()

    asegurar_frontend()

    host_vinculacion = "127.0.0.1" if args.host == "0.0.0.0" else args.host
    if puerto_en_uso(args.port, host_vinculacion):
        if args.kill:
            print(f"🔄 Liberando puerto {args.port}...")
            liberar_puerto(args.port)
            time.sleep(0.5)
        else:
            print(f"\n⚠️ El puerto {args.port} ya está en uso por otro proceso (probablemente una instancia anterior).")
            print(f"👉 Para liberar el puerto, ejecutá en tu terminal:")
            print(f"   fuser -k {args.port}/tcp")
            print(f"👉 O ejecutá Foxden forzando la liberación:")
            print(f"   python run.py --kill")
            print(f"👉 O iniciá en otro puerto:")
            print(f"   python run.py --port {args.port + 1}\n")
            sys.exit(1)

    print(f"🦊 Iniciando Foxden en http://localhost:{args.port} (y http://{args.host}:{args.port})")
    print("👉 Presioná Ctrl+C para detener el panel.")

    uvicorn.run("app.main:app", host=args.host, port=args.port, reload=args.reload)


# Alias para compatibilidad
main = principal


if __name__ == "__main__":
    principal()
