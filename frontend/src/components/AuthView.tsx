/**
 * Vista de autenticación y configuración inicial de Foxden.
 * Muestra el asistente de creación de administrador en el primer arranque
 * o la pantalla de inicio de sesión para proteger el panel expuesto a la red/internet.
 */

import React, { useState } from 'react';
import { Lock, User, KeyRound, ShieldAlert, Eye, EyeOff, ArrowRight, Loader2, CheckCircle2 } from 'lucide-react';
import { api } from '../services/api';

interface AuthViewProps {
  setupRequired: boolean;
  onAuthSuccess: (username: string) => void;
}

export const AuthView: React.FC<AuthViewProps> = ({ setupRequired, onAuthSuccess }) => {
  const [username, setUsername] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [confirmPassword, setConfirmPassword] = useState<string>('');
  const [showPassword, setShowPassword] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const userClean = username.trim();
    if (!userClean || userClean.length < 3) {
      setError('El nombre de usuario debe contener al menos 3 caracteres.');
      return;
    }

    if (!password || password.length < 4) {
      setError('La contraseña debe contener al menos 4 caracteres.');
      return;
    }

    if (setupRequired && password !== confirmPassword) {
      setError('Las contraseñas no coinciden. Por favor verifícalas.');
      return;
    }

    setLoading(true);
    try {
      if (setupRequired) {
        const res = await api.configurarAdmin({ username: userClean, password });
        onAuthSuccess(res.username || userClean);
      } else {
        const res = await api.iniciarSesion({ username: userClean, password });
        onAuthSuccess(res.username || userClean);
      }
    } catch (err: any) {
      setError(err.message || 'Error al procesar la autenticación');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-dark-900 px-4 py-8 select-none">
      {/* Tarjeta de Autenticación */}
      <div className="w-full max-w-md bg-dark-800/90 border border-dark-700/80 rounded-2xl p-7 sm:p-8 backdrop-blur shadow-2xl relative overflow-hidden">
        {/* Glow de acento superior */}
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-fox-500 via-amber-500 to-fox-600" />

        {/* Encabezado con Logotipo */}
        <div className="flex flex-col items-center text-center mb-6">
          <div className="w-14 h-14 rounded-2xl bg-fox-500/10 border border-fox-500/20 p-2.5 flex items-center justify-center shadow-inner mb-3">
            <img src="/logo.png" alt="Foxden Logo" className="w-full h-full object-contain drop-shadow" />
          </div>

          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold tracking-wider uppercase mb-2 bg-fox-500/15 text-fox-400 border border-fox-500/25">
            {setupRequired ? (
              <>
                <KeyRound className="w-3 h-3" />
                Primer Arranque
              </>
            ) : (
              <>
                <Lock className="w-3 h-3" />
                Acceso Protegido
              </>
            )}
          </div>

          <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
            {setupRequired ? 'Configurar Administrador' : 'Iniciar Sesión en Foxden'}
          </h2>
          <p className="text-xs text-slate-400 mt-1.5 max-w-sm">
            {setupRequired
              ? 'Define el usuario y contraseña maestro para salvaguardar la consola y el túnel público del servidor.'
              : 'Ingresa tus credenciales de administrador para acceder al panel de control de Minecraft.'}
          </p>
        </div>

        {/* Mensaje de Error */}
        {error && (
          <div className="mb-5 bg-rose-500/15 border border-rose-500/30 text-rose-300 rounded-xl p-3 text-xs flex items-start gap-2.5">
            <ShieldAlert className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
            <div className="flex-1 leading-relaxed">{error}</div>
          </div>
        )}

        {/* Formulario */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Campo Usuario */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              Nombre de Usuario
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                <User className="w-4 h-4" />
              </div>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="ej. admin"
                autoComplete="username"
                autoFocus
                required
                className="w-full pl-10 pr-3.5 py-2.5 bg-dark-750 border border-dark-700 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-fox-500 transition-colors"
              />
            </div>
          </div>

          {/* Campo Contraseña */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              Contraseña
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                <Lock className="w-4 h-4" />
              </div>
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                autoComplete={setupRequired ? 'new-password' : 'current-password'}
                required
                className="w-full pl-10 pr-10 py-2.5 bg-dark-750 border border-dark-700 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-fox-500 transition-colors"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-200 transition-colors"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {/* Campo Confirmar Contraseña (solo primer arranque) */}
          {setupRequired && (
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Confirmar Contraseña
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                  <CheckCircle2 className="w-4 h-4" />
                </div>
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••"
                  autoComplete="new-password"
                  required
                  className="w-full pl-10 pr-3.5 py-2.5 bg-dark-750 border border-dark-700 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-fox-500 transition-colors"
                />
              </div>
            </div>
          )}

          {/* Botón de Envío */}
          <button
            type="submit"
            disabled={loading}
            className="w-full mt-2 py-2.5 px-4 rounded-xl font-semibold text-sm transition-all shadow-md bg-fox-500 hover:bg-fox-600 active:scale-[0.98] text-white flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>{setupRequired ? 'Configurando...' : 'Verificando...'}</span>
              </>
            ) : (
              <>
                <span>{setupRequired ? 'Crear Administrador y Entrar' : 'Entrar al Panel'}</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>

        {/* Nota al pie */}
        <div className="mt-6 text-center text-[11px] text-slate-500">
          Foxden Minecraft Manager • Sesión segura con cifrado PBKDF2
        </div>
      </div>
    </div>
  );
};
