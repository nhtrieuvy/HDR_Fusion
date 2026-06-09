export type UploadMode = 'direct' | 'presigned'

function cleanBaseUrl(rawValue: string | undefined): string {
  const value = rawValue?.trim() || '/v1'
  if (value === '/v1' || value.endsWith('/v1')) return value.replace(/\/$/, '')
  return `${value.replace(/\/$/, '')}/v1`
}

function parseBoolean(value: string | undefined, fallback: boolean): boolean {
  if (value == null) return fallback
  return ['1', 'true', 'yes', 'on'].includes(value.toLowerCase())
}

export const env = {
  apiBaseUrl: cleanBaseUrl(import.meta.env.VITE_API_BASE_URL),
  uploadMode: ((import.meta.env.VITE_UPLOAD_MODE as UploadMode | undefined) || 'direct') as UploadMode,
  enableDebugArtifacts: parseBoolean(import.meta.env.VITE_ENABLE_DEBUG_ARTIFACTS, true),
  pollIntervalMs: Number(import.meta.env.VITE_POLL_INTERVAL_MS || 2000),
  enableMockApi: parseBoolean(import.meta.env.VITE_ENABLE_MOCK_API, false),
}
