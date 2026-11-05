import { JdkInfo, ServerFullConfig, ServerStatus } from '../types';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = 'Request failed';
    try {
      const data = await res.json();
      errorDetail = data.detail || data.message || errorDetail;
    } catch {
      errorDetail = res.statusText || errorDetail;
    }
    throw new Error(errorDetail);
  }
  return res.json() as Promise<T>;
}

export const api = {
  async getStatus(): Promise<ServerStatus> {
    const res = await fetch('/api/status');
    return handleResponse<ServerStatus>(res);
  },

  async startServer(): Promise<{ status: string }> {
    const res = await fetch('/api/server/start', { method: 'POST' });
    return handleResponse<{ status: string }>(res);
  },

  async stopServer(): Promise<{ status: string }> {
    const res = await fetch('/api/server/stop', { method: 'POST' });
    return handleResponse<{ status: string }>(res);
  },

  async restartServer(): Promise<{ status: string }> {
    const res = await fetch('/api/server/restart', { method: 'POST' });
    return handleResponse<{ status: string }>(res);
  },

  async sendCommand(command: string): Promise<{ status: string }> {
    const res = await fetch('/api/server/command', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command }),
    });
    return handleResponse<{ status: string }>(res);
  },

  async getConfig(): Promise<ServerFullConfig> {
    const res = await fetch('/api/config');
    return handleResponse<ServerFullConfig>(res);
  },

  async updateConfig(payload: any): Promise<{ status: string; config: ServerFullConfig }> {
    const res = await fetch('/api/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return handleResponse<{ status: string; config: ServerFullConfig }>(res);
  },

  async getJdks(): Promise<{ jdks: JdkInfo[] }> {
    const res = await fetch('/api/jdks');
    return handleResponse<{ jdks: JdkInfo[] }>(res);
  },

  async startTunnel(): Promise<any> {
    const res = await fetch('/api/tunnel/start', { method: 'POST' });
    return handleResponse<any>(res);
  },

  async stopTunnel(): Promise<any> {
    const res = await fetch('/api/tunnel/stop', { method: 'POST' });
    return handleResponse<any>(res);
  },

  async getVersions(serverType: string, includeSnapshots: boolean = false): Promise<{ server_type: string; versions: string[] }> {
    const res = await fetch(`/api/installer/versions?server_type=${serverType}&include_snapshots=${includeSnapshots}`);
    return handleResponse<{ server_type: string; versions: string[] }>(res);
  },

  async getInstalledJars(): Promise<{ jars: string[] }> {
    const res = await fetch('/api/installer/installed-jars');
    return handleResponse<{ jars: string[] }>(res);
  },

  async downloadVersion(serverType: string, version: string): Promise<any> {
    const res = await fetch('/api/installer/download', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ server_type: serverType, version }),
    });
    return handleResponse<any>(res);
  },

  async testDiscord(webhookUrl: string, showIp: boolean): Promise<{ status: string; message: string }> {
    const res = await fetch('/api/discord/test', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ webhook_url: webhookUrl, show_ip: showIp }),
    });
    return handleResponse<{ status: string; message: string }>(res);
  },
};
