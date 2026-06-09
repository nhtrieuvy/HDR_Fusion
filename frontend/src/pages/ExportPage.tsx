import { Download, FileImage, RotateCcw } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { downloadArtifact, downloadArtifactAsPng, getArtifactAccess } from '../api/artifacts'
import type { Artifact } from '../api/types'
import { Button } from '../components/common/Button'
import { EmptyState } from '../components/common/EmptyState'
import { PageHeader } from '../components/common/PageHeader'
import { useJobPolling } from '../hooks/useJobPolling'
import { useAppStore } from '../store/appStore'
import { artifactDisplayName } from '../utils/displayNames'
import { formatBytes } from '../utils/file'

export function ExportPage() {
  const { t } = useTranslation()
  const [error, setError] = useState<string | null>(null)
  const currentJobId = useAppStore((state) => state.currentJobId ?? state.recentJobs[0]?.id)
  const polling = useJobPolling(currentJobId)
  const artifacts = polling.resultsQuery.data ?? []
  const exports = ['final_jpg', 'final_png', 'final_webp', 'final_tiff']
    .map((type) => artifacts.find((artifact) => artifact.artifact_type === type))
    .filter((artifact): artifact is Artifact => Boolean(artifact))
  const pngFallback =
    artifacts.find((artifact) => artifact.artifact_type === 'final_png') ??
    artifacts.find((artifact) => artifact.artifact_type === 'final_jpg') ??
    artifacts.find((artifact) => artifact.artifact_type === 'final_webp')

  return (
    <div className="space-y-6">
      <PageHeader title={t('export.title')} description={t('export.description')} />
      {exports.length ? (
        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {exports.map((artifact) => (
            <ExportCard key={artifact.id} artifact={artifact} />
          ))}
        </section>
      ) : (
        <EmptyState icon={FileImage} title={t('export.emptyTitle')} description={t('export.emptyDesc')} />
      )}
      <div className="flex flex-wrap gap-3">
        <FormatDownloadButton artifact={artifacts.find((artifact) => artifact.artifact_type === 'final_jpg')} format="jpg" onError={setError} />
        <FormatDownloadButton artifact={artifacts.find((artifact) => artifact.artifact_type === 'final_png')} fallbackArtifact={pngFallback} format="png" onError={setError} />
        <FormatDownloadButton artifact={artifacts.find((artifact) => artifact.artifact_type === 'final_webp')} format="webp" onError={setError} />
        <FormatDownloadButton artifact={artifacts.find((artifact) => artifact.artifact_type === 'final_tiff')} format="tiff" onError={setError} />
        <Link to="/upload">
          <Button type="button" variant="primary">
            <RotateCcw className="h-4 w-4" />
            {t('export.new')}
          </Button>
        </Link>
      </div>
      {error ? <div className="rounded-2xl border border-red-300/25 bg-red-400/10 p-4 text-sm text-red-200 light:bg-red-50 light:text-red-700">{error}</div> : null}
    </div>
  )
}

function FormatDownloadButton({
  artifact,
  fallbackArtifact,
  format,
  onError,
}: {
  artifact?: Artifact
  fallbackArtifact?: Artifact
  format: 'jpg' | 'png' | 'webp' | 'tiff'
  onError?: (message: string | null) => void
}) {
  const { t } = useTranslation()
  const sourceArtifact = artifact ?? (format === 'png' ? fallbackArtifact : undefined)
  const access = useQuery({
    queryKey: ['export-format-artifact-url', sourceArtifact?.id, format],
    queryFn: async () => getArtifactAccess(sourceArtifact!.id),
    enabled: Boolean(sourceArtifact),
  })

  async function handleDownload() {
    try {
      onError?.(null)
      if (!sourceArtifact) return
      if (format === 'png' && artifact?.artifact_type !== 'final_png') {
        await downloadArtifactAsPng(sourceArtifact, 'hdr-reconstruction.png')
      } else {
        await downloadArtifact(sourceArtifact, `hdr-reconstruction.${format}`)
      }
    } catch (error) {
      onError?.(error instanceof Error ? error.message : String(error))
    }
  }

  return (
    <Button disabled={!sourceArtifact || !access.data?.url} type="button" variant="secondary" onClick={handleDownload}>
      <Download className="h-4 w-4" />
      {format === 'jpg' ? t('export.jpg') : format === 'png' ? t('export.png') : format === 'webp' ? t('export.webp') : t('export.tiff')}
    </Button>
  )
}

function ExportCard({ artifact }: { artifact: Artifact }) {
  const { t } = useTranslation()
  const access = useQuery({
    queryKey: ['export-artifact-url', artifact.id],
    queryFn: async () => getArtifactAccess(artifact.id),
  })

  return (
    <div className="surface-card rounded-3xl p-5">
      <div className="grid h-12 w-12 place-items-center rounded-2xl bg-cyan-300/10 text-cyan-200">
        <FileImage className="h-5 w-5" />
      </div>
      <h3 className="mt-5 text-sm font-semibold text-white light:text-slate-950">{artifactDisplayName(t, artifact.artifact_type)}</h3>
      <p className="mt-1 text-xs text-slate-400">{formatBytes(artifact.file_size)}</p>
      <Button
        className="mt-5 w-full"
        disabled={!access.data?.url || access.data.url.startsWith('local://')}
        type="button"
        variant="primary"
        onClick={() => void downloadArtifact(artifact, artifact.storage_key.split('/').pop() ?? artifact.artifact_type)}
      >
          <Download className="h-4 w-4" />
        {t('common.download')}
      </Button>
    </div>
  )
}
