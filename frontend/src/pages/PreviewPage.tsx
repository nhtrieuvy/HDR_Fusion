import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { downloadArtifact, getArtifactAccess } from '../api/artifacts'
import type { Artifact } from '../api/types'
import { PageHeader } from '../components/common/PageHeader'
import { BeforeAfterViewer } from '../components/preview/BeforeAfterViewer'
import { ImageToolbar } from '../components/preview/ImageToolbar'
import { useJobPolling } from '../hooks/useJobPolling'
import { useAppStore } from '../store/appStore'

export function PreviewPage() {
  const { t } = useTranslation()
  const [zoom, setZoom] = useState(1)
  const [histogramEnabled, setHistogramEnabled] = useState(false)
  const currentJobId = useAppStore((state) => state.currentJobId ?? state.recentJobs[0]?.id)
  const polling = useJobPolling(currentJobId)
  const artifacts = polling.resultsQuery.data ?? []
  const finalArtifact =
    artifacts.find((artifact) => artifact.artifact_type === 'final_jpg') ??
    artifacts.find((artifact) => artifact.artifact_type === 'final_png') ??
    artifacts.find((artifact) => artifact.artifact_type === 'final_webp')
  const beforeArtifact = artifacts.find((artifact) => artifact.artifact_type.includes('source_preview'))
  const finalUrl = useArtifactUrl(finalArtifact)
  const beforeUrl = useArtifactUrl(beforeArtifact)

  return (
    <div className="space-y-6">
      <PageHeader
        title={t('preview.title')}
        description={t('preview.description')}
        actions={
          <ImageToolbar
            histogramEnabled={histogramEnabled}
            onDownload={finalArtifact ? () => void downloadArtifact(finalArtifact, finalArtifact.storage_key.split('/').pop() ?? finalArtifact.artifact_type) : undefined}
            onFit={() => setZoom(1)}
            onToggleHistogram={() => setHistogramEnabled((value) => !value)}
            onZoomIn={() => setZoom((value) => Math.min(2.5, Number((value + 0.1).toFixed(2))))}
            onZoomOut={() => setZoom((value) => Math.max(0.5, Number((value - 0.1).toFixed(2))))}
          />
        }
      />
      <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
        <BeforeAfterViewer afterUrl={finalUrl.data} beforeUrl={beforeUrl.data} zoom={zoom} />
        <div className="space-y-6">
          <aside className="surface-card h-fit rounded-3xl p-5">
            <h3 className="text-sm font-semibold text-white light:text-slate-950">{t('preview.metadata')}</h3>
            <div className="mt-5 space-y-4 text-sm">
              <Meta label={t('preview.inputFiles')} value={polling.jobQuery.data ? t('preview.rawBracketRange') : '-'} />
              <Meta label={t('preview.resolution')} value={finalArtifact?.width && finalArtifact.height ? `${finalArtifact.width} x ${finalArtifact.height}` : '-'} />
              <Meta label={t('preview.processingTime')} value="-" />
              <Meta label={t('preview.outputFormat')} value={finalArtifact?.mime_type ?? '-'} />
              <Meta label={t('preview.hdrScore')} value={t('preview.qcValue')} />
              <Meta label={t('preview.zoom')} value={`${Math.round(zoom * 100)}%`} />
            </div>
          </aside>
          {histogramEnabled ? <HistogramPanel /> : null}
        </div>
      </section>
    </div>
  )
}

function HistogramPanel() {
  const { t } = useTranslation()
  return (
    <div className="surface-card rounded-3xl p-5">
      <h3 className="text-sm font-semibold text-white light:text-slate-950">{t('preview.histogram')}</h3>
      <div className="mt-5 flex h-32 items-end gap-1 rounded-2xl border border-white/10 bg-slate-950/45 p-3 light:border-slate-200 light:bg-white">
        {Array.from({ length: 34 }).map((_, index) => (
          <span
            key={index}
            className="flex-1 rounded-t bg-gradient-to-t from-cyan-400 to-violet-400"
            style={{ height: `${20 + Math.abs(Math.sin(index * 0.55)) * 76}%` }}
          />
        ))}
      </div>
    </div>
  )
}

function Meta({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-2xl border border-white/8 bg-white/[0.03] p-3 light:border-slate-200 light:bg-white/70">
      <span className="text-slate-400 light:text-slate-600">{label}</span>
      <span className="text-right font-semibold text-white light:text-slate-950">{value}</span>
    </div>
  )
}

function useArtifactUrl(artifact?: Artifact) {
  return useQuery({
    queryKey: ['preview-artifact-url', artifact?.id],
    queryFn: async () => {
      const access = await getArtifactAccess(artifact!.id)
      return access.url && !access.url.startsWith('local://') ? access.url : undefined
    },
    enabled: Boolean(artifact),
  })
}
