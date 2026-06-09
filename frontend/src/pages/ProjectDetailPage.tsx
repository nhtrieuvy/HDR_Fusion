import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { listProjects } from '../api/projects'
import { Button } from '../components/common/Button'
import { EmptyState } from '../components/common/EmptyState'
import { ErrorState } from '../components/common/ErrorState'
import { LoadingState } from '../components/common/LoadingState'
import { PageHeader } from '../components/common/PageHeader'
import { StatusBadge } from '../components/common/StatusBadge'
import { useAppStore } from '../store/appStore'
import { formatDateTime } from '../utils/format'

export function ProjectDetailPage() {
  const { t } = useTranslation()
  const { projectId } = useParams()
  const projectsQuery = useQuery({ queryKey: ['projects'], queryFn: () => listProjects() })
  const imageSets = useAppStore((state) => state.imageSets).filter((item) => item.project_id === projectId)
  const jobs = useAppStore((state) => state.recentJobs).filter((job) =>
    imageSets.some((imageSet) => imageSet.id === job.image_set_id),
  )

  if (projectsQuery.isLoading) return <LoadingState label={t('common.loading')} />
  if (projectsQuery.isError) return <ErrorState message={projectsQuery.error.message} />

  const project = projectsQuery.data?.find((item) => item.id === projectId)
  if (!project) return <EmptyState title={t('projects.notFoundTitle')} description={t('projects.notFoundDesc')} />

  return (
    <div className="space-y-6">
      <PageHeader
        title={project.name}
        description={project.description ?? `${t('common.created')} ${formatDateTime(project.created_at)}`}
        eyebrow={t('projects.project')}
        actions={
          <Link to={`/jobs/new?projectId=${project.id}`}>
            <Button type="button">{t('common.newJob')}</Button>
          </Link>
        }
      />

      <section className="surface-card rounded-[2rem] p-6">
        <h2 className="text-base font-semibold text-white light:text-slate-950">{t('projects.imageSets')}</h2>
        <div className="mt-4">
          {imageSets.length ? (
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {imageSets.map((imageSet) => (
                <div key={imageSet.id} className="rounded-3xl border border-white/10 bg-white/[0.04] p-5 light:border-slate-200 light:bg-white/80">
                  <div className="text-sm font-semibold text-white light:text-slate-950">{imageSet.name ?? imageSet.id}</div>
                  <div className="mt-1 text-xs text-slate-500">{formatDateTime(imageSet.created_at)}</div>
                  <div className="mt-3 text-xs font-medium text-slate-400">{t(`common.statusValues.${imageSet.status}`, { defaultValue: imageSet.status })}</div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState title={t('projects.noLocalImageSets')} description={t('projects.noLocalImageSetsDesc')} />
          )}
        </div>
      </section>

      <section className="surface-card rounded-[2rem] p-6">
        <h2 className="text-base font-semibold text-white light:text-slate-950">{t('projects.jobs')}</h2>
        <div className="mt-4">
          {jobs.length ? (
            <div className="divide-y divide-white/8 overflow-hidden rounded-3xl border border-white/10 bg-slate-950/35 light:divide-slate-200 light:border-slate-200 light:bg-white">
              {jobs.map((job) => (
                <Link key={job.id} className="flex items-center justify-between gap-4 p-4 transition hover:bg-white/[0.05] light:hover:bg-slate-50" to={`/jobs/${job.id}`}>
                  <div className="min-w-0">
                    <div className="truncate text-sm font-semibold text-white light:text-slate-950">{job.id}</div>
                    <div className="mt-1 text-xs text-slate-500">{t(`preset.names.${job.preset_name}`, { defaultValue: job.preset_name })}</div>
                  </div>
                  <StatusBadge status={job.status} />
                </Link>
              ))}
            </div>
          ) : (
            <EmptyState title={t('projects.noJobsLocal')} description={t('projects.noJobsLocalDesc')} />
          )}
        </div>
      </section>
    </div>
  )
}
