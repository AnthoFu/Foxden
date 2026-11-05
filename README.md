# Foxden 🦊

> **Autonomous Minecraft Server Manager**  
> Panel de control autónomo, moderno y ligero para desplegar y administrar servidores de Minecraft localmente o en la nube (GitHub Codespaces) sin anuncios, sin telemetría y con soberanía total.

Desarrollado con pasión por **[AnthoFu](https://github.com/AnthoFu)** (Anthony Fuentes).

---

## 🌟 Características Principales

- **🦊 Soberanía y Control Total:** Sin herramientas opacas, sin acortadores de enlaces ni publicidad invasiva. Todo el código te pertenece.
- **⚡ Soporte Multi-Versión y Multi-Motor:** Descarga e instalación automática en un solo clic para:
  - **Mojang Vanilla** (todas las versiones oficiales de lanzamiento)
  - **Fabric Loader** (con soporte para mods modernos)
  - **Purpur MC** (optimizado para alto rendimiento y plugins Bukkit/Paper)
  - **Minecraft Forge** (instalación automatizada para servidores con mods)
- **☕ Detección Inteligente de Java (JDK):** Escaneo dinámico de versiones instaladas (Java 17, 21 y 25) y configuración automática de `JAVA_HOME` y `PATH` según los requerimientos de la versión de Minecraft elegida.
- **🌐 Conexión Pública Integrada (Playit.gg):** Túnel TCP de baja latencia con descarga automática del agente y vinculación rápida, permitiendo que tus amigos se conecten a tu servidor en GitHub Codespaces sin necesidad de abrir puertos en el router.
- **🖥️ Consola en Vivo con WebSockets:** Transmisión bidireccional en tiempo real con resaltado de sintaxis ANSI, buffer circular de registros y navegación de historial de comandos (flechas arriba/abajo).
- **🔔 Alertas por Webhook de Discord:** Notificaciones automáticas con embeds enriquecidos cuando el servidor se enciende o se apaga, con opción para mostrar u ocultar la IP pública por privacidad y botón de prueba integrado.
- **⚙️ Configuración Visual:** Ajuste de propiedades (`online-mode` para cuentas No-Premium y Premium, dificultad, modo de juego, MOTD, puertos y asignación de memoria RAM JVM `-Xms` / `-Xmx`).
- **☁️ Listo para GitHub Codespaces:** Incluye `.devcontainer` optimizado para iniciar en la nube con un solo clic.

---

## 🚀 Guía Paso a Paso: De Cero a Servidor en Línea

Sigue estos sencillos pasos para crear tu servidor de Minecraft desde cero en **GitHub Codespaces** (o en tu computadora):

### 1. Iniciar el Entorno
- **En GitHub Codespaces (Recomendado):**
  1. Haz clic en el botón verde **Code** > pestaña **Codespaces** > **Create codespace on main**.
  2. Espera unos segundos a que el contenedor termine de configurarse.
  3. En la terminal integrada de Codespaces, inicia el panel ejecutando:
     ```bash
     python run.py
     ```
  4. Codespaces detectará el puerto `8000` y abrirá la pestaña automáticamente en tu navegador (también puedes hacer clic en **Open in Browser** en la notificación inferior).

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
1. En el panel web, ve a la pestaña **📦 Versiones e Instalador**.
2. Elige el tipo de servidor según lo que quieras jugar:
   - **Vanilla:** Si quieres jugar el Minecraft oficial clásico sin modificaciones.
   - **Fabric:** Ideal para optimización (Sodium, Lithium, Iris) y mods modernos ligeros.
   - **Purpur:** La mejor opción para jugar con plugins (Spigot/Paper) y máxima fluidez.
   - **Forge:** Para paquetes de mods tradicionales pesados.
3. Elige la versión que quieras (por ejemplo: `26.3`, `1.21.4`, `1.20.1`) y haz clic en **📥 Descargar e Instalar**.
4. El panel descargará e instalará el servidor de forma automática.

---

### 3. Agregar Mods (Opcional)
Si elegiste **Fabric** o **Forge**:
1. Entra en la carpeta `servidor_minecraft/mods/` desde el explorador de archivos de Codespaces o de tu sistema.
2. Sube o pega allí tus archivos de mods con extensión `.jar`.
   > 💡 *Asegúrate de que los mods coincidan exactamente con la versión de Minecraft y con el cargador seleccionado.*

---

### 4. Configurar las Opciones del Servidor
1. Entra en la pestaña **⚙️ Configuración**.
2. Personaliza las opciones principales:
   - **Modo Online:** Desactívalo si tú o tus amigos usan launchers no oficiales (**No-Premium / Cracked**). Déjalo activado si todos juegan con cuenta oficial comprada de Minecraft.
   - **Memoria RAM:** Asigna la memoria mínima y máxima (recomendado para Codespaces: Mínimo 2 GB, Máximo 4 GB).
   - **Dificultad, Modo de Juego y MOTD** (mensaje de bienvenida en la lista de servidores).
3. Haz clic en **Guardar Configuración**.

---

### 5. Iniciar el Servidor
1. En la esquina superior derecha del panel, haz clic en el botón verde **▶ Iniciar**.
2. En la pestaña **🖥️ Consola en Vivo**, verás la carga del mapa en tiempo real hasta que aparezca el mensaje:
   ```text
   [FOXDEN] ¡El servidor está EN LÍNEA y listo para recibir jugadores!
   ```
3. Si quieres darte permisos de Administrador para usar comandos en el juego, escribe en la consola:
   ```text
   op tu_usuario
   ```
   y presiona **Enviar**.

---

### 6. Conectar Jugadores con Playit.gg (Túnel Público)
Para que cualquier persona pueda entrar al servidor desde cualquier parte del mundo sin abrir puertos:
1. Ve a la pestaña **🌐 Conexión Pública (Playit.gg)** y haz clic en **🌐 Iniciar Túnel**.
2. **Primera vez (Vinculación):** Aparecerá un aviso con un botón amarillo. Haz clic para abrir tu cuenta gratuita en [playit.gg](https://playit.gg) y vincular el agente en unos segundos.
3. Una vez conectado, el estado cambiará a **🟢 ONLINE**.
4. Consulta tu dirección pública asignada en tu cuenta de [playit.gg/manage/tunnels](https://playit.gg/manage/tunnels) (por ejemplo: `mi-servidor.gl.joinmc.link`).
5. Pega esa dirección en el campo del panel para tenerla siempre guardada y copiarla con un solo clic.
6. ¡Comparte esa dirección con tus amigos para que se conecten desde: **Minecraft > Multijugador > Conexión Directa**!

---

## 🏗️ Estructura del Proyecto

```text
foxden/
├── app/
│   ├── api/          # Endpoints REST (FastAPI) y WebSocket de la consola
│   ├── core/         # Motores del dominio (Procesos, Configuración, Instalador, JDK, Túnel)
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

## ❓ Preguntas Frecuentes y Consejos

<details>
<summary><strong>¿Qué versión de Java necesito tener instalada?</strong></summary>
Foxden cuenta con un administrador inteligente de JDKs que detecta automáticamente si tu versión de Minecraft necesita Java 17, Java 21 o Java 25, y configura las variables de entorno sin que tengas que ajustar nada manualmente.
</details>

<details>
<summary><strong>¿Dónde se guardan el mapa y las partidas?</strong></summary>
Todos los datos de tu mundo se generan dentro de <code>servidor_minecraft/world/</code>. Si quieres hacer una copia de seguridad manual, solo descarga esa carpeta.
</details>

<details>
<summary><strong>¿Cómo detengo el servidor de forma segura?</strong></summary>
Haz clic en el botón rojo <strong>■ Detener</strong> en el panel. Foxden enviará el comando <code>stop</code> a Minecraft y esperará a que todos los bloques y chunks se guarden en el disco antes de cerrar el proceso, evitando cualquier pérdida o corrupción de datos.
</details>

---

## 🦊 Créditos y Licencia

Creado con pasión por **[AnthoFu](https://github.com/AnthoFu)**.  
Distribuido bajo licencia MIT.
