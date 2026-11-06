/**
 * Utilidades de formateo para la interfaz de Foxden.
 */

/**
 * Convierte un total de segundos en una representación legible de tiempo transcurrido (ej. 1h 30m).
 */
export function formatearTiempoActivo(segundos: number): string {
  const s = Math.floor(segundos);
  const m = Math.floor(s / 60);
  const h = Math.floor(m / 60);

  if (h > 0) {
    return `${h}h ${m % 60}m`;
  }
  if (m > 0) {
    return `${m}m ${s % 60}s`;
  }
  return `${s}s`;
}

// Alias para compatibilidad
export const formatUptime = formatearTiempoActivo;
