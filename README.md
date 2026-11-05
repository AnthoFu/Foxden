# Foxden 🦊

> **Autonomous Minecraft Server Manager**  
> Panel de control autónomo, moderno y liviano para desplegar y administrar servidores de Minecraft localmente o en la nube (GitHub Codespaces) sin anuncios, sin telemetría y con soberanía total.

Desarrollado por **[AnthoFu](https://github.com/AnthoFu)** (Anthony Fuentes).

---

## 🌟 Características Principales

- **🦊 Identidad & Control Total:** Sin dependencias opacas, sin acortadores de enlaces ni publicidad invasiva. Todo el código te pertenece.
- **⚡ Soporte Multi-Versión & Multi-Motor:** Descarga e instalación automática en un clic para:
  - **Mojang Vanilla** (todas las releases oficiales)
  - **Fabric Loader** (con soporte de mods)
  - **Purpur MC** (optimizado para alto rendimiento y plugins Bukkit/Paper)
  - **Minecraft Forge** (instalación automatizada con servidor de mods)
- **☕ Detección Inteligente de Java (JDK):** Escaneo dinámico de versiones instaladas (Java 17, 21 y 25) y asignación automática del entorno `JAVA_HOME`/`PATH` según el requerimiento de la versión de Minecraft.
- **🌐 Conexión Pública Integrada (Playit.gg):** Túnel TCP de baja latencia con autodescarga del binario y vinculación instantánea, permitiendo que jugadores externos se conecten a tu servidor en GitHub Codespaces sin necesidad de abrir puertos en tu router.
- **🖥️ Consola en Vivo con WebSockets:** Transmisión bidireccional en tiempo real con resaltado de sintaxis ANSI, buffer circular de registros e historial de comandos (flechas arriba/abajo).
- **⚙️ Configuración Visual:** Ajuste de propiedades (`online-mode` para cuentas No-Premium/Premium, dificultad, modo de juego, MOTD, puertos y asignación de memoria RAM JVM `-Xms` / `-Xmx`).
- **☁️ Listo para GitHub Codespaces:** Incluye `.devcontainer` optimizado para iniciar en la nube con un solo clic.

---

## 🏗️ Arquitectura del Proyecto

Construido bajo principios de arquitectura limpia y separación de responsabilidades:

```text
foxden/
├── app/
│   ├── api/          # Endpoints REST (FastAPI) y WebSocket de la consola
│   ├── core/         # Motores del dominio (Procesos, Config, Instalador, JDK, Túnel)
│   ├── static/       # Dashboard SPA oscuro (HTML5, Vanilla JS, CSS3 puro)
│   └── main.py       # Ensamblador de la aplicación FastAPI
├── servidor_minecraft/ # Directorio aislado de ejecución del servidor (ignorado en git)
├── .devcontainer/    # Configuración de contenedor para GitHub Codespaces
├── requirements.txt  # Dependencias Python
└── run.py            # CLI launcher con autoinstalación de dependencias y recarga en vivo
```

---

## 🚀 Inicio Rápido

### Opción A: En GitHub Codespaces (Recomendado)
1. Abrí este repositorio en **GitHub Codespaces**.
2. En la terminal integrada, ejecutá:
   ```bash
   python run.py
   ```
3. El puerto `8000` se abrirá automáticamente en tu navegador.
4. En la pestaña **Versiones e Instalador**, elegí tu versión favorita (ej: Vanilla, Fabric o Purpur) y hacé clic en **Descargar e Instalar**.
5. ¡Iniciá el túnel en la pestaña **Conexión Pública** y compartí la dirección con tus amigos!

### Opción B: Localmente (Linux / macOS / Windows)
1. **Cloná el repositorio:**
   ```bash
   git clone https://github.com/AnthoFu/foxden.git
   cd foxden
   ```
2. **Creá y activá tu entorno virtual:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # En Windows: .venv\Scripts\activate
   ```
3. **Iniciá Foxden:**
   ```bash
   python run.py
   ```
4. Abrí tu navegador en `http://localhost:8000`.

---

## 🦊 Créditos & Licencia

Creado con pasión por **AnthoFu**.  
Distribuido bajo licencia MIT.
