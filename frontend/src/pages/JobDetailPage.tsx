import { useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { ArtifactBrowser } from '../components/artifacts/ArtifactBrowser'
import { ErrorState } from '../components/common/ErrorState'
import { LoadingState } from '../components/common/LoadingState'
import { PageHeader } from '../components/common/PageHeader'
import { StatusBadge } from '../components/common/StatusBadge'
import { JobActions } from '../components/jobs/JobActions'
import { JobProgress } from '../components/processing/JobProgress'
import { PipelineTimeline } from '../components/processing/PipelineTimeline'
import { QCPanel } from '../components/qc/QCPanel'
import { ResultGallery } from '../components/results/ResultGallery'
import { useJobPolling } from '../hooks/useJobPolling'
import { useAppStore } from '../store/appStore'
import { formatDateTime } from '../utils/format'

export function JobDetailPage() {
  const { t } = useTranslation()
  const { jobId } = useParams()
  const { jobQuery, stepsQuery, resultsQuery } = useJobPolling(jobId)
  const setCurrentJobId = useAppStore((state) => state.setCurrentJobId)

  useEffect(() => {
    if (jobId) setCurrentJobId(jobId)
  }, [jobId, setCurrentJobId])

  if (jobQuery.isLoading) return <LoadingState label={`${t('common.loading')} ${t('job.title').toLowerCase()}`} />
  if (jobQuery.isError) return <ErrorState message={jobQuery.error.message} title={t('job.cannotLoad')} />
  if (!jobQuery.data) return <ErrorState message={t('job.notFound')} />

  const job = jobQuery.data
  const artifacts = resultsQuery.data ?? []
  const qcReportArtifact = artifacts.find((artifact) => artifact.artifact_type === 'qc_report')

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow={t('job.eyebrow')}
        title={`${t('job.title')} ${job.id}`}
        description={`${job.pipeline_name} ${job.pipeline_version} · ${job.preset_name} ${job.preset_version}`}
        actions={<StatusBadge status={job.status} />}
      />

      <section className="glass-panel rounded-[2rem] p-6">
        <div className="grid gap-6 xl:grid-cols-[1fr_auto]">
          <div>
            <div className="grid gap-4 text-sm text-slate-400 light:text-slate-600 md:grid-cols-2 xl:grid-cols-4">
              <Info label={t('app.pipeline')} value={`${job.pipeline_name} ${job.pipeline_version}`} />
              <Info label={t('common.preset')} value={`${t(`preset.names.${job.preset_name}`, { defaultValue: job.preset_name })} ${job.preset_version}`} />
              <Info label={t('common.created')} value={formatDateTime(job.created_at)} />
              <Info label={t('common.completedAt')} value={formatDateTime(job.completed_at)} />
            </div>
            <div className="mt-6">
              <div className="mb-2 flex items-center justify-between text-xs text-slate-400">
                <span>{t('common.progress')}</span>
                <span>{Math.round(job.progress)}%</span>
              </div>
              <JobProgress value={job.progress} />
            </div>
          </div>
          <JobActions job={job} />
        </div>

        {job.error_message ? (
          <div className="mt-5">
            <ErrorState message={job.error_message} title={t('job.backendError')} />
          </div>
        ) : null}

        <details className="mt-5 overflow-hidden rounded-3xl border border-white/10 bg-slate-950/40 light:border-slate-200 light:bg-white">
          <summary className="cursor-pointer px-5 py-4 text-sm font-semibold text-white light:text-slate-950">{t('job.config')}</summary>
          <pre className="max-h-96 overflow-auto border-t border-white/10 bg-slate-950 p-5 text-xs text-slate-100">
            {JSON.stringify(job.config_snapshot ?? job.params ?? {}, null, 2)}
          </pre>
        </details>
      </section>

      <section className="grid gap-6 xl:grid-cols-[420px_1fr]">
        <PipelineTimeline progress={job.progress} steps={stepsQuery.data ?? []} />
        <div className="surface-card rounded-[2rem] p-6">
          <h2 className="mb-4 text-base font-semibold text-white light:text-slate-950">{t('job.results')}</h2>
          {resultsQuery.isLoading ? <LoadingState label={`${t('common.loading')} ${t('job.results').toLowerCase()}`} /> : null}
          {resultsQuery.isError ? <ErrorState message={resultsQuery.error.message} title={t('job.cannotLoadResults')} /> : null}
          <ResultGallery artifacts={artifacts} qcReport={qcReportArtifact ? undefined : null} />
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[420px_1fr]">
        <div className="surface-card rounded-[2rem] p-6">
          <h2 className="mb-4 text-base font-semibold text-white light:text-slate-950">{t('job.qc')}</h2>
          <QCPanel artifacts={artifacts} />
        </div>
        <div className="surface-card rounded-[2rem] p-6">
          <h2 className="mb-4 text-base font-semibold text-white light:text-slate-950">{t('job.artifacts')}</h2>
          <ArtifactBrowser artifacts={artifacts} />
        </div>
      </section>
    </div>
  )
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-white/8 bg-white/[0.03] p-4 light:border-slate-200 light:bg-white/70">
      <div className="text-xs uppercase tracking-[0.16em] text-slate-500">{label}</div>
      <div className="mt-2 break-words text-sm font-semibold text-white light:text-slate-950">{value}</div>
    </div>
  )
}
