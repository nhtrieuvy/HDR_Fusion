import axios from 'axios'
import { env } from '../config/env'
import { getData } from './client'
import { mockDelay, readMockState } from './mock'
import type { Artifact, ArtifactAccess, JsonValue } from './types'

export async function getArtifactAccess(artifactId: string): Promise<ArtifactAccess> {
  if (env.enableMockApi) {
    const state = readMockState()
    const artifact = Object.values(state.artifacts)
      .flat()
      .find((item) => item.id === artifactId)
    if (!artifact) throw new Error('errors.artifactNotFound')
    return mockDelay({ artifact, url: '', method: 'GET' })
  }
  const access = await getData<ArtifactAccess>(`/artifacts/${artifactId}`)
  if (!access.url || access.url.startsWith('local://')) {
    return { ...access, url: artifactContentUrl(artifactId) }
  }
  return { ...access, url: resolveArtifactUrl(access.url) }
}

export async function fetchJsonArtifact(artifact: Artifact): Promise<JsonValue> {
  const access = await getArtifactAccess(artifact.id)
  if (!access.url) {
    throw new Error('errors.artifactUrlUnavailable')
  }
  const response = await axios.get<JsonValue>(access.url)
  return response.data
}

export async function downloadArtifact(artifact: Artifact, filename?: string): Promise<void> {
  const access = await getArtifactAccess(artifact.id)
  if (!access.url || access.url.startsWith('local://')) {
    throw new Error('errors.artifactUrlUnavailable')
  }
  const response = await axios.get<Blob>(withDownloadParam(access.url), { responseType: 'blob' })
  downloadBlob(response.data, filename ?? artifact.storage_key.split('/').pop() ?? artifact.artifact_type)
}

export async function downloadArtifactAsPng(artifact: Artifact, filename = 'hdr-reconstruction.png'): Promise<void> {
  const access = await getArtifactAccess(artifact.id)
  if (!access.url || access.url.startsWith('local://')) {
    throw new Error('errors.artifactUrlUnavailable')
  }
  const response = await axios.get<Blob>(access.url, { responseType: 'blob' })
  const sourceUrl = URL.createObjectURL(response.data)
  try {
    const image = await loadImage(sourceUrl)
    const canvas = document.createElement('canvas')
    canvas.width = image.naturalWidth
    canvas.height = image.naturalHeight
    const context = canvas.getContext('2d')
    if (!context) throw new Error('errors.canvasUnavailable')
    context.drawImage(image, 0, 0)
    const pngBlob = await new Promise<Blob>((resolve, reject) => {
      canvas.toBlob((blob) => (blob ? resolve(blob) : reject(new Error('errors.pngEncodeFailed'))), 'image/png')
    })
    downloadBlob(pngBlob, filename)
  } finally {
    URL.revokeObjectURL(sourceUrl)
  }
}

function downloadBlob(blob: Blob, filename: string): void {
  const objectUrl = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = objectUrl
  anchor.download = filename
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(objectUrl)
}

function loadImage(url: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const image = new Image()
    image.onload = () => resolve(image)
    image.onerror = () => reject(new Error('errors.imageLoadFailed'))
    image.src = url
  })
}

export function artifactGroupKey(type: string): string {
  if (type === 'final_jpg' || type === 'final_png' || type === 'final_webp' || type === 'final_tiff') return 'processedOutputs'
  if (type.startsWith('candidate_')) return 'candidates'
  if (type.startsWith('mask_') || type.includes('mask') || type.includes('amount')) return 'masks'
  if (type.includes('weight') || type.includes('rejection')) return 'weightMaps'
  if (type.includes('qc')) return 'qcReports'
  if (type.includes('debug') || type.includes('report')) return 'debugReports'
  if (type.includes('hdr') || type.includes('radiance') || type.includes('amaze')) return 'hdrBase'
  return 'other'
}

export function isImageArtifact(artifact: Artifact): boolean {
  return Boolean(artifact.mime_type?.startsWith('image/'))
}

export function isJsonArtifact(artifact: Artifact): boolean {
  return artifact.mime_type === 'application/json' || artifact.storage_key.endsWith('.json')
}

function artifactContentUrl(artifactId: string): string {
  return resolveArtifactUrl(`/v1/artifacts/${artifactId}/content`)
}

function resolveArtifactUrl(url: string): string {
  if (!url.startsWith('/')) return url
  if (env.apiBaseUrl.startsWith('http')) {
    return `${env.apiBaseUrl.replace(/\/v1$/, '')}${url}`
  }
  return url
}

function withDownloadParam(url: string): string {
  return `${url}${url.includes('?') ? '&' : '?'}download=true`
}
