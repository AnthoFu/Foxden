import React from 'react';
import { Terminal, Send, Trash2, ArrowDownCircle } from 'lucide-react';
import { useConsole } from '../../hooks/useConsole';

export const ConsoleTab: React.FC = () => {
  const {
    logs,
    isConnected,
    autoscroll,
    setAutoscroll,
    command,
    setCommand,
    terminalEndRef,
    sendConsoleCommand,
    handleKeyDown,
    clearLogs,
  } = useConsole();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendConsoleCommand();
  };

  return (
    <div className="flex flex-col h-[calc(100vh-180px)] min-h-[500px] bg-dark-950 border border-dark-700 rounded-xl overflow-hidden shadow-xl">
      {/* Console Toolbar */}
      <div className="bg-dark-800 border-b border-dark-700 px-4 py-2.5 flex items-center justify-between text-xs">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-fox-400" />
          <span className="font-bold text-slate-300 tracking-wider">TERMINAL EN TIEMPO REAL</span>
          <span
            className={`flex items-center gap-1.5 ml-2 px-2 py-0.5 rounded-full border text-[11px] font-medium ${
              isConnected
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
            }`}
          >
            <span className={`w-1.5 h-1.5 rounded-full ${isConnected ? 'bg-emerald-400' : 'bg-rose-400'}`} />
            {isConnected ? 'WebSocket Conectado' : 'Reconectando...'}
          </span>
        </div>

        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 cursor-pointer text-slate-300 hover:text-white select-none">
            <input
              type="checkbox"
              checked={autoscroll}
              onChange={(e) => setAutoscroll(e.target.checked)}
              className="rounded bg-dark-900 border-dark-700 text-fox-500 focus:ring-fox-500 w-3.5 h-3.5"
            />
            <span className="flex items-center gap-1">
              <ArrowDownCircle className="w-3.5 h-3.5" />
              Auto-desplazamiento
            </span>
          </label>

          <button
            onClick={clearLogs}
            className="flex items-center gap-1 text-slate-400 hover:text-slate-200 transition-colors px-2 py-1 rounded hover:bg-dark-750"
            title="Limpiar registros en pantalla"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Limpiar</span>
          </button>
        </div>
      </div>

      {/* Terminal Output */}
      <div className="flex-1 p-4 overflow-y-auto font-mono text-[13px] bg-dark-950 text-sky-300 space-y-1">
        {logs.length === 0 ? (
          <div className="text-slate-600 italic py-8 text-center select-none font-sans">
            Esperando registros del servidor de Minecraft... Haz clic en Iniciar arriba para arrancar.
          </div>
        ) : (
          logs.map((line, idx) => {
            const isFoxden = line.includes('[FOXDEN]');
            const isError = line.includes('ERROR') || line.includes('Exception') || line.includes('CRASH');
            const isWarn = line.includes('WARN');
            const isReady = line.includes('EN LÍNEA') || line.includes('Done (');

            let color = 'text-slate-300';
            if (isFoxden) color = 'text-fox-400 font-semibold';
            if (isReady) color = 'text-emerald-400 font-bold';
            if (isWarn) color = 'text-amber-300';
            if (isError) color = 'text-rose-400 font-semibold';

            return (
              <div key={idx} className={`terminal-line ${color}`}>
                {line}
              </div>
            );
          })
        )}
        <div ref={terminalEndRef} />
      </div>

      {/* Command Input Form */}
      <form onSubmit={handleSubmit} className="bg-dark-800 border-t border-dark-700 p-2.5 flex items-center gap-2">
        <span className="text-fox-500 font-mono font-bold pl-2 select-none">&gt;</span>
        <input
          type="text"
          value={command}
          onChange={(e) => setCommand(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Escribe un comando de Minecraft (ej: op mi_usuario, help, time set day)..."
          className="flex-1 bg-dark-900 border border-dark-700 rounded-lg px-3 py-2 text-sm text-slate-100 font-mono focus:outline-none focus:border-fox-500 transition-colors placeholder:text-slate-500 placeholder:font-sans"
        />
        <button
          type="submit"
          disabled={!command.trim()}
          className="flex items-center gap-1.5 px-4 py-2 bg-fox-600 hover:bg-fox-500 disabled:opacity-40 text-white rounded-lg text-sm font-semibold transition-all active:scale-95 disabled:active:scale-100"
        >
          <span>Enviar</span>
          <Send className="w-3.5 h-3.5" />
        </button>
      </form>
    </div>
  );
};
