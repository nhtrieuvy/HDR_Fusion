export function formatDateTime(value: string | null | undefined): string {
  if (!value) return '-'
  return new Intl.DateTimeFormat(undefined, {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

export function formatDuration(start: string | null, end: string | null): string {
  if (!start || !end) return '-'
  const milliseconds = new Date(end).getTime() - new Date(start).getTime()
  if (!Number.isFinite(milliseconds) || milliseconds < 0) return '-'
  if (milliseconds < 1000) return `${milliseconds} ms`
  return `${(milliseconds / 1000).toFixed(1)} s`
}

export function percent(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return '-'
  return `${Math.round(value)}%`
}

export function compactNumber(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return '-'
  return new Intl.NumberFormat(undefined, { maximumFractionDigits: 3 }).format(value)
}
