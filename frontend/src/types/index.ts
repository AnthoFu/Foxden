export type ProcessState = 'STOPPED' | 'STARTING' | 'RUNNING' | 'STOPPING';

export interface SoftwareInfo {
  name: string;
  icon: string;
  type: string;
  runner: string;
  description: string;
}

export interface TunnelStatus {
  state: 'RUNNING' | 'WAITING_CLAIM' | 'STOPPED';
  public_address: string | null;
  claim_url: string | null;
  logs: string[];
}

export interface ServerStatus {
  state: ProcessState;
  cpu_percent: number;
  memory_mb: number;
  uptime_seconds: number;
  target_jar: string;
  min_ram_gb: number;
  max_ram_gb: number;
  software_info: SoftwareInfo;
  installed_version: string;
  installed_engine?: string;
  is_installed: boolean;
  active_jdk: string;
  tunnel: TunnelStatus;
  discord_enabled: boolean;
  discord_configured: boolean;
  app_version?: string;
}

export interface JdkInfo {
  major: number;
  path: string;
  name: string;
  home: string;
}

export interface ServerSummaryConfig {
  server_port: number;
  motd: string;
  max_players: number;
  difficulty: string;
  gamemode: string;
  online_mode: boolean;
  pvp: boolean;
  white_list: boolean;
  view_distance: number;
  level_seed?: string;
}

export interface ServerFullConfig {
  summary: ServerSummaryConfig;
  all_properties: Record<string, string>;
  min_ram_gb: number;
  max_ram_gb: number;
  target_jar: string;
  selected_jdk: string;
  discord_enabled: boolean;
  discord_webhook_url: string;
  discord_show_ip: boolean;
  public_ip_alias: string;
  software_info: SoftwareInfo;
  tunnel: TunnelStatus;
}

export interface ModItem {
  filename: string;
  name: string;
  version: string;
  description: string;
  loader: string;
  enabled: boolean;
  size_bytes: number;
  size_mb: number;
  modified_at: string;
}

export interface ModsResponse {
  mods: ModItem[];
  total: number;
  enabled_count: number;
  disabled_count: number;
}

export interface ModrinthHit {
  project_id: string;
  slug: string;
  author: string;
  title: string;
  description: string;
  categories: string[];
  display_categories: string[];
  versions: string[];
  downloads: number;
  follows: number;
  icon_url: string | null;
  date_modified: string;
  latest_version: string;
  client_side: string;
  server_side: string;
}

export interface ModrinthSearchResponse {
  hits: ModrinthHit[];
  offset: number;
  limit: number;
  total_hits: number;
}

export interface ModrinthInstallResult {
  status: string;
  result: {
    status: string;
    installed_file: string;
    installed_files: string[];
    dependencies_installed: string[];
    version_number: string;
  };
  mods: ModItem[];
}
