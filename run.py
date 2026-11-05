#!/usr/bin/env python3
"""
Launcher script for Minecraft Server Manager.
Runs the FastAPI web server on http://localhost:8000 with auto-reload enabled.
Auto-bootstraps dependencies if running on a fresh environment.
"""

import argparse
import subprocess
import sys
from pathlib import Path

# Self-bootstrap dependencies in fresh environments (like GitHub Codespaces)
try:
    import fastapi
    import uvicorn
except ImportError:
    print("📦 Dependencias faltantes detectadas. Instalando requirements.txt automáticamente...")
    req_file = Path(__file__).resolve().parent / "requirements.txt"
    if req_file.exists():
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(req_file)])
        import fastapi
        import uvicorn
    else:
        print("❌ Error: No se encontró requirements.txt")
        sys.exit(1)


def ensure_frontend():
    base_dir = Path(__file__).resolve().parent
    frontend_dir = base_dir / "frontend"
    frontend_dist = frontend_dir / "dist"

    if frontend_dir.exists() and not (frontend_dist / "index.html").exists():
        import shutil
        npm_bin = shutil.which("npm")
        if npm_bin:
            print("📦 Compilando frontend React moderno por primera vez...")
            try:
                subprocess.check_call([npm_bin, "install"], cwd=str(frontend_dir))
                subprocess.check_call([npm_bin, "run", "build"], cwd=str(frontend_dir))
                print("✨ Frontend compilado con éxito.")
            except Exception as e:
                print(f"⚠️ Aviso: No se pudo compilar el frontend ({e}).")


def main():
    parser = argparse.ArgumentParser(description="Foxden - Autonomous Minecraft Server Manager")
    parser.add_argument("--host", default="0.0.0.0", help="Host IP to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    parser.add_argument("--no-reload", dest="reload", action="store_false", default=True, help="Disable auto-reload")
    args = parser.parse_args()

    ensure_frontend()

    print(f"🦊 Iniciando Foxden en http://localhost:{args.port} (y http://{args.host}:{args.port})")
    print("👉 Presioná Ctrl+C para detener el panel.")

    uvicorn.run("app.main:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
