import { useState } from 'react'
import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useQuery } from '@tanstack/react-query'
import { Eye } from 'lucide-react'
import { listJobs } from '../api/jobs'
import { Button } from '../components/common/Button'
import { EmptyState } from '../components/common/EmptyState'
import { LoadingState } from '../components/common/LoadingState'
import { PageHeader } from '../components/common/PageHeader'
import { StatusBadge } from '../components/common/StatusBadge'
import { useAppStore } from '../store/appStore'
import { formatDateTime, formatDuration } from '../utils/format'

export function HistoryPage() {
  const { t } = useTranslation()
  const [filter, setFilter] = useState('all')
  const setRecentJobs = useAppStore((state) => state.setRecentJobs)
  const jobsQuery = useQuery({ queryKey: ['jobs', 'history'], queryFn: () => listJobs(500) })
  const jobs = jobsQuery.data ?? []
  useEffect(() => {
    if (jobsQuery.data) setRecentJobs(jobsQuery.data)
  }, [jobsQuery.data, setRecentJobs])
  const filtered = filter === 'all' ? jobs : jobs.filter((job) => job.status === filter)

  return (
    <div className="space-y-6">
      <PageHeader title={t('history.title')} description={t('history.description')} />
      <div className="surface-card rounded-3xl p-5">
        <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-sm font-semibold text-white light:text-slate-950">{t('history.title')}</h2>
          <label>
            <span className="sr-only">{t('history.filter')}</span>
            <select className="field min-w-48" value={filter} onChange={(event) => setFilter(event.target.value)}>
              <option value="all">{t('history.all')}</option>
              <option value="completed">{t('common.completed')}</option>
              <option value="running">{t('common.running')}</option>
              <option value="failed">{t('common.failed')}</option>
              <option value="manual_review">{t('common.manualReview')}</option>
            </select>
          </label>
        </div>
        {jobsQuery.isLoading ? <LoadingState label={t('common.loading')} /> : null}
        {filtered.length ? (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead className="text-xs uppercase tracking-[0.16em] text-slate-500">
                <tr>
                  <th className="py-3">{t('history.jobName')}</th>
                  <th>{t('common.status')}</th>
                  <th>{t('common.preset')}</th>
                  <th>{t('history.createdAt')}</th>
                  <th>{t('common.duration')}</th>
                  <th>{t('common.action')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/8 light:divide-slate-200">
                {filtered.map((job) => (
                  <tr key={job.id}>
                    <td className="max-w-[280px] truncate py-4 font-semibold text-white light:text-slate-950">{job.id}</td>
                    <td><StatusBadge status={job.status} /></td>
                    <td className="text-slate-400 light:text-slate-600">{t(`preset.names.${job.preset_name}`, { defaultValue: job.preset_name })}</td>
                    <td className="text-slate-400 light:text-slate-600">{formatDateTime(job.created_at)}</td>
                    <td className="text-slate-400 light:text-slate-600">{formatDuration(job.started_at, job.completed_at)}</td>
                    <td>
                      <Link to={`/jobs/${job.id}`}>
                        <Button size="sm" type="button" variant="secondary">
                          <Eye className="h-4 w-4" />
                          {t('common.view')}
                        </Button>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : !jobsQuery.isLoading ? (
          <EmptyState title={t('dashboard.noJobs')} />
        ) : null}
      </div>
    </div>
  )
}
