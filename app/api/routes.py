"""
Rutas de la API REST para el panel de administración de Foxden.
Provee endpoints para estado del servidor, consola, configuración, instalador,
túnel público de Playit y alertas de Discord.
"""

from pathlib import Path
from typing import Dict, List, Optional
from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field

from app.core.config import ConfigManager
from app.core.discord import DiscordNotifier
from app.core.installer import ServerInstaller
from app.core.jdk import JdkManager
from app.core.modrinth import ModrinthClient
from app.core.mods import ModManager
from app.core.process import MinecraftProcess
from app.core.settings import SettingsManager
from app.core.tunnel import PlayitTunnelManager
from app.version import __version__

router = APIRouter(prefix="/api")


class CommandRequest(BaseModel):
    """Esquema de solicitud para ejecutar un comando en la consola de Minecraft."""
    command: str = Field(..., description="Comando para la consola de Minecraft")


class ConfigUpdateRequest(BaseModel):
    """Esquema de solicitud para actualizar la configuración de Foxden y server.properties."""
    properties: Dict[str, str] = Field(default_factory=dict)
    min_ram_gb: Optional[int] = Field(default=None, ge=1, le=64)
    max_ram_gb: Optional[int] = Field(default=None, ge=1, le=64)
    target_jar: Optional[str] = Field(default=None)
    installed_engine: Optional[str] = Field(default=None)
    selected_jdk: Optional[str] = Field(default=None)
    discord_enabled: Optional[bool] = Field(default=None)
    discord_webhook_url: Optional[str] = Field(default=None)
    discord_show_ip: Optional[bool] = Field(default=None)
    public_ip_alias: Optional[str] = Field(default=None)


class DiscordTestRequest(BaseModel):
    """Esquema de solicitud para probar el envío de webhook a Discord."""
    webhook_url: Optional[str] = Field(default=None)
    show_ip: Optional[bool] = Field(default=None)


class DownloadVersionRequest(BaseModel):
    """Esquema de solicitud para descargar e instalar una versión de Minecraft."""
    server_type: str = Field(default="vanilla", description="vanilla, fabric, forge o neoforge")
    version: str = Field(..., description="Identificador de versión de Minecraft, ej. 26.2, 1.21.4")


class ModToggleRequest(BaseModel):
    """Esquema de solicitud para activar o desactivar un mod."""
    filename: str = Field(..., description="Nombre del archivo mod, ej. jei-1.20.1.jar")
    enabled: bool = Field(..., description="True para activar, False para desactivar")


class ModrinthInstallRequest(BaseModel):
    """Esquema de solicitud para descargar e instalar un mod desde Modrinth."""
    project_id: str = Field(..., description="ID o slug del proyecto en Modrinth")
    version_id: Optional[str] = Field(default=None, description="ID específico de la versión a instalar")
    loader: Optional[str] = Field(default=None, description="Cargador (fabric, forge, neoforge)")
    game_version: Optional[str] = Field(default=None, description="Versión de Minecraft")
    install_dependencies: bool = Field(default=True, description="Instalar automáticamente dependencias requeridas")


