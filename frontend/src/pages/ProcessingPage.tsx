import { Activity } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Button } from '../components/common/Button'
import { EmptyState } from '../components/common/EmptyState'
import { PageHeader } from '../components/common/PageHeader'
import { JobProgress } from '../components/processing/JobProgress'
import { LogPanel } from '../components/processing/LogPanel'
import { PipelineTimeline } from '../components/processing/PipelineTimeline'
import { useJobPolling } from '../hooks/useJobPolling'
import { useAppStore } from '../store/appStore'

export function ProcessingPage() {
  const { t } = useTranslation()
  const recentJobs = useAppStore((state) => state.recentJobs)
  const currentJobId = useAppStore((state) => state.currentJobId ?? state.recentJobs[0]?.id)
  const polling = useJobPolling(currentJobId)
  const job = polling.jobQuery.data ?? recentJobs.find((item) => item.id === currentJobId)
  const steps = polling.stepsQuery.data ?? []

  return (
    <div className="space-y-6">
      <PageHeader title={t('processing.title')} description={t('processing.description')} eyebrow={t('app.pipeline')} />

      {!job ? (
        <EmptyState
          icon={Activity}
          title={t('processing.noJob')}
          description={t('processing.noJobDesc')}
          action={
            <Link to="/upload">
              <Button type="button">{t('common.newJob')}</Button>
            </Link>
          }
        />
      ) : (
        <section className="grid gap-6 xl:grid-cols-[420px_1fr]">
          <div className="space-y-6">
            <div className="surface-card rounded-3xl p-5">
              <div className="flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold text-white light:text-slate-950">{job.id}</p>
                  <p className="mt-1 text-xs text-slate-400">{t(`preset.names.${job.preset_name}`, { defaultValue: job.preset_name })}</p>
                </div>
                <span className="text-2xl font-semibold text-cyan-200">{Math.round(job.progress)}%</span>
              </div>
              <div className="mt-5">
                <JobProgress value={job.progress} />
              </div>
            </div>
            <PipelineTimeline progress={job.progress} steps={steps} />
          </div>
          <LogPanel job={job} steps={steps} />
        </section>
      )}
    </div>
  )
}
