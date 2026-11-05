import React, { useState, useEffect } from 'react';
import { Save, Bell, Eye, EyeOff, FlaskConical, CheckCircle, AlertCircle, Cpu, Sliders } from 'lucide-react';
import { api } from '../../services/api';
import { JdkInfo } from '../../types';

export const ConfigTab: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [saveFeedback, setSaveFeedback] = useState<string | null>(null);

  // General server settings
  const [motd, setMotd] = useState<string>('Mi Servidor de Minecraft');
  const [port, setPort] = useState<number>(25565);
  const [maxPlayers, setMaxPlayers] = useState<number>(20);
  const [gamemode, setGamemode] = useState<string>('survival');
  const [difficulty, setDifficulty] = useState<string>('easy');
  const [onlineMode, setOnlineMode] = useState<string>('true');
  const [pvp, setPvp] = useState<string>('true');
  const [whitelist, setWhitelist] = useState<string>('false');
  const [levelSeed, setLevelSeed] = useState<string>('');

  // Memory & Java
  const [minRam, setMinRam] = useState<number>(2);
  const [maxRam, setMaxRam] = useState<number>(4);
  const [selectedJdk, setSelectedJdk] = useState<string>('auto');
  const [jdks, setJdks] = useState<JdkInfo[]>([]);

  // Discord settings
  const [discordEnabled, setDiscordEnabled] = useState<boolean>(true);
  const [discordWebhookUrl, setDiscordWebhookUrl] = useState<string>('');
  const [discordShowIp, setDiscordShowIp] = useState<boolean>(true);
  const [showWebhookPassword, setShowWebhookPassword] = useState<boolean>(false);
  const [testingDiscord, setTestingDiscord] = useState<boolean>(false);
  const [discordTestFeedback, setDiscordTestFeedback] = useState<{ type: 'success' | 'error'; msg: string } | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const [configData, jdksData] = await Promise.all([api.getConfig(), api.getJdks()]);

        const s = configData.summary;
        if (s) {
          setMotd(s.motd || '');
          setPort(s.server_port || 25565);
          setMaxPlayers(s.max_players || 20);
          setGamemode(s.gamemode || 'survival');
          setDifficulty(s.difficulty || 'easy');
          setOnlineMode(s.online_mode ? 'true' : 'false');
          setPvp(s.pvp ? 'true' : 'false');
          setWhitelist(s.white_list ? 'true' : 'false');
          setLevelSeed(s.level_seed || '');
        }

        setMinRam(configData.min_ram_gb || 2);
        setMaxRam(configData.max_ram_gb || 4);
        setSelectedJdk(configData.selected_jdk || 'auto');
        setDiscordEnabled(configData.discord_enabled !== false);
        setDiscordWebhookUrl(configData.discord_webhook_url || '');
        setDiscordShowIp(configData.discord_show_ip !== false);

        setJdks(jdksData.jdks || []);
      } catch (err) {
        console.error('Error loading config:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSaveFeedback(null);

    const payload = {
      properties: {
        motd,
        'server-port': String(port),
        'max-players': String(maxPlayers),
        gamemode,
        difficulty,
        'online-mode': onlineMode,
        pvp,
        'white-list': whitelist,
        'level-seed': levelSeed.trim(),
      },
      min_ram_gb: Number(minRam),
      max_ram_gb: Number(maxRam),
      selected_jdk: selectedJdk,
      discord_enabled: discordEnabled,
      discord_webhook_url: discordWebhookUrl.trim(),
      discord_show_ip: discordShowIp,
    };

    try {
      await api.updateConfig(payload);
      setSaveFeedback('✓ Configuración guardada correctamente');
      setTimeout(() => setSaveFeedback(null), 4000);
    } catch (err: any) {
      setSaveFeedback(`✗ Error al guardar: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  const handleTestDiscord = async () => {
    if (!discordWebhookUrl.trim()) {
      setDiscordTestFeedback({ type: 'error', msg: 'Ingresa primero la URL del webhook de Discord.' });
      return;
    }
    setTestingDiscord(true);
    setDiscordTestFeedback(null);

    try {
      const res = await api.testDiscord(discordWebhookUrl.trim(), discordShowIp);
      setDiscordTestFeedback({ type: 'success', msg: `✓ ${res.message || 'Notificación enviada con éxito'}` });
    } catch (err: any) {
      setDiscordTestFeedback({ type: 'error', msg: `✗ ${err.message || 'Error al conectar con Discord'}` });
    } finally {
      setTestingDiscord(false);
      setTimeout(() => setDiscordTestFeedback(null), 6000);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12 text-slate-400 text-sm">
        Cargando opciones de configuración...
      </div>
    );
  }

  return (
    <form onSubmit={handleSave} className="space-y-6 max-w-4xl mx-auto pb-12">
      {/* Card 1: Server Properties */}
      <div className="bg-dark-800 border border-dark-700 rounded-xl p-6 shadow-md">
        <div className="border-b border-dark-700 pb-4 mb-6 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Sliders className="w-5 h-5 text-fox-400" />
              Ajustes Principales del Servidor
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Configura el comportamiento del mundo en <code>server.properties</code>.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {/* MOTD */}
          <div className="md:col-span-2">
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
              Mensaje del Día (MOTD)
            </label>
            <input
              type="text"
              value={motd}
              onChange={(e) => setMotd(e.target.value)}
              placeholder="Mi Servidor de Minecraft"
              className="w-full bg-dark-900 border border-dark-700 rounded-lg px-3.5 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-fox-500 transition-colors"
            />
          </div>

          {/* Port */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
              Puerto Interno
            </label>
            <input
              type="number"
              value={port}
              onChange={(e) => setPort(Number(e.target.value))}
              className="w-full bg-dark-900 border border-dark-700 rounded-lg px-3.5 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-fox-500 transition-colors"
            />
          </div>

          {/* Max Players */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
              Máximo de Jugadores
            </label>
            <input
              type="number"
              min={1}
              max={1000}
              value={maxPlayers}
              onChange={(e) => setMaxPlayers(Number(e.target.value))}
              className="w-full bg-dark-900 border border-dark-700 rounded-lg px-3.5 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-fox-500 transition-colors"
            />
          </div>

          {/* Gamemode */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
              Modo de Juego
            </label>
            <select
              value={gamemode}
              onChange={(e) => setGamemode(e.target.value)}
              className="w-full bg-dark-900 border border-dark-700 rounded-lg px-3.5 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-fox-500 transition-colors"
            >
              <option value="survival">Supervivencia (Survival)</option>
              <option value="creative">Creativo (Creative)</option>
              <option value="adventure">Aventura (Adventure)</option>
              <option value="spectator">Espectador (Spectator)</option>
            </select>
          </div>

          {/* Difficulty */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
              Dificultad
            </label>
            <select
              value={difficulty}
              onChange={(e) => setDifficulty(e.target.value)}
              className="w-full bg-dark-900 border border-dark-700 rounded-lg px-3.5 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-fox-500 transition-colors"
            >
              <option value="peaceful">Pacífico (Peaceful)</option>
              <option value="easy">Fácil (Easy)</option>
              <option value="normal">Normal</option>
              <option value="hard">Difícil (Hard)</option>
            </select>
          </div>

          {/* Online Mode */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
              Tipo de Cuentas (Online Mode)
            </label>
            <select
              value={onlineMode}
              onChange={(e) => setOnlineMode(e.target.value)}
              className="w-full bg-dark-900 border border-dark-700 rounded-lg px-3.5 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-fox-500 transition-colors"
            >
              <option value="true">Solo Cuentas Premium (Mojang / Microsoft)</option>
              <option value="false">Permitir No-Premium y Premium (Modo Libre)</option>
            </select>
          </div>

          {/* PvP */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
              Combate PvP
            </label>
            <select
              value={pvp}
              onChange={(e) => setPvp(e.target.value)}
              className="w-full bg-dark-900 border border-dark-700 rounded-lg px-3.5 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-fox-500 transition-colors"
            >
              <option value="true">Activado (Permitir daño entre jugadores)</option>
              <option value="false">Desactivado (Sin fuego amigo)</option>
            </select>
          </div>

          {/* Whitelist */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
              Lista Blanca (Whitelist)
            </label>
            <select
              value={whitelist}
              onChange={(e) => setWhitelist(e.target.value)}
              className="w-full bg-dark-900 border border-dark-700 rounded-lg px-3.5 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-fox-500 transition-colors"
            >
              <option value="false">Desactivada (cualquiera puede entrar)</option>
              <option value="true">Activada (solo usuarios autorizados)</option>
            </select>
          </div>

          {/* Level Seed */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
              Semilla del Mundo (World Seed)
            </label>
            <input
              type="text"
              value={levelSeed}
              onChange={(e) => setLevelSeed(e.target.value)}
              placeholder="Opcional (vacío = mapa aleatorio)"
              className="w-full bg-dark-900 border border-dark-700 rounded-lg px-3.5 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-fox-500 transition-colors"
            />
            <p className="text-[11px] text-slate-400 mt-1">Configúrala antes de iniciar el mapa por primera vez.</p>
          </div>
        </div>
      </div>

      {/* Card 2: Memory & Java */}
      <div className="bg-dark-800 border border-dark-700 rounded-xl p-6 shadow-md">
        <div className="border-b border-dark-700 pb-4 mb-6">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Cpu className="w-5 h-5 text-blue-400" />
            Memoria RAM y Entorno Java (JDK)
          </h2>
          <p className="text-xs text-slate-400 mt-1">Ajusta los recursos del servidor para evitar lag o bloqueos.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mb-5">
          {/* Min RAM */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
              RAM Mínima (-Xms)
            </label>
            <div className="relative">
              <input
                type="number"
                min={1}
                max={32}
                value={minRam}
                onChange={(e) => setMinRam(Number(e.target.value))}
                className="w-full bg-dark-900 border border-dark-700 rounded-lg px-3.5 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-fox-500 transition-colors pr-12"
              />
              <span className="absolute right-3.5 top-2.5 text-xs font-bold text-slate-500 select-none">GB</span>
            </div>
          </div>

          {/* Max RAM */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
              RAM Máxima (-Xmx)
            </label>
            <div className="relative">
              <input
                type="number"
                min={1}
                max={32}
                value={maxRam}
                onChange={(e) => setMaxRam(Number(e.target.value))}
                className="w-full bg-dark-900 border border-dark-700 rounded-lg px-3.5 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-fox-500 transition-colors pr-12"
              />
              <span className="absolute right-3.5 top-2.5 text-xs font-bold text-slate-500 select-none">GB</span>
            </div>
          </div>
        </div>

        {/* Java Selector */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
            Versión de Java para Ejecutar
          </label>
          <select
            value={selectedJdk}
            onChange={(e) => setSelectedJdk(e.target.value)}
            className="w-full bg-dark-900 border border-dark-700 rounded-lg px-3.5 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-fox-500 transition-colors"
          >
            <option value="auto">⚡ Automático (Detectar la versión ideal según Minecraft)</option>
            {jdks.map((jdk) => (
              <option key={jdk.path} value={jdk.path}>
                {jdk.name} ({jdk.path})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Card 3: Discord Notifications */}
      <div className="bg-dark-800 border border-dark-700 rounded-xl p-6 shadow-md">
        <div className="border-b border-dark-700 pb-4 mb-6">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Bell className="w-5 h-5 text-indigo-400" />
            Notificaciones de Discord
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Recibe alertas automáticas con embeds y dirección de conexión en tu canal de Discord.
          </p>
        </div>

        {/* Master Toggle */}
        <div className="bg-dark-750 border border-dark-700 rounded-xl p-4 mb-5 flex items-start gap-3">
          <input
            type="checkbox"
            id="chkDiscordEnabled"
            checked={discordEnabled}
            onChange={(e) => setDiscordEnabled(e.target.checked)}
            className="mt-1 w-4 h-4 rounded text-fox-500 focus:ring-fox-500 bg-dark-900 border-dark-700 cursor-pointer"
          />
          <label htmlFor="chkDiscordEnabled" className="cursor-pointer">
            <span className="block text-sm font-bold text-slate-100">Activar notificaciones automáticas de Discord</span>
            <span className="block text-xs text-slate-400 mt-0.5">
              Si desactivas esta opción, Foxden pausará el envío de mensajes sin necesidad de borrar tu URL de webhook.
            </span>
          </label>
        </div>

        {/* Webhook Fields */}
        <div className={`space-y-4 transition-opacity duration-200 ${discordEnabled ? 'opacity-100' : 'opacity-40 pointer-events-none'}`}>
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
              URL del Webhook de Discord
            </label>
            <div className="flex gap-2">
              <input
                type={showWebhookPassword ? 'text' : 'password'}
                value={discordWebhookUrl}
                onChange={(e) => setDiscordWebhookUrl(e.target.value)}
                placeholder="https://discord.com/api/webhooks/..."
                className="flex-1 bg-dark-900 border border-dark-700 rounded-lg px-3.5 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-fox-500 transition-colors font-mono"
              />
              <button
                type="button"
                onClick={() => setShowWebhookPassword(!showWebhookPassword)}
                className="px-3 bg-dark-700 hover:bg-dark-750 text-slate-300 rounded-lg border border-dark-700 transition-colors"
                title="Mostrar/Ocultar URL"
              >
                {showWebhookPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
              <button
                type="button"
                onClick={handleTestDiscord}
                disabled={testingDiscord || !discordWebhookUrl.trim()}
                className="flex items-center gap-1.5 px-3 py-2 bg-dark-700 hover:bg-dark-750 text-slate-200 rounded-lg text-xs font-semibold border border-dark-700 disabled:opacity-40"
              >
                <FlaskConical className="w-3.5 h-3.5 text-indigo-400" />
                <span>{testingDiscord ? 'Probando...' : 'Probar Webhook'}</span>
              </button>
            </div>
            {discordTestFeedback && (
              <p
                className={`text-xs mt-2 font-medium flex items-center gap-1 ${
                  discordTestFeedback.type === 'success' ? 'text-emerald-400' : 'text-rose-400'
                }`}
              >
                {discordTestFeedback.type === 'success' ? <CheckCircle className="w-3.5 h-3.5" /> : <AlertCircle className="w-3.5 h-3.5" />}
                {discordTestFeedback.msg}
              </p>
            )}
          </div>

          <div className="flex items-start gap-3 pt-2">
            <input
              type="checkbox"
              id="chkDiscordShowIp"
              checked={discordShowIp}
              onChange={(e) => setDiscordShowIp(e.target.checked)}
              className="mt-0.5 w-4 h-4 rounded text-fox-500 focus:ring-fox-500 bg-dark-900 border-dark-700 cursor-pointer"
            />
            <label htmlFor="chkDiscordShowIp" className="cursor-pointer">
              <span className="block text-sm font-medium text-slate-200">
                Incluir la dirección IP pública (Playit) en las notificaciones
              </span>
              <span className="block text-xs text-slate-400 mt-0.5">
                Desactiva esta opción si prefieres mantener la IP oculta por privacidad en tu servidor de Discord.
              </span>
            </label>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex items-center justify-between pt-2">
        <button
          type="submit"
          disabled={saving}
          className="flex items-center gap-2 px-6 py-2.5 rounded-lg bg-fox-600 hover:bg-fox-500 active:scale-95 text-white font-semibold text-sm shadow-md transition-all disabled:opacity-40"
        >
          <Save className="w-4 h-4" />
          <span>{saving ? 'Guardando...' : 'Guardar Configuración'}</span>
        </button>

        {saveFeedback && (
          <span
            className={`text-xs font-semibold px-3 py-1.5 rounded-lg border ${
              saveFeedback.startsWith('✓')
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                : 'bg-rose-500/10 border-rose-500/30 text-rose-400'
            }`}
          >
            {saveFeedback}
          </span>
        )}
      </div>
    </form>
  );
};