def detectar_informacion_software(
    directorio_servidor: Path,
    archivo_objetivo: str,
    motor_instalado: Optional[str] = None,
) -> dict:
    """Detecta el motor y la configuración activa del servidor de Minecraft instalado."""
    tiene_run_sh = (directorio_servidor / "run.sh").exists()
    tiene_objetivo = (directorio_servidor / archivo_objetivo).exists() if archivo_objetivo else False
    tiene_algun_jar = any(p.is_file() and not p.name.endswith("installer.jar") for p in directorio_servidor.glob("*.jar")) if directorio_servidor.exists() else False

    if not tiene_run_sh and not tiene_objetivo and not tiene_algun_jar:
        return {
            "name": "Sin motor instalado",
            "icon": "📦",
            "type": "none",
            "runner": "Ninguno",
            "description": "Aún no has instalado ningún motor de Minecraft. Ve a 'Versiones e Instalador' para descargar uno.",
        }

    motor = (motor_instalado or "").lower().strip()

    # Si se conoce explícitamente el motor instalado, se respeta con máxima prioridad
    if motor == "vanilla":
        return {
            "name": "Minecraft Vanilla (Oficial)",
            "icon": "🌱",
            "type": "vanilla",
            "runner": archivo_objetivo if archivo_objetivo else "server.jar",
            "description": "Servidor oficial de Mojang sin modificaciones",
        }
    elif motor == "neoforge":
        return {
            "name": "NeoForge",
            "icon": "🔥",
            "type": "neoforge",
            "runner": archivo_objetivo if archivo_objetivo else "run.sh",
            "description": "Servidor moderno para mods de NeoForge (ejecuta run.sh)",
        }
    elif motor == "fabric":
        return {
            "name": "Fabric Loader",
            "icon": "🧵",
            "type": "fabric",
            "runner": archivo_objetivo if archivo_objetivo else "server.jar",
            "description": "Servidor con soporte para mods de Fabric",
        }
    elif motor == "forge":
        return {
            "name": "Minecraft Forge",
            "icon": "🔨",
            "type": "forge",
            "runner": archivo_objetivo if archivo_objetivo else "run.sh",
            "description": "Servidor con soporte para mods de Forge (ejecuta run.sh)",
        }

    # Inferencia secundaria basada en el archivo_objetivo activo
    objetivo_minus = (archivo_objetivo or "").lower()

    if archivo_objetivo == "run.sh" or (tiene_run_sh and not tiene_objetivo):
        es_neoforge = False
        if (directorio_servidor / "run.sh").exists():
            try:
                contenido = (directorio_servidor / "run.sh").read_text(errors="ignore")
                if "neoforged" in contenido or "neoforge" in contenido:
                    es_neoforge = True
            except Exception:
                pass

        if es_neoforge:
            return {
                "name": "NeoForge",
                "icon": "🔥",
                "type": "neoforge",
                "runner": "run.sh",
                "description": "Servidor moderno para mods de NeoForge (ejecuta run.sh)",
            }
        return {
            "name": "Minecraft Forge",
            "icon": "🔨",
            "type": "forge",
            "runner": "run.sh",
            "description": "Servidor con soporte para mods de Forge (ejecuta run.sh)",
        }

    if "fabric" in objetivo_minus or (directorio_servidor / ".fabric").exists():
        return {
            "name": "Fabric Loader",
            "icon": "🧵",
            "type": "fabric",
            "runner": archivo_objetivo if archivo_objetivo else "server.jar",
            "description": "Servidor con soporte para mods de Fabric",
        }

    if "forge" in objetivo_minus:
        return {
            "name": "Minecraft Forge",
            "icon": "🔨",
            "type": "forge",
            "runner": archivo_objetivo,
            "description": "Servidor con soporte para mods de Forge",
        }

    if "neoforge" in objetivo_minus:
        return {
            "name": "NeoForge",
            "icon": "🔥",
            "type": "neoforge",
            "runner": archivo_objetivo,
            "description": "Servidor moderno para mods de NeoForge",
        }

    return {
        "name": "Minecraft Vanilla (Oficial)",
        "icon": "🌱",
        "type": "vanilla",
        "runner": archivo_objetivo if archivo_objetivo else "server.jar",
        "description": "Servidor oficial de Mojang sin modificaciones",
    }


# Alias en inglés para compatibilidad
detect_software_info = detectar_informacion_software


