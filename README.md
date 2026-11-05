# Foxden 🦊

> **Tu servidor de Minecraft listo en minutos.**  
> Un panel web simple y moderno para crear, configurar y jugar en tu propio servidor de Minecraft con amigos desde **GitHub Codespaces** (en la nube) o desde tu computadora. ¡Sin pagar hosting y sin configuraciones complicadas!

---

## ⚡ Inicio Rápido (En 3 Pasos)

### 1. Abre el panel en GitHub Codespaces
1. Haz clic arriba en el botón verde **Code** > pestaña **Codespaces** > **Create codespace on main**.
2. Espera unos momentos a que cargue y, en la terminal que aparece abajo, escribe:
   ```bash
   python run.py
   ```
3. Se abrirá automáticamente la ventana del panel de control en tu navegador (o haz clic en **Open in Browser** en el aviso que aparece).

### 2. Elige tu versión de Minecraft
1. Ve a la pestaña **📦 Versiones e Instalador**.
2. Elige el tipo de juego que prefieras:
   - **Vanilla:** El Minecraft oficial clásico de toda la vida.
   - **NeoForge:** La opción moderna recomendada para jugar con mods (1.20.1 en adelante).
   - **Forge:** Para paquetes de mods y versiones tradicionales.
   - **Fabric:** Ideal para optimización (Sodium, Iris) y mods ligeros.
3. Elige la versión (por ejemplo `1.21.4` o `1.20.1`) y haz clic en **Descargar e Instalar**.

### 3. ¡Inicia y juega!
1. Haz clic en el botón verde **▶ Iniciar** arriba a la derecha.
2. En unos segundos tu servidor estará listo para recibir jugadores.

---

## 👥 ¿Cómo se conectan mis amigos?

Para que cualquier persona pueda entrar a tu partida desde cualquier lugar sin tener que abrir puertos en tu router:

1. Ve a la pestaña **🌐 Conexión Pública (Playit.gg)** y haz clic en **Iniciar Túnel**.
2. **La primera vez:** Haz clic en el botón amarillo para abrir tu cuenta gratuita en [playit.gg](https://playit.gg) y vincular tu servidor en unos segundos.
3. Copia la dirección que te asignen (por ejemplo: `mi-servidor.gl.joinmc.link`).
4. ¡Pásale esa dirección a tus amigos para que entren desde **Minecraft > Multijugador > Conexión Directa**!

---

## 🎮 Ajustes Populares (Pestaña Configuración)

- **Permitir cuentas no oficiales (No-Premium):** En la pestaña **⚙️ Configuración**, cambia **Tipo de Cuentas** a *Permitir No-Premium y Premium* y haz clic en **Guardar Configuración**.
- **Semilla del mundo (World Seed):** Si quieres generar un mapa específico con una semilla que te guste, escríbela en el campo **Semilla del Mundo** antes de iniciar el servidor por primera vez.
- **Darte permisos de Administrador (OP):** En la pestaña **🖥️ Consola en Vivo**, escribe:
  ```text
  op tu_nombre_en_minecraft
  ```
  y presiona **Enviar**.

---

## 🧩 ¿Cómo agregar Mods?

Si elegiste **NeoForge**, **Fabric** o **Forge**:
1. Abre la carpeta `servidor_minecraft/mods/` en el explorador de archivos de la izquierda.
2. Arrastra y suelta allí tus archivos de mods (archivos con extensión `.jar`).
3. Asegúrate de que los mods coincidan con la versión de Minecraft que instalaste.
4. Inicia o reinicia el servidor. ¡Listo!

---

## 🔔 Notificaciones en Discord (Opcional)

Si tienes un canal de Discord con tus amigos:
1. En Discord, ve a los ajustes de tu canal > **Integraciones** > **Webhooks** y crea uno nuevo.
2. Copia la URL del webhook y pégala en la pestaña **⚙️ Configuración** de Foxden.
3. Foxden avisará automáticamente en tu canal cuando el servidor esté encendido con la dirección para entrar, y avisará cuando se apague.
4. Puedes pausar o reactivar las alertas en cualquier momento con el interruptor sin tener que borrar tu URL.

---

## ❓ Preguntas Frecuentes

<details>
<summary><strong>¿Tengo que instalar Java en mi computadora?</strong></summary>
Si usas <strong>GitHub Codespaces</strong>, no tienes que instalar nada; todo viene listo y Foxden detecta y utiliza la versión de Java adecuada según la versión de Minecraft que elijas.
</details>

<details>
<summary><strong>¿Dónde se guarda mi mundo y mis construcciones?</strong></summary>
Todo tu progreso y partidas se guardan dentro de la carpeta <code>servidor_minecraft/world/</code>. Si quieres hacer una copia de seguridad, solo descarga esa carpeta.
</details>

<details>
<summary><strong>¿Cómo apago el servidor correctamente?</strong></summary>
Haz clic en el botón rojo <strong>■ Detener</strong> en el panel. Foxden guardará todo el mapa antes de cerrar el juego para que nunca pierdas nada.
</details>

---

Hecho con ❤️ por **[AnthoFu](https://github.com/AnthoFu)**.
