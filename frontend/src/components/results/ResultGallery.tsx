import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import type { Artifact, QCReport } from '../../api/types'
import { fetchJsonArtifact, getArtifactAccess } from '../../api/artifacts'
import { candidateDisplayName } from '../../utils/displayNames'
import { EmptyState } from '../common/EmptyState'
import { BeforeAfterSlider } from './BeforeAfterSlider'
import { CandidateSelector } from './CandidateSelector'
import { DownloadButtons } from './DownloadButtons'

interface ResultGalleryProps {
  artifacts: Artifact[]
  qcReport?: QCReport | null
}

export function ResultGallery({ artifacts, qcReport }: ResultGalleryProps) {
  const { t } = useTranslation()
  const finalArtifact =
    artifacts.find((artifact) => artifact.artifact_type === 'final_jpg') ??
    artifacts.find((artifact) => artifact.artifact_type === 'final_png') ??
    artifacts.find((artifact) => artifact.artifact_type === 'final_webp')
  const before = artifacts.find((artifact) => artifact.artifact_type.includes('source_preview'))
  const qcArtifact = artifacts.find((artifact) => artifact.artifact_type === 'qc_report')

  const finalAccess = useArtifactUrl(finalArtifact?.id)
  const beforeAccess = useArtifactUrl(before?.id)
  const qcQuery = useQuery({
    queryKey: ['result-qc-report', qcArtifact?.id],
    queryFn: () => fetchJsonArtifact(qcArtifact!),
    enabled: !qcReport && Boolean(qcArtifact),
  })
  const effectiveQc = qcReport ?? (qcQuery.data as QCReport | undefined)

  if (!artifacts.length) {
    return <EmptyState title={t('results.noResults')} description={t('results.noResultsDesc')} />
  }

  const selectedCandidate = effectiveQc?.selected_candidate
  const selectedCandidateLabel = selectedCandidate ? candidateDisplayName(t, selectedCandidate) : t('common.notReported')

  return (
    <div className="space-y-6">
      <div>
        <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
          <div>
              <h3 className="text-sm font-semibold text-white light:text-slate-950">{t('results.finalOutput')}</h3>
              <p className="text-xs text-slate-500">
              {t('results.selectedCandidate')}: {selectedCandidateLabel}
            </p>
          </div>
          <DownloadButtons artifacts={artifacts} />
        </div>
        <BeforeAfterSlider beforeUrl={beforeAccess.data} afterUrl={finalAccess.data} />
      </div>

      <div>
        <h3 className="mb-3 text-sm font-semibold text-white light:text-slate-950">{t('results.candidateImages')}</h3>
        <CandidateSelector artifacts={artifacts} selectedCandidate={effectiveQc?.selected_candidate} />
      </div>
    </div>
  )
}

function useArtifactUrl(artifactId: string | undefined) {
  return useQuery({
    queryKey: ['artifact-url', artifactId],
    queryFn: async () => {
      const access = await getArtifactAccess(artifactId!)
      if (!access.url || access.url.startsWith('local://')) return undefined
      return access.url
    },
    enabled: Boolean(artifactId),
    staleTime: 5 * 60 * 1000,
  })
}
