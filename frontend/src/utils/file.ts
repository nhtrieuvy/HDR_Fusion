export const RAW_EXTENSIONS = ['.dng', '.cr2', '.cr3', '.nef', '.arw', '.raf', '.rw2', '.orf', '.pef']

export function fileExtension(filename: string): string {
  const index = filename.lastIndexOf('.')
  return index >= 0 ? filename.slice(index).toLowerCase() : ''
}

export function isRawFile(file: File): boolean {
  return RAW_EXTENSIONS.includes(fileExtension(file.name))
}

export function formatBytes(bytes: number | null | undefined): string {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let value = bytes
  let unitIndex = 0
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024
    unitIndex += 1
  }
  return `${value.toFixed(value >= 10 || unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`
}

export function totalFileSize(files: File[]): number {
  return files.reduce((sum, file) => sum + file.size, 0)
}
