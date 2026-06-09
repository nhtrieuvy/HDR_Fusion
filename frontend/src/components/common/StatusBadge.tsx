import { CheckCircle2, CircleDashed, Clock3, Loader2, XCircle } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { JobStatus, StepStatus } from '../../api/types'
import { cn } from '../../utils/cn'

interface StatusBadgeProps {
  status: JobStatus | StepStatus
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const { t } = useTranslation()
  const normalized = String(status)
  const tone =
    normalized === 'completed'
      ? 'border-emerald-300/25 bg-emerald-400/12 text-emerald-200 light:bg-emerald-50 light:text-emerald-700'
      : normalized === 'running' || normalized === 'uploading'
        ? 'border-cyan-300/25 bg-cyan-400/12 text-cyan-200 light:bg-cyan-50 light:text-cyan-700'
        : normalized === 'queued' || normalized === 'pending'
          ? 'border-amber-300/25 bg-amber-400/12 text-amber-200 light:bg-amber-50 light:text-amber-700'
          : normalized === 'failed' || normalized === 'qc_failed'
            ? 'border-red-300/25 bg-red-400/12 text-red-200 light:bg-red-50 light:text-red-700'
            : normalized === 'uploaded'
              ? 'border-emerald-300/25 bg-emerald-400/12 text-emerald-200 light:bg-emerald-50 light:text-emerald-700'
              : 'border-violet-300/25 bg-violet-400/12 text-violet-200 light:bg-violet-50 light:text-violet-700'

  const Icon =
    normalized === 'completed'
      ? CheckCircle2
      : normalized === 'uploaded'
        ? CheckCircle2
        : normalized === 'running' || normalized === 'uploading'
        ? Loader2
        : normalized === 'failed' || normalized === 'qc_failed'
          ? XCircle
          : normalized === 'queued'
            ? Clock3
            : CircleDashed

  return (
    <span className={cn('inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold capitalize', tone)}>
      <Icon className={cn('h-3.5 w-3.5', (normalized === 'running' || normalized === 'uploading') && 'animate-spin')} />
      {statusLabel(normalized, t)}
    </span>
  )
}

function statusLabel(status: string, t: (key: string) => string) {
  if (status === 'completed') return t('common.completed')
  if (status === 'running') return t('common.running')
  if (status === 'uploading') return t('common.statusValues.uploading')
  if (status === 'uploaded') return t('common.statusValues.uploaded')
  if (status === 'queued') return t('common.queued')
  if (status === 'pending') return t('common.pending')
  if (status === 'failed' || status === 'qc_failed') return t('common.failed')
  if (status === 'manual_review') return t('common.manualReview')
  if (status === 'skipped') return t('common.skipped')
  return t('common.unknown')
}
