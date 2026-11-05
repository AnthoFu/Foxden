# Foxden 🦊

> **Autonomous Minecraft Server Manager**  
> Panel de control autónomo, moderno y liviano para desplegar y administrar servidores de Minecraft localmente o en la nube (GitHub Codespaces) sin anuncios, sin telemetría y con soberanía total.

Desarrollado con pasión por **[AnthoFu](https://github.com/AnthoFu)** (Anthony Fuentes).

---

## 🌟 Características Principales

- **🦊 Soberanía & Control Total:** Sin herramientas opacas, sin acortadores de enlaces ni publicidad invasiva. Todo el código te pertenece.
- **⚡ Soporte Multi-Versión & Multi-Motor:** Descarga e instalación automática en un clic para:
  - **Mojang Vanilla** (todas las releases oficiales)
  - **Fabric Loader** (con soporte de mods)
  - **Purpur MC** (optimizado para alto rendimiento y plugins Bukkit/Paper)
  - **Minecraft Forge** (instalación automatizada con servidor de mods)
- **☕ Detección Inteligente de Java (JDK):** Escaneo dinámico de versiones instaladas (Java 17, 21 y 25) y asignación automática del entorno `JAVA_HOME`/`PATH` según el requerimiento de la versión de Minecraft.
- **🌐 Conexión Pública Integrada (Playit.gg):** Túnel TCP de baja latencia con autodescarga del binario y vinculación instantánea, permitiendo que jugadores externos se conecten a tu servidor en GitHub Codespaces sin necesidad de abrir puertos en tu router.
- **🖥️ Consola en Vivo con WebSockets:** Transmisión bidireccional en tiempo real con resaltado de sintaxis ANSI, buffer circular de registros en español e historial de comandos (flechas arriba/abajo).
- **⚙️ Configuración Visual:** Ajuste de propiedades (`online-mode` para cuentas No-Premium/Premium, dificultad, modo de juego, MOTD, puertos y asignación de memoria RAM JVM `-Xms` / `-Xmx`).
- **☁️ Listo para GitHub Codespaces:** Incluye `.devcontainer` optimizado para iniciar en la nube con un solo clic.

---

## 🚀 Guía Paso a Paso: De Cero a Servidor en Línea

Seguí estos simples pasos para crear tu servidor de Minecraft desde cero en **GitHub Codespaces** (o localmente):

### 1. Iniciar el Entorno
- **En GitHub Codespaces (Recomendado):**
  1. Hacé clic en el botón verde **Code** > pestaña **Codespaces** > **Create codespace on main**.
  2. Esperá unos segundos a que el contenedor se configure automáticamente.
  3. En la terminal inferior de Codespaces, iniciá el panel ejecutando:
     ```bash
     python run.py
     ```
  4. Codespaces detectará el puerto `8000` y abrirá la pestaña en tu navegador (o podés hacer clic en **Open in Browser** en la notificación).

- **Localmente (Linux / macOS / Windows):**
  ```bash
  git clone https://github.com/AnthoFu/foxden.git
  cd foxden
  python3 -m venv .venv
  source .venv/bin/activate  # En Windows: .venv\Scripts\activate
  python run.py
  ```

---

### 2. Instalar el Motor de Minecraft
1. En el panel web, andá a la pestaña **📦 Versiones e Instalador**.
2. Elegí el tipo de servidor según lo que quieras jugar:
   - **Vanilla:** Si querés jugar el Minecraft oficial tradicional sin modificaciones.
   - **Fabric:** Ideal para optimización (Sodium, Lithium) y mods modernos ligeros.
   - **Purpur:** La mejor opción para jugar con plugins (Spigot/Paper) y máxima fluidez.
   - **Forge:** Para paquetes de mods pesados tradicionales.
3. Elegí la versión que quieras (ej: `26.3`, `1.21.4`, `1.20.1`) y hacé clic en **📥 Descargar e Instalar**.
4. El panel descargará e instalará el servidor automáticamente.

---

### 3. Agregar Mods (Opcional)
Si elegiste **Fabric** o **Forge**:
1. Entrá a la carpeta `servidor_minecraft/mods/` en el explorador de archivos.
2. Subí o pegá allí tus archivos `.jar` de los mods.
   > 💡 *Asegurate de que los mods coincidan exactamente con la versión de Minecraft y el cargador elegido.*

---

### 4. Configurar las Opciones del Servidor
1. Entrá a la pestaña **⚙️ Configuración**.
2. Personalizá las opciones principales:
   - **Modo Online:** Desactivalo si vos o tus amigos usan launchers no oficiales (**No-Premium / Cracked**). Dejalo activado si todos tienen cuenta comprada de Minecraft.
   - **Memoria RAM:** Asigná la memoria mínima y máxima (recomendado para Codespaces: Mínimo 2 GB, Máximo 4 GB).
   - **Dificultad, Modo de Juego y MOTD** (mensaje de bienvenida).
3. Hacé clic en **Guardar Configuración**.

---

### 5. Iniciar el Servidor
1. En la parte superior derecha del panel, hacé clic en el botón verde **▶ Iniciar**.
2. En la pestaña **🖥️ Consola en Vivo**, verás el arranque en tiempo real hasta que aparezca:
   ```text
   [FOXDEN] ¡El servidor está EN LÍNEA y listo para recibir jugadores!
   ```
3. Si querés darte permisos de Administrador para usar comandos en el juego, escribí en la consola:
   ```text
   op tu_usuario
   ```
   y presioná **Enviar**.

---

### 6. Conectar Jugadores con Playit.gg (Túnel Público)
Para que cualquier amigo pueda entrar desde su casa sin abrir puertos:
1. Andá a la pestaña **🌐 Conexión Pública (Playit.gg)** y hacé clic en **🌐 Iniciar Túnel**.
2. **Primera vez (Vinculación):** Aparecerá un aviso amarillo con un enlace. Hacé clic para abrir tu cuenta gratuita en [playit.gg](https://playit.gg) y vincular tu agente en 10 segundos.
3. Una vez conectado, el estado cambiará a **🟢 ONLINE**.
4. Consultá tu IP pública asignada en tu cuenta de [playit.gg/manage/tunnels](https://playit.gg/manage/tunnels) (por ejemplo: `mi-servidor.gl.joinmc.link`).
5. Pegá esa IP en la cajita del panel para tenerla siempre a mano y poder copiarla con un clic.
6. ¡Pasale esa dirección a tus amigos para que se conecten desde: **Minecraft > Multijugador > Conexión Directa**!

---

## 🏗️ Estructura del Proyecto

```text
foxden/
├── app/
│   ├── api/          # Endpoints REST (FastAPI) y WebSocket de la consola
│   ├── core/         # Motores del dominio (Procesos, Config, Instalador, JDK, Túnel)
│   ├── static/       # Dashboard SPA oscuro (HTML5, Vanilla JS, CSS3 puro)
│   └── main.py       # Ensamblador de la aplicación FastAPI
├── servidor_minecraft/
│   ├── mods/         # Carpeta lista para colocar tus mods (.jar)
│   └── .gitkeep      # Directorio aislado de ejecución del servidor (datos ignorados en git)
├── .devcontainer/    # Configuración de contenedor lista para GitHub Codespaces
├── requirements.txt  # Dependencias Python mínimas
└── run.py            # CLI launcher con autoinstalación de dependencias y recarga en vivo
```

---

## ❓ Preguntas Frecuentes & Consejos

<details>
<summary><strong>¿Qué versión de Java necesito tener instalada?</strong></summary>
Foxden cuenta con un administrador inteligente de JDKs que detecta automáticamente si tu versión de Minecraft necesita Java 17, Java 21 o Java 25, y configura las variables de entorno sin que tengas que cambiar nada manualmente.
</details>

<details>
<summary><strong>¿Dónde se guardan el mapa y las partidas?</strong></summary>
Todos los datos de tu mundo se generan dentro de <code>servidor_minecraft/world/</code>. Si querés hacer un backup manual, podés descargar esa carpeta.
</details>

<details>
<summary><strong>¿Cómo detengo el servidor de forma segura?</strong></summary>
Hacé clic en el botón rojo <strong>■ Detener</strong> en el panel. Foxden enviará el comando <code>stop</code> a Minecraft y esperará a que todos los bloques y chunks se guarden en el disco antes de cerrar el proceso, evitando cualquier corrupción de datos.
</details>

---

## 🦊 Créditos & Licencia

Creado con pasión por **[AnthoFu](https://github.com/AnthoFu)**.  
Distribuido bajo licencia MIT.
