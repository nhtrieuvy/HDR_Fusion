import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import type { Artifact, QCReport } from '../../api/types'
import { fetchJsonArtifact } from '../../api/artifacts'
import { EmptyState } from '../common/EmptyState'
import { ErrorState } from '../common/ErrorState'
import { LoadingState } from '../common/LoadingState'
import { QCRecommendation } from './QCRecommendation'
import { QCScoreCard } from './QCScoreCard'

interface QCPanelProps {
  artifacts: Artifact[]
}

export function QCPanel({ artifacts }: QCPanelProps) {
  const { t } = useTranslation()
  const qcArtifact = useMemo(() => artifacts.find((artifact) => artifact.artifact_type === 'qc_report'), [artifacts])
  const query = useQuery({
    queryKey: ['qc-report', qcArtifact?.id],
    queryFn: () => fetchJsonArtifact(qcArtifact!),
    enabled: Boolean(qcArtifact),
  })

  if (!qcArtifact) {
    return (
      <EmptyState
        title={t('qc.noReport')}
        description={t('qc.noReportDesc')}
      />
    )
  }

  if (query.isLoading) return <LoadingState label={t('qc.loading')} />
  if (query.isError) {
    return (
      <ErrorState
        title={t('qc.cannotLoad')}
        message={`${query.error.message}. ${t('qc.metadataBelow')}`}
      />
    )
  }

  const report = query.data as QCReport
  const metrics = report.metrics ?? {}
  const coreMetrics = [
    'final_highlight_clipping',
    'unrecoverable_source_clipping',
    'technical_clipping_after_processing',
    'halo_score',
    'ghosting_alignment_residual',
    'blur_sharpness',
    'shadow_noise',
    'color_cast',
    'magenta_green_artifact_risk',
    'mask_leak_risk',
    'window_exterior_detail_confidence',
    'overall_naturalness_score',
  ]

  return (
    <div className="space-y-4">
      <QCRecommendation report={report} />
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {coreMetrics.map((key) => (
          <QCScoreCard key={key} label={t(`qc.metrics.${key}`)} value={metrics[key]} />
        ))}
      </div>
      {Array.isArray(report.warnings) && report.warnings.length ? (
        <div className="rounded-2xl border border-amber-300/25 bg-amber-400/10 p-4">
          <div className="text-sm font-semibold text-amber-100 light:text-amber-900">{t('common.warnings')}</div>
          <ul className="mt-2 space-y-1 text-sm text-amber-100 light:text-amber-800">
            {report.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  )
}
