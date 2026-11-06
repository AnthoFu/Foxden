/**
 * Cliente HTTP tipado para interactuar con la API REST de Foxden.
 */

import { JdkInfo, ServerFullConfig, ServerStatus } from '../types';

/**
 * Procesa la respuesta de la API y lanza un error descriptivo si el estado HTTP no es exitoso.
 */
async function manejarRespuesta<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detalleError = 'Error en la solicitud';
    try {
      const data = await res.json();
      detalleError = data.detail || data.message || detalleError;
    } catch {
      detalleError = res.statusText || detalleError;
    }
    throw new Error(detalleError);
  }
  return res.json() as Promise<T>;
}

// Alias para compatibilidad
export const handleResponse = manejarRespuesta;

export const api = {
  /**
   * Obtiene las métricas y estado completo del servidor y túnel.
   */
  async obtenerEstado(): Promise<ServerStatus> {
    const res = await fetch('/api/status');
    return manejarRespuesta<ServerStatus>(res);
  },

  /**
   * Inicia el proceso de Minecraft.
   */
  async iniciarServidor(): Promise<{ status: string }> {
    const res = await fetch('/api/server/start', { method: 'POST' });
    return manejarRespuesta<{ status: string }>(res);
  },

  /**
   * Detiene el servidor de Minecraft de forma segura.
   */
  async detenerServidor(): Promise<{ status: string }> {
    const res = await fetch('/api/server/stop', { method: 'POST' });
    return manejarRespuesta<{ status: string }>(res);
  },

  /**
   * Reinicia el servidor de Minecraft.
   */
  async reiniciarServidor(): Promise<{ status: string }> {
    const res = await fetch('/api/server/restart', { method: 'POST' });
    return manejarRespuesta<{ status: string }>(res);
  },

  /**
   * Envía un comando a la consola de Minecraft.
   */
  async enviarComando(comando: string): Promise<{ status: string }> {
    const res = await fetch('/api/server/command', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command: comando }),
    });
    return manejarRespuesta<{ status: string }>(res);
  },

  /**
   * Obtiene la configuración consolidada.
   */
  async obtenerConfiguracion(): Promise<ServerFullConfig> {
    const res = await fetch('/api/config');
    return manejarRespuesta<ServerFullConfig>(res);
  },

  /**
   * Guarda cambios en la configuración.
   */
  async actualizarConfiguracion(carga: any): Promise<{ status: string; config: ServerFullConfig }> {
    const res = await fetch('/api/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(carga),
    });
    return manejarRespuesta<{ status: string; config: ServerFullConfig }>(res);
  },

  /**
   * Lista los JDK instalados en el sistema.
   */
  async obtenerJdks(): Promise<{ jdks: JdkInfo[] }> {
    const res = await fetch('/api/jdks');
    return manejarRespuesta<{ jdks: JdkInfo[] }>(res);
  },

  /**
   * Inicia el túnel público Playit.
   */
  async iniciarTunel(): Promise<any> {
    const res = await fetch('/api/tunnel/start', { method: 'POST' });
    return manejarRespuesta<any>(res);
  },

  /**
   * Detiene el túnel Playit.
   */
  async detenerTunel(): Promise<any> {
    const res = await fetch('/api/tunnel/stop', { method: 'POST' });
    return manejarRespuesta<any>(res);
  },

  /**
   * Obtiene la lista de versiones de Minecraft disponibles para instalar.
   */
  async obtenerVersiones(tipoServidor: string, incluirSnapshots: boolean = false): Promise<{ server_type: string; versions: string[] }> {
    const res = await fetch(`/api/installer/versions?server_type=${tipoServidor}&include_snapshots=${incluirSnapshots}`);
    return manejarRespuesta<{ server_type: string; versions: string[] }>(res);
  },

  /**
   * Lista los archivos ejecutables (JARs o run.sh) instalados.
   */
  async obtenerJarsInstalados(): Promise<{ jars: string[] }> {
    const res = await fetch('/api/installer/installed-jars');
    return manejarRespuesta<{ jars: string[] }>(res);
  },

  /**
   * Descarga e instala una versión específica.
   */
  async descargarVersion(tipoServidor: string, version: string): Promise<any> {
    const res = await fetch('/api/installer/download', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ server_type: tipoServidor, version }),
    });
    return manejarRespuesta<any>(res);
  },

  /**
   * Envía un mensaje de prueba al webhook de Discord.
   */
  async probarDiscord(urlWebhook: string, mostrarIp: boolean): Promise<{ status: string; message: string }> {
    const res = await fetch('/api/discord/test', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ webhook_url: urlWebhook, show_ip: mostrarIp }),
    });
    return manejarRespuesta<{ status: string; message: string }>(res);
  },

  // Alias en inglés para compatibilidad
  getStatus() { return this.obtenerEstado(); },
  startServer() { return this.iniciarServidor(); },
  stopServer() { return this.detenerServidor(); },
  restartServer() { return this.reiniciarServidor(); },
  sendCommand(command: string) { return this.enviarComando(command); },
  getConfig() { return this.obtenerConfiguracion(); },
  updateConfig(payload: any) { return this.actualizarConfiguracion(payload); },
  getJdks() { return this.obtenerJdks(); },
  startTunnel() { return this.iniciarTunel(); },
  stopTunnel() { return this.detenerTunel(); },
  getVersions(serverType: string, includeSnapshots: boolean = false) { return this.obtenerVersiones(serverType, includeSnapshots); },
  getInstalledJars() { return this.obtenerJarsInstalados(); },
  downloadVersion(serverType: string, version: string) { return this.descargarVersion(serverType, version); },
  testDiscord(webhookUrl: string, showIp: boolean) { return this.probarDiscord(webhookUrl, showIp); },
};
