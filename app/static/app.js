/**
 * Foxden - Frontend Client
 */

document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const statusBadge = document.getElementById("statusBadge");
  const statusText = document.getElementById("statusText");
  const cpuValue = document.getElementById("cpuValue");
  const ramValue = document.getElementById("ramValue");
  const uptimeValue = document.getElementById("uptimeValue");
  const headerTunnelText = document.getElementById("headerTunnelText");

  const btnStart = document.getElementById("btnStart");
  const btnRestart = document.getElementById("btnRestart");
  const btnStop = document.getElementById("btnStop");

  const tabBtns = document.querySelectorAll(".tab-btn");
  const tabPanes = document.querySelectorAll(".tab-pane");

  const terminalBody = document.getElementById("terminalBody");
  const chkAutoscroll = document.getElementById("chkAutoscroll");
  const btnClearConsole = document.getElementById("btnClearConsole");
  const commandForm = document.getElementById("commandForm");
  const commandInput = document.getElementById("commandInput");
  const wsStatus = document.getElementById("wsStatus");

  const configForm = document.getElementById("configForm");
  const configSaveMsg = document.getElementById("configSaveMsg");
  const cfgJdk = document.getElementById("cfgJdk");

  const activeSoftwareIcon = document.getElementById("activeSoftwareIcon");
  const activeSoftwareName = document.getElementById("activeSoftwareName");
  const activeSoftwareDesc = document.getElementById("activeSoftwareDesc");
  const selActiveJar = document.getElementById("selActiveJar");
  const btnSetActiveJar = document.getElementById("btnSetActiveJar");

  const selServerType = document.getElementById("selServerType");
  const selVersion = document.getElementById("selVersion");
  const chkSnapshots = document.getElementById("chkSnapshots");
  const btnDownloadServer = document.getElementById("btnDownloadServer");
  const downloadFeedback = document.getElementById("downloadFeedback");

  // Tunnel Elements
  const tunnelDot = document.getElementById("tunnelDot");
  const tunnelStatusText = document.getElementById("tunnelStatusText");
  const btnStartTunnel = document.getElementById("btnStartTunnel");
  const btnStopTunnel = document.getElementById("btnStopTunnel");
  const tunnelClaimBox = document.getElementById("tunnelClaimBox");
  const tunnelClaimLink = document.getElementById("tunnelClaimLink");
  const tunnelAddressCard = document.getElementById("tunnelAddressCard");
  const tunnelAddressDisplay = document.getElementById("tunnelAddressDisplay");
  const tunnelDetectedWrapper = document.getElementById("tunnelDetectedWrapper");
  const tunnelExternalPrompt = document.getElementById("tunnelExternalPrompt");
  const txtSavedAlias = document.getElementById("txtSavedAlias");
  const btnSaveAlias = document.getElementById("btnSaveAlias");
  const btnEditAlias = document.getElementById("btnEditAlias");
  const btnCopyAddress = document.getElementById("btnCopyAddress");
  const tunnelLogsBody = document.getElementById("tunnelLogsBody");

  // State
  let ws = null;
  let commandHistory = [];
  let historyIndex = -1;

  // Tabs
  tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      tabBtns.forEach((b) => b.classList.remove("active"));
      tabPanes.forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      const targetPane = document.getElementById(btn.dataset.tab);
      if (targetPane) targetPane.classList.add("active");

      if (btn.dataset.tab === "tabConfig") loadConfig();
      if (btn.dataset.tab === "tabVersions") loadVersionsTab();
      if (btn.dataset.tab === "tabTunnel") fetchStatus();
    });
  });

  // WebSocket
  function connectWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws/console`;

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      wsStatus.textContent = "● WebSocket: Conectado";
      wsStatus.className = "connection-status connected";
    };

    ws.onmessage = (event) => {
      appendTerminalLine(event.data);
    };

    ws.onclose = () => {
      wsStatus.textContent = "● WebSocket: Reconectando en 3s...";
      wsStatus.className = "connection-status";
      setTimeout(connectWebSocket, 3000);
    };

    ws.onerror = () => {
      ws.close();
    };
  }

  function appendTerminalLine(text) {
    const line = document.createElement("div");
    line.className = "terminal-line";

    if (text.startsWith("[FOXDEN]") || text.startsWith("[MC-MANAGER]")) {
      line.classList.add("manager");
    } else if (text.startsWith(">")) {
      line.classList.add("command");
    } else if (text.includes("ERROR") || text.includes("Exception")) {
      line.classList.add("error");
    } else if (text.includes("WARN")) {
      line.classList.add("warn");
    } else {
      line.classList.add("info");
    }

    line.textContent = text;
    terminalBody.appendChild(line);

    if (chkAutoscroll.checked) {
      terminalBody.scrollTop = terminalBody.scrollHeight;
    }
  }

  btnClearConsole.addEventListener("click", () => {
    terminalBody.innerHTML = "";
  });

  // Command input with history
  commandForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const cmd = commandInput.value.trim();
    if (!cmd) return;

    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(cmd);
    } else {
      fetch("/api/server/command", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command: cmd }),
      });
    }

    commandHistory.push(cmd);
    historyIndex = commandHistory.length;
    commandInput.value = "";
  });

  commandInput.addEventListener("keydown", (e) => {
    if (e.key === "ArrowUp") {
      if (historyIndex > 0) {
        historyIndex--;
        commandInput.value = commandHistory[historyIndex];
      }
      e.preventDefault();
    } else if (e.key === "ArrowDown") {
      if (historyIndex < commandHistory.length - 1) {
        historyIndex++;
        commandInput.value = commandHistory[historyIndex];
      } else {
        historyIndex = commandHistory.length;
        commandInput.value = "";
      }
      e.preventDefault();
    }
  });

  // Status Polling
  async function fetchStatus() {
    try {
      const res = await fetch("/api/status");
      if (!res.ok) return;
      const data = await res.json();

      const state = data.state;
      statusBadge.className = "status-badge";
      if (state === "RUNNING") {
        statusBadge.classList.add("online");
        statusText.textContent = "EN LÍNEA";
      } else if (state === "STARTING") {
        statusBadge.classList.add("starting");
        statusText.textContent = "INICIANDO...";
      } else if (state === "STOPPING") {
        statusBadge.classList.add("stopping");
        statusText.textContent = "DETENIENDO...";
      } else {
        statusText.textContent = "DETENIDO";
      }

      cpuValue.textContent = `${data.cpu_percent}%`;
      ramValue.textContent = `${data.memory_mb} MB`;
      uptimeValue.textContent = formatUptime(data.uptime_seconds);

      if (data.software_info) {
        if (activeSoftwareIcon) activeSoftwareIcon.textContent = data.software_info.icon || "🎮";
        if (activeSoftwareName) activeSoftwareName.textContent = data.software_info.name || "Servidor Minecraft";
        if (activeSoftwareDesc) activeSoftwareDesc.textContent = data.software_info.description || "";
      }

      btnStart.disabled = state !== "STOPPED";
      btnRestart.disabled = state === "STOPPED";
      btnStop.disabled = state === "STOPPED" || state === "STOPPING";

      // Tunnel State Handling
      if (data.tunnel) {
        renderTunnelState(data.tunnel);
      }
    } catch (err) {
      statusText.textContent = "OFFLINE (API)";
    }
  }

  function renderTunnelState(tunnel) {
    const tState = tunnel.state;

    if (tState === "RUNNING") {
      headerTunnelText.textContent = "ONLINE";
      headerTunnelText.style.color = "var(--accent-green)";
      tunnelDot.className = "status-dot online";
      tunnelStatusText.textContent = "TÚNEL CONECTADO Y TRANSMITIENDO";
      btnStartTunnel.disabled = true;
      btnStopTunnel.disabled = false;
      tunnelClaimBox.style.display = "none";
      tunnelAddressCard.style.display = "block";

      const savedAlias = localStorage.getItem("mc_playit_alias") || "";
      const displayIp = tunnel.public_address || savedAlias;

      if (displayIp) {
        if (tunnelDetectedWrapper) tunnelDetectedWrapper.style.display = "block";
        if (tunnelExternalPrompt) tunnelExternalPrompt.style.display = "none";
        tunnelAddressDisplay.textContent = displayIp;
      } else {
        if (tunnelDetectedWrapper) tunnelDetectedWrapper.style.display = "none";
        if (tunnelExternalPrompt) tunnelExternalPrompt.style.display = "block";
      }
    } else if (tState === "WAITING_CLAIM") {
      headerTunnelText.textContent = "VINCULAR";
      headerTunnelText.style.color = "var(--accent-amber)";
      tunnelDot.className = "status-dot starting";
      tunnelStatusText.textContent = "ESPERANDO VINCULACIÓN EN PLAYIT.GG";
      btnStartTunnel.disabled = true;
      btnStopTunnel.disabled = false;

      if (tunnel.claim_url) {
        tunnelClaimBox.style.display = "block";
        tunnelClaimLink.href = tunnel.claim_url;
      }
      tunnelAddressCard.style.display = "none";
    } else {
      headerTunnelText.textContent = "OFFLINE";
      headerTunnelText.style.color = "var(--text-muted)";
      tunnelDot.className = "status-dot";
      tunnelStatusText.textContent = "TÚNEL DETENIDO";
      btnStartTunnel.disabled = false;
      btnStopTunnel.disabled = true;
      tunnelClaimBox.style.display = "none";
      tunnelAddressCard.style.display = "none";
    }

    // Render tunnel logs
    if (tunnelLogsBody && tunnel.recent_logs) {
      tunnelLogsBody.innerHTML = "";
      tunnel.recent_logs.forEach((l) => {
        const line = document.createElement("div");
        line.className = "terminal-line info";
        line.textContent = l;
        tunnelLogsBody.appendChild(line);
      });
      tunnelLogsBody.scrollTop = tunnelLogsBody.scrollHeight;
    }
  }

  btnStartTunnel.addEventListener("click", async () => {
    btnStartTunnel.disabled = true;
    await fetch("/api/tunnel/start", { method: "POST" });
    fetchStatus();
  });

  btnStopTunnel.addEventListener("click", async () => {
    btnStopTunnel.disabled = true;
    await fetch("/api/tunnel/stop", { method: "POST" });
    fetchStatus();
  });

  btnCopyAddress.addEventListener("click", () => {
    const text = tunnelAddressDisplay.textContent;
    if (text) {
      navigator.clipboard.writeText(text);
      btnCopyAddress.textContent = "✓ ¡Copiado!";
      setTimeout(() => { btnCopyAddress.textContent = "📋 Copiar IP"; }, 2500);
    }
  });

  if (btnSaveAlias) {
    btnSaveAlias.addEventListener("click", () => {
      const val = (txtSavedAlias.value || "").trim();
      if (!val) return;
      localStorage.setItem("mc_playit_alias", val);
      fetchStatus();
    });
  }

  if (btnEditAlias) {
    btnEditAlias.addEventListener("click", () => {
      localStorage.removeItem("mc_playit_alias");
      if (txtSavedAlias) txtSavedAlias.value = "";
      fetchStatus();
    });
  }

  function formatUptime(seconds) {
    if (!seconds) return "0s";
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    const h = Math.floor(m / 60);
    if (h > 0) return `${h}h ${m % 60}m`;
    if (m > 0) return `${m}m ${s}s`;
    return `${s}s`;
  }

  // Buttons actions
  btnStart.addEventListener("click", async () => {
    btnStart.disabled = true;
    await fetch("/api/server/start", { method: "POST" });
    fetchStatus();
  });

  btnStop.addEventListener("click", async () => {
    btnStop.disabled = true;
    await fetch("/api/server/stop", { method: "POST" });
    fetchStatus();
  });

  btnRestart.addEventListener("click", async () => {
    btnRestart.disabled = true;
    await fetch("/api/server/restart", { method: "POST" });
    fetchStatus();
  });

  // Config tab
  async function loadConfig() {
    try {
      const res = await fetch("/api/config");
      const data = await res.json();
      const s = data.summary;

      document.getElementById("cfgMotd").value = s.motd || "";
      document.getElementById("cfgPort").value = s.server_port || 25565;
      document.getElementById("cfgMaxPlayers").value = s.max_players || 20;
      document.getElementById("cfgGamemode").value = s.gamemode || "survival";
      document.getElementById("cfgDifficulty").value = s.difficulty || "easy";
      document.getElementById("cfgOnlineMode").value = s.online_mode ? "true" : "false";
      document.getElementById("cfgPvp").value = s.pvp ? "true" : "false";
      document.getElementById("cfgWhitelist").value = s.white_list ? "true" : "false";

      document.getElementById("cfgMinRam").value = data.min_ram_gb || 2;
      document.getElementById("cfgMaxRam").value = data.max_ram_gb || 4;

      if (document.getElementById("cfgDiscordWebhook")) {
        document.getElementById("cfgDiscordWebhook").value = data.discord_webhook_url || "";
      }
      if (document.getElementById("cfgDiscordShowIp")) {
        document.getElementById("cfgDiscordShowIp").checked = data.discord_show_ip !== false;
      }

      // Load installed JDKs
      const jdkRes = await fetch("/api/jdks");
      if (jdkRes.ok) {
        const jdkData = await jdkRes.json();
        cfgJdk.innerHTML = '<option value="auto">⚡ Automático (Detectar según versión de Minecraft)</option>';
        jdkData.jdks.forEach((jdk) => {
          const opt = document.createElement("option");
          opt.value = jdk.path;
          opt.textContent = `${jdk.name} (${jdk.path})`;
          cfgJdk.appendChild(opt);
        });
        cfgJdk.value = data.selected_jdk || "auto";
      }
    } catch (e) {
      console.error("Error loading config", e);
    }
  }

  configForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    configSaveMsg.textContent = "Guardando...";
    configSaveMsg.className = "save-feedback";

    const payload = {
      properties: {
        "motd": document.getElementById("cfgMotd").value,
        "server-port": document.getElementById("cfgPort").value,
        "max-players": document.getElementById("cfgMaxPlayers").value,
        "gamemode": document.getElementById("cfgGamemode").value,
        "difficulty": document.getElementById("cfgDifficulty").value,
        "online-mode": document.getElementById("cfgOnlineMode").value,
        "pvp": document.getElementById("cfgPvp").value,
        "white-list": document.getElementById("cfgWhitelist").value,
      },
      min_ram_gb: parseInt(document.getElementById("cfgMinRam").value, 10),
      max_ram_gb: parseInt(document.getElementById("cfgMaxRam").value, 10),
      selected_jdk: cfgJdk.value,
      discord_webhook_url: document.getElementById("cfgDiscordWebhook") ? document.getElementById("cfgDiscordWebhook").value.trim() : "",
      discord_show_ip: document.getElementById("cfgDiscordShowIp") ? document.getElementById("cfgDiscordShowIp").checked : true,
    };

    try {
      const res = await fetch("/api/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        configSaveMsg.textContent = "✓ Cambios guardados correctamente";
        configSaveMsg.className = "save-feedback success";
      } else {
        configSaveMsg.textContent = "✗ Error al guardar";
        configSaveMsg.className = "save-feedback error";
      }
    } catch (err) {
      configSaveMsg.textContent = "✗ Error de red";
      configSaveMsg.className = "save-feedback error";
    }
    setTimeout(() => { configSaveMsg.textContent = ""; }, 4000);
  });

  // Discord test button and password toggle
  const btnTestDiscord = document.getElementById("btnTestDiscord");
  const discordTestFeedback = document.getElementById("discordTestFeedback");
  if (btnTestDiscord) {
    btnTestDiscord.addEventListener("click", async () => {
      const webhookUrl = (document.getElementById("cfgDiscordWebhook")?.value || "").trim();
      const showIp = document.getElementById("cfgDiscordShowIp") ? document.getElementById("cfgDiscordShowIp").checked : true;

      if (!webhookUrl) {
        if (discordTestFeedback) {
          discordTestFeedback.textContent = "⚠️ Ingresa primero la URL del webhook de Discord.";
          discordTestFeedback.style.color = "var(--accent-amber)";
        }
        return;
      }

      btnTestDiscord.disabled = true;
      if (discordTestFeedback) {
        discordTestFeedback.textContent = "⏳ Enviando notificación de prueba a Discord...";
        discordTestFeedback.style.color = "var(--text-muted)";
      }

      try {
        const res = await fetch("/api/discord/test", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ webhook_url: webhookUrl, show_ip: showIp }),
        });
        const data = await res.json();
        if (res.ok) {
          if (discordTestFeedback) {
            discordTestFeedback.textContent = `✓ ${data.message || "¡Notificación enviada con éxito!"}`;
            discordTestFeedback.style.color = "var(--accent-green)";
          }
        } else {
          if (discordTestFeedback) {
            discordTestFeedback.textContent = `✗ ${data.detail || "Error al enviar al webhook de Discord."}`;
            discordTestFeedback.style.color = "var(--accent-red)";
          }
        }
      } catch (err) {
        if (discordTestFeedback) {
          discordTestFeedback.textContent = "✗ Error de red al conectar con el servidor.";
          discordTestFeedback.style.color = "var(--accent-red)";
        }
      } finally {
        btnTestDiscord.disabled = false;
        setTimeout(() => {
          if (discordTestFeedback) discordTestFeedback.textContent = "";
        }, 6000);
      }
    });
  }

  const btnToggleWebhookVisibility = document.getElementById("btnToggleWebhookVisibility");
  if (btnToggleWebhookVisibility) {
    btnToggleWebhookVisibility.addEventListener("click", () => {
      const input = document.getElementById("cfgDiscordWebhook");
      if (!input) return;
      if (input.type === "password") {
        input.type = "text";
        btnToggleWebhookVisibility.textContent = "🙈";
      } else {
        input.type = "password";
        btnToggleWebhookVisibility.textContent = "👁️";
      }
    });
  }

  // Versions tab
  async function loadVersionsTab() {
    await loadInstalledJars();
    await loadVersionsCatalog();
  }

  async function loadInstalledJars() {
    try {
      const jarsRes = await fetch("/api/installer/installed-jars");
      const jarsData = await jarsRes.json();
      selActiveJar.innerHTML = "";
      jarsData.jars.forEach((jar) => {
        const opt = document.createElement("option");
        opt.value = jar;
        opt.textContent = jar;
        selActiveJar.appendChild(opt);
      });

      const statusRes = await fetch("/api/status");
      const statusData = await statusRes.json();
      if (statusData.target_jar) {
        selActiveJar.value = statusData.target_jar;
      }
      if (statusData.software_info) {
        if (activeSoftwareIcon) activeSoftwareIcon.textContent = statusData.software_info.icon || "🎮";
        if (activeSoftwareName) activeSoftwareName.textContent = statusData.software_info.name || "Servidor Minecraft";
        if (activeSoftwareDesc) activeSoftwareDesc.textContent = statusData.software_info.description || "";
      }
    } catch (e) {
      console.error("Error loading jars", e);
    }
  }

  async function loadVersionsCatalog() {
    const serverType = selServerType.value;
    const includeSnapshots = chkSnapshots.checked;

    selVersion.innerHTML = "<option value=''>Consultando catálogo oficial...</option>";

    try {
      const url = `/api/installer/versions?server_type=${serverType}&include_snapshots=${includeSnapshots}`;
      const res = await fetch(url);
      const data = await res.json();

      selVersion.innerHTML = "";
      data.versions.forEach((ver) => {
        const opt = document.createElement("option");
        opt.value = ver;
        let prefix = "Minecraft";
        if (serverType === "forge") prefix = "Forge MC";
        if (serverType === "fabric") prefix = "Fabric MC";
        if (serverType === "purpur") prefix = "Purpur MC";
        opt.textContent = `${prefix} ${ver}`;
        selVersion.appendChild(opt);
      });
    } catch (e) {
      selVersion.innerHTML = "<option value=''>Error al cargar versiones</option>";
      console.error("Error loading versions catalog", e);
    }
  }

  selServerType.addEventListener("change", loadVersionsCatalog);
  chkSnapshots.addEventListener("change", loadVersionsCatalog);

  btnSetActiveJar.addEventListener("click", async () => {
    const jar = selActiveJar.value;
    if (!jar) return;
    await fetch("/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target_jar: jar }),
    });
    await fetchStatus();
    alert(`Ejecutable activo establecido manualmente en: ${jar}`);
  });

  btnDownloadServer.addEventListener("click", async () => {
    const serverType = selServerType.value;
    const ver = selVersion.value;
    if (!ver) return;

    btnDownloadServer.disabled = true;
    downloadFeedback.textContent = `⏳ Descargando e instalando ${serverType.toUpperCase()} ${ver}... Esto puede demorar unos momentos.`;
    downloadFeedback.style.color = "var(--accent-amber)";

    try {
      const res = await fetch("/api/installer/download", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ server_type: serverType, version: ver }),
      });
      const data = await res.json();
      if (res.ok) {
        downloadFeedback.textContent = `✓ ${data.message}! Se configuró automáticamente como ejecutable activo.`;
        downloadFeedback.style.color = "var(--accent-green)";
        await loadInstalledJars();
        await fetchStatus();
      } else {
        downloadFeedback.textContent = `✗ Error: ${data.detail || "Fallo en descarga"}`;
        downloadFeedback.style.color = "var(--accent-red)";
      }
    } catch (err) {
      downloadFeedback.textContent = "✗ Error de conexión al descargar.";
      downloadFeedback.style.color = "var(--accent-red)";
    } finally {
      btnDownloadServer.disabled = false;
    }
  });

  // Start polling & ws
  connectWebSocket();
  fetchStatus();
  setInterval(fetchStatus, 2500);
});
