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


def main():
    parser = argparse.ArgumentParser(description="Foxden - Autonomous Minecraft Server Manager")
    parser.add_argument("--host", default="0.0.0.0", help="Host IP to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    parser.add_argument("--no-reload", dest="reload", action="store_false", default=True, help="Disable auto-reload")
    args = parser.parse_args()

    print(f"🦊 Iniciando Foxden en http://localhost:{args.port} (y http://{args.host}:{args.port})")
    print("👉 Presioná Ctrl+C para detener el panel.")

    uvicorn.run("app.main:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
