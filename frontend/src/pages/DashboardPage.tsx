import { useQuery } from '@tanstack/react-query'
import { Activity, ArrowRight, CheckCircle2, Clock3, ImageUp, Sparkles, XCircle } from 'lucide-react'
import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { listJobs } from '../api/jobs'
import { listProjects } from '../api/projects'
import { Button } from '../components/common/Button'
import { EmptyState } from '../components/common/EmptyState'
import { LoadingState } from '../components/common/LoadingState'
import { PageHeader } from '../components/common/PageHeader'
import { StatusBadge } from '../components/common/StatusBadge'
import { useAppStore } from '../store/appStore'
import { formatDateTime, formatDuration } from '../utils/format'

export function DashboardPage() {
  const { t } = useTranslation()
  const projectsQuery = useQuery({ queryKey: ['projects'], queryFn: () => listProjects() })
  const setRecentJobs = useAppStore((state) => state.setRecentJobs)
  const jobsQuery = useQuery({
    queryKey: ['jobs', 'recent'],
    queryFn: () => listJobs(100),
  })
  const recentJobs = jobsQuery.data ?? []
  useEffect(() => {
    if (jobsQuery.data) setRecentJobs(jobsQuery.data)
  }, [jobsQuery.data, setRecentJobs])
  const completed = recentJobs.filter((job) => job.status === 'completed').length
  const failed = recentJobs.filter((job) => job.status === 'failed' || job.status === 'qc_failed').length

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow={t('app.name')}
        title={t('dashboard.title')}
        description={t('dashboard.description')}
        actions={
          <Link to="/upload">
            <Button type="button" variant="primary">
              <ImageUp className="h-4 w-4" />
              {t('dashboard.quickAction')}
            </Button>
          </Link>
        }
      />

      <section className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="glass-panel overflow-hidden rounded-[2rem] p-7">
          <div className="max-w-2xl">
            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-cyan-300/20 bg-cyan-300/10 px-3 py-1 text-xs font-semibold text-cyan-200">
              <Sparkles className="h-3.5 w-3.5" />
              {t('app.labTitle')}
            </div>
            <h2 className="text-3xl font-semibold leading-tight text-white light:text-slate-950 md:text-5xl">
              {t('dashboard.heroTitle')}
            </h2>
            <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-400 light:text-slate-600">{t('dashboard.heroCopy')}</p>
          </div>
          <div className="mt-8 grid gap-3 md:grid-cols-3">
            <MetricCard icon={Activity} label={t('dashboard.totalJobs')} value={recentJobs.length.toString()} />
            <MetricCard icon={CheckCircle2} label={t('dashboard.completed')} value={completed.toString()} />
            <MetricCard icon={XCircle} label={t('dashboard.failed')} value={failed.toString()} />
          </div>
        </div>

        <div className="surface-card rounded-[2rem] p-6">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white light:text-slate-950">{t('dashboard.lastRun')}</h3>
            <Clock3 className="h-4 w-4 text-cyan-300" />
          </div>
          {jobsQuery.isLoading ? <LoadingState label={t('common.loading')} /> : null}
          {recentJobs[0] ? (
            <Link className="mt-5 block rounded-3xl border border-white/10 bg-white/[0.04] p-5 transition hover:bg-white/[0.07] light:border-slate-200 light:bg-white light:hover:bg-slate-50" to={`/jobs/${recentJobs[0].id}`}>
              <div className="flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold text-white light:text-slate-950">{recentJobs[0].id}</p>
                  <p className="mt-1 text-xs text-slate-400">{formatDateTime(recentJobs[0].created_at)}</p>
                </div>
                <StatusBadge status={recentJobs[0].status} />
              </div>
              <div className="mt-4 h-2 overflow-hidden rounded-full bg-white/10 light:bg-slate-200">
                <div className="h-full rounded-full bg-gradient-to-r from-cyan-300 to-violet-400" style={{ width: `${recentJobs[0].progress}%` }} />
              </div>
            </Link>
          ) : !jobsQuery.isLoading ? (
            <EmptyState title={t('dashboard.noJobs')} description={t('dashboard.heroCopy')} />
          ) : null}
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-2">
        <div className="surface-card rounded-[2rem] p-6">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-base font-semibold text-white light:text-slate-950">{t('dashboard.recentProjects')}</h3>
            <Link className="text-sm font-semibold text-cyan-300 light:text-cyan-700" to="/projects">
              {t('common.view')}
            </Link>
          </div>
          {projectsQuery.isLoading ? <LoadingState label={t('common.loading')} /> : null}
          {projectsQuery.data?.length ? (
            <div className="space-y-2">
              {projectsQuery.data.slice(0, 5).map((project) => (
                <Link key={project.id} className="flex items-center justify-between rounded-2xl border border-white/8 bg-white/[0.03] p-4 transition hover:bg-white/[0.06] light:border-slate-200 light:bg-white/80" to={`/projects/${project.id}`}>
                  <div>
                    <p className="text-sm font-semibold text-white light:text-slate-950">{project.name}</p>
                    <p className="mt-1 text-xs text-slate-400 light:text-slate-600">{formatDateTime(project.created_at)}</p>
                  </div>
                  <ArrowRight className="h-4 w-4 text-slate-500" />
                </Link>
              ))}
            </div>
          ) : !projectsQuery.isLoading ? (
            <EmptyState title={t('dashboard.noProjects')} />
          ) : null}
        </div>

        <div className="surface-card rounded-[2rem] p-6">
          <h3 className="mb-4 text-base font-semibold text-white light:text-slate-950">{t('dashboard.recentJobs')}</h3>
          {jobsQuery.isLoading ? <LoadingState label={t('common.loading')} /> : null}
          {recentJobs.length ? (
            <div className="space-y-2">
              {recentJobs.slice(0, 6).map((job) => (
                <Link key={job.id} className="grid gap-3 rounded-2xl border border-white/8 bg-white/[0.03] p-4 transition hover:bg-white/[0.06] light:border-slate-200 light:bg-white/80 md:grid-cols-[1fr_auto_auto]" to={`/jobs/${job.id}`}>
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-white light:text-slate-950">{job.id}</p>
                    <p className="mt-1 text-xs text-slate-400 light:text-slate-600">{t(`preset.names.${job.preset_name}`, { defaultValue: job.preset_name })}</p>
                  </div>
                  <StatusBadge status={job.status} />
                  <span className="text-xs text-slate-400 light:text-slate-600">{formatDuration(job.started_at, job.completed_at)}</span>
                </Link>
              ))}
            </div>
          ) : !jobsQuery.isLoading ? (
            <EmptyState title={t('dashboard.noJobs')} />
          ) : null}
        </div>
      </section>
    </div>
  )
}

function MetricCard({ icon: Icon, label, value }: { icon: typeof Activity; label: string; value: string }) {
  return (
    <div className="rounded-3xl border border-white/10 bg-white/[0.05] p-5 light:border-slate-200 light:bg-white/80">
      <Icon className="h-5 w-5 text-cyan-300" />
      <div className="mt-4 text-3xl font-semibold text-white light:text-slate-950">{value}</div>
      <div className="mt-1 text-xs font-medium text-slate-400 light:text-slate-600">{label}</div>
    </div>
  )
}