def configurar_rutas(
    enrutador_app: APIRouter,
    proceso: MinecraftProcess,
    config_mgr: ConfigManager,
    installer: ServerInstaller,
    tunnel_mgr: PlayitTunnelManager,
    settings_mgr: SettingsManager,
    discord_notifier: DiscordNotifier,
    mod_mgr: Optional[ModManager] = None,
    modrinth_client: Optional[ModrinthClient] = None,
) -> None:
    """Registra y enlaza todos los controladores de rutas REST de la aplicación."""
    gestor_jdk = JdkManager()

    @enrutador_app.get("/status")
    async def obtener_estado():
        """Devuelve el estado completo y métricas de Foxden."""
        metricas = proceso.obtener_metricas()
        objetivo = settings_mgr.obtener("target_jar", "server.jar")
        motor = settings_mgr.obtener("installed_engine", "")
        metricas["target_jar"] = objetivo
        metricas["installed_engine"] = motor
        metricas["min_ram_gb"] = settings_mgr.obtener("min_ram_gb", 2)
        metricas["max_ram_gb"] = settings_mgr.obtener("max_ram_gb", 4)
        metricas["software_info"] = detectar_informacion_software(
            installer.server_dir, objetivo, motor_instalado=motor
        )
        metricas["installed_version"] = settings_mgr.obtener("installed_version", "")
        metricas["is_installed"] = installer.esta_servidor_instalado()
        metricas["active_jdk"] = settings_mgr.obtener("selected_jdk", "auto")
        metricas["tunnel"] = tunnel_mgr.obtener_estado()
        metricas["discord_enabled"] = discord_notifier.enabled
        metricas["discord_configured"] = discord_notifier.esta_configurado()
        metricas["app_version"] = __version__
        return metricas

    @enrutador_app.get("/version")
    async def obtener_version():
        """Devuelve la versión actual de la aplicación Foxden."""
        return {"version": __version__, "app": "Foxden"}

    @enrutador_app.get("/jdks")
    async def obtener_jdks():
        """Lista las versiones de JDK instaladas en el sistema."""
        instalados = gestor_jdk.listar_jdks_instalados()
        return {"jdks": instalados}

    @enrutador_app.get("/tunnel/status")
    async def obtener_estado_tunel():
        """Obtiene el estado actual del túnel Playit."""
        return tunnel_mgr.obtener_estado()

    @enrutador_app.post("/tunnel/start")
    async def iniciar_tunel():
        """Inicia el proceso del túnel de conexión pública."""
        exito = await tunnel_mgr.iniciar()
        if not exito and tunnel_mgr.state != "RUNNING":
            raise HTTPException(status_code=400, detail="No se pudo iniciar el túnel de Playit.")
        return {"status": "started", "tunnel": tunnel_mgr.obtener_estado()}

    @enrutador_app.post("/tunnel/stop")
    async def detener_tunel():
        """Detiene el túnel Playit."""
        exito = await tunnel_mgr.detener()
        if not exito:
            raise HTTPException(status_code=400, detail="El túnel no se encuentra en ejecución.")
        return {"status": "stopped", "tunnel": tunnel_mgr.obtener_estado()}

    @enrutador_app.post("/server/start")
    async def iniciar_servidor():
        """Inicia el servidor de Minecraft previa verificación de instalación y JDK."""
        if not installer.esta_servidor_instalado():
            raise HTTPException(
                status_code=400,
                detail="Debes configurar e instalar al menos un motor de Minecraft desde la pestaña 'Versiones e Instalador' antes de iniciar el servidor.",
            )

        config_mgr.asegurar_eula_aceptado()

        min_ram = settings_mgr.obtener("min_ram_gb", 2)
        max_ram = settings_mgr.obtener("max_ram_gb", 4)
        objetivo = settings_mgr.obtener("target_jar", "server.jar")
        version_instalada = settings_mgr.obtener("installed_version", "")

        # Seleccionar mejor JDK
        ruta_jdk_seleccionada = settings_mgr.obtener("selected_jdk")
        if ruta_jdk_seleccionada and ruta_jdk_seleccionada != "auto":
            jdks = gestor_jdk.listar_jdks_instalados()
            info_jdk = next((j for j in jdks if j["path"] == ruta_jdk_seleccionada), None)
            if not info_jdk:
                info_jdk = gestor_jdk.obtener_mejor_jdk_para_version(version_instalada)
        else:
            info_jdk = gestor_jdk.obtener_mejor_jdk_para_version(version_instalada)

        bin_java = info_jdk.get("path", "java")
        entorno = gestor_jdk.construir_entorno_para_jdk(info_jdk)

        # Si el objetivo explícito es run.sh (Forge/NeoForge), invocar vía bash
        if objetivo == "run.sh":
            proceso.launch_command = ["bash", "run.sh"]
        else:
            proceso.launch_command = [
                bin_java,
                f"-Xms{min_ram}G",
                f"-Xmx{max_ram}G",
                "-jar",
                objetivo,
                "nogui",
            ]

        exito = await proceso.iniciar(env=entorno)
        if not exito:
            raise HTTPException(status_code=400, detail="No se pudo iniciar el servidor o ya está en ejecución.")
        return {"status": "started", "metrics": proceso.obtener_metricas(), "jdk_used": info_jdk}

    @enrutador_app.post("/server/stop")
    async def detener_servidor():
        """Detiene de forma limpia el servidor de Minecraft."""
        exito = await proceso.detener()
        if not exito:
            raise HTTPException(status_code=400, detail="El servidor no está en ejecución.")
        return {"status": "stopped"}

    @enrutador_app.post("/server/restart")
    async def reiniciar_servidor():
        """Reinicia el servidor de Minecraft."""
        exito = await proceso.reiniciar()
        if not exito:
            raise HTTPException(status_code=400, detail="Error al reiniciar el servidor.")
        return {"status": "restarted"}

    @enrutador_app.post("/server/command")
    async def enviar_comando(solicitud: CommandRequest):
        """Envía un comando a la consola de Minecraft."""
        exito = await proceso.enviar_comando(solicitud.command)
        if not exito:
            raise HTTPException(status_code=400, detail="Error al enviar el comando. ¿El servidor está encendido?")
        return {"status": "command_sent"}

    @enrutador_app.get("/config")
    async def obtener_configuracion():
        """Devuelve la configuración consolidada del servidor y del panel."""
        resumen = config_mgr.obtener_resumen_ajustes()
        todas_las_propiedades = config_mgr.leer_propiedades()
        objetivo = settings_mgr.obtener("target_jar", "server.jar")
        motor = settings_mgr.obtener("installed_engine", "")
        return {
            "summary": resumen,
            "all_properties": todas_las_propiedades,
            "min_ram_gb": settings_mgr.obtener("min_ram_gb", 2),
            "max_ram_gb": settings_mgr.obtener("max_ram_gb", 4),
            "target_jar": objetivo,
            "installed_engine": motor,
            "selected_jdk": settings_mgr.obtener("selected_jdk", "auto"),
            "discord_enabled": settings_mgr.obtener("discord_enabled", True),
            "discord_webhook_url": discord_notifier.webhook_url or "",
            "discord_show_ip": discord_notifier.show_ip,
            "public_ip_alias": settings_mgr.obtener("public_ip_alias", ""),
            "software_info": detectar_informacion_software(
                installer.server_dir, objetivo, motor_instalado=motor
            ),
            "tunnel": tunnel_mgr.obtener_estado(),
        }

    @enrutador_app.post("/config")
    async def actualizar_configuracion(solicitud: ConfigUpdateRequest):
        """Actualiza las propiedades de Minecraft y los ajustes globales de Foxden."""
        if solicitud.properties:
            config_mgr.actualizar_propiedades(solicitud.properties)

        actualizaciones = {}
        if solicitud.min_ram_gb is not None:
            actualizaciones["min_ram_gb"] = solicitud.min_ram_gb
        if solicitud.max_ram_gb is not None:
            actualizaciones["max_ram_gb"] = solicitud.max_ram_gb
        if solicitud.target_jar is not None:
            actualizaciones["target_jar"] = solicitud.target_jar
            jar_minus = solicitud.target_jar.lower()
            if jar_minus == "run.sh":
                es_neo = False
                if (installer.server_dir / "run.sh").exists():
                    try:
                        es_neo = "neoforged" in (installer.server_dir / "run.sh").read_text(errors="ignore")
                    except Exception:
                        pass
                actualizaciones["installed_engine"] = "neoforge" if es_neo else "forge"
            elif "forge" in jar_minus:
                actualizaciones["installed_engine"] = "forge"
            elif "fabric" in jar_minus:
                actualizaciones["installed_engine"] = "fabric"
            elif "neoforge" in jar_minus:
                actualizaciones["installed_engine"] = "neoforge"
            else:
                actualizaciones["installed_engine"] = "vanilla"

        if solicitud.installed_engine is not None:
            actualizaciones["installed_engine"] = solicitud.installed_engine.lower()

        if solicitud.selected_jdk is not None:
            actualizaciones["selected_jdk"] = solicitud.selected_jdk
        if solicitud.discord_enabled is not None:
            actualizaciones["discord_enabled"] = solicitud.discord_enabled
            discord_notifier.enabled = solicitud.discord_enabled
        if solicitud.discord_webhook_url is not None:
            url_limpia = solicitud.discord_webhook_url.strip()
            actualizaciones["discord_webhook_url"] = url_limpia
            discord_notifier.webhook_url = url_limpia if url_limpia else None
        if solicitud.discord_show_ip is not None:
            actualizaciones["discord_show_ip"] = solicitud.discord_show_ip
            discord_notifier.show_ip = solicitud.discord_show_ip
        if solicitud.public_ip_alias is not None:
            actualizaciones["public_ip_alias"] = solicitud.public_ip_alias.strip()

        if actualizaciones:
            settings_mgr.actualizar(actualizaciones)

        return {"status": "updated", "config": await obtener_configuracion()}

    @enrutador_app.post("/discord/test")
    async def probar_discord(solicitud: DiscordTestRequest):
        """Despacha un mensaje embebido de prueba a Discord."""
        url = (solicitud.webhook_url or discord_notifier.webhook_url or "").strip()
        if not url:
            raise HTTPException(status_code=400, detail="Debes ingresar la URL del Webhook de Discord.")

        if not (url.startswith("https://discord.com/api/webhooks/") or url.startswith("https://discordapp.com/api/webhooks/")):
            raise HTTPException(
                status_code=400,
                detail="La URL debe ser un webhook oficial de Discord (comenzar con https://discord.com/api/webhooks/...)",
            )

        ip = tunnel_mgr.public_address or settings_mgr.obtener("public_ip_alias") or "playit.tu-servidor.gg"
        objetivo = settings_mgr.obtener("target_jar", "server.jar")
        motor = settings_mgr.obtener("installed_engine", "")
        info = detectar_informacion_software(installer.server_dir, objetivo, motor_instalado=motor)
        tipo = info.get("type", "vanilla")
        exito = await discord_notifier.enviar_mensaje_prueba(
            ip_publica=ip,
            webhook_personalizado=url,
            mostrar_ip_personalizado=solicitud.show_ip,
            tipo_motor=tipo,
        )
        if not exito:
            raise HTTPException(
                status_code=400,
                detail="Discord rechazó la solicitud. Verifica que la URL del Webhook sea correcta y esté activa.",
            )

        return {"status": "success", "message": "¡Notificación de prueba enviada con éxito a Discord!"}

    @enrutador_app.get("/installer/versions")
    async def obtener_versiones(
        server_type: str = Query("vanilla", description="vanilla, fabric, forge, o neoforge"),
        include_snapshots: bool = Query(False, description="Incluir versiones experimentales (snapshots)")
    ):
        """Devuelve el catálogo de versiones descargables para el cargador seleccionado."""
        versiones = await installer.obtener_versiones(tipo_servidor=server_type, incluir_snapshots=include_snapshots)
        return {"server_type": server_type, "versions": versiones}

    @enrutador_app.get("/installer/installed-jars")
    async def obtener_jars_instalados():
        """Devuelve los ejecutables instalados en el servidor."""
        jars = installer.listar_jars_instalados()
        return {"jars": jars}

    @enrutador_app.post("/installer/download")
    async def descargar_version(solicitud: DownloadVersionRequest):
        """Descarga e instala la versión solicitada."""
        try:
            archivo_objetivo = await installer.descargar_servidor(solicitud.server_type, solicitud.version)
            config_mgr.asegurar_eula_aceptado()
            motor = solicitud.server_type.lower()
            settings_mgr.actualizar({
                "target_jar": archivo_objetivo.name,
                "installed_version": solicitud.version,
                "installed_engine": motor,
            })
            info_software = detectar_informacion_software(
                installer.server_dir,
                archivo_objetivo.name,
                motor_instalado=motor,
            )
            return {
                "status": "success",
                "message": f"{info_software['name']} ({solicitud.version}) listo para iniciar",
                "target_jar": archivo_objetivo.name,
                "installed_version": solicitud.version,
                "installed_engine": motor,
                "software_info": info_software,
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @enrutador_app.get("/mods")
    async def obtener_mods():
        """Lista todos los mods instalados en servidor_minecraft/mods/."""
        if not mod_mgr:
            return {"mods": [], "total": 0, "enabled_count": 0, "disabled_count": 0}
        mods = mod_mgr.listar_mods()
        activos = sum(1 for m in mods if m["enabled"])
        desactivados = len(mods) - activos
        return {
            "mods": mods,
            "total": len(mods),
            "enabled_count": activos,
            "disabled_count": desactivados,
        }

    @enrutador_app.post("/mods/upload")
    async def subir_mods(files: List[UploadFile] = File(...)):
        """Sube uno o varios archivos .jar o .zip de modpacks e instala los mods."""
        if not mod_mgr:
            raise HTTPException(status_code=500, detail="Gestor de mods no configurado.")

        resultados = []
        for archivo in files:
            nombre = archivo.filename or "mod.jar"
            contenido = await archivo.read()
            try:
                res = mod_mgr.instalar_archivo(contenido, nombre)
                resultados.append({"filename": nombre, "status": "success", "detail": res})
            except Exception as e:
                resultados.append({"filename": nombre, "status": "error", "error": str(e)})

        return {"uploaded": resultados, "mods": mod_mgr.listar_mods()}

    @enrutador_app.post("/mods/toggle")
    async def alternar_mod(solicitud: ModToggleRequest):
        """Activa o desactiva un mod (.jar <-> .jar.disabled)."""
        if not mod_mgr:
            raise HTTPException(status_code=500, detail="Gestor de mods no configurado.")
        try:
            res = mod_mgr.alternar_estado(solicitud.filename, solicitud.enabled)
            return {"status": "success", "mod": res}
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="El mod especificado no existe.")
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @enrutador_app.delete("/mods/{filename}")
    async def eliminar_mod(filename: str):
        """Elimina un archivo de mod del servidor."""
        if not mod_mgr:
            raise HTTPException(status_code=500, detail="Gestor de mods no configurado.")
        try:
            exito = mod_mgr.eliminar_mod(filename)
            if not exito:
                raise HTTPException(status_code=404, detail="El archivo no existe.")
            return {"status": "success", "message": f"Mod {filename} eliminado correctamente."}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @enrutador_app.get("/mods/modrinth/search")
    async def buscar_mods_modrinth(
        query: str = "",
        loader: Optional[str] = None,
        version: Optional[str] = None,
        sort: str = "relevance",
        offset: int = 0,
        limit: int = 20,
        server_only: bool = True,
    ):
        """Busca mods en Modrinth con filtros por cargador, versión de Minecraft y soporte de servidor."""
        if not modrinth_client:
            raise HTTPException(status_code=500, detail="Cliente de Modrinth no configurado.")
        try:
            return await modrinth_client.buscar_mods(
                query=query,
                loader=loader,
                version=version,
                solo_servidor=server_only,
                sort=sort,
                limit=limit,
                offset=offset,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error consultando Modrinth: {str(e)}")

    @enrutador_app.get("/mods/modrinth/project/{project_id}/versions")
    async def obtener_versiones_modrinth(
        project_id: str,
        loader: Optional[str] = None,
        version: Optional[str] = None,
    ):
        """Obtiene las versiones disponibles de un mod en Modrinth."""
        if not modrinth_client:
            raise HTTPException(status_code=500, detail="Cliente de Modrinth no configurado.")
        try:
            return await modrinth_client.obtener_versiones(
                project_id_o_slug=project_id,
                loader=loader,
                version=version,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error obteniendo versiones de Modrinth: {str(e)}")

    @enrutador_app.post("/mods/modrinth/install")
    async def instalar_mod_modrinth(solicitud: ModrinthInstallRequest):
        """Descarga e instala un mod desde Modrinth con sus dependencias requeridas."""
        if not modrinth_client:
            raise HTTPException(status_code=500, detail="Cliente de Modrinth no configurado.")

        motor = solicitud.loader or settings_mgr.obtener("installed_engine", "")
        ver = solicitud.game_version or settings_mgr.obtener("installed_version", "")
        try:
            resultado = await modrinth_client.instalar_mod(
                project_id_o_slug=solicitud.project_id,
                version_id=solicitud.version_id,
                loader=motor,
                game_version=ver,
                instalar_dependencias=solicitud.install_dependencies,
            )
            mods_actualizados = mod_mgr.listar_mods() if mod_mgr else []
            return {
                "status": "success",
                "result": resultado,
                "mods": mods_actualizados,
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"No se pudo instalar desde Modrinth: {str(e)}")


# Alias en inglés para compatibilidad
setup_routes = configurar_rutas
