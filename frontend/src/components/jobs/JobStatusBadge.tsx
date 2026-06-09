import type { JobStatus } from '../../api/types'
import { useTranslation } from 'react-i18next'
import { cn } from '../../utils/cn'
import { jobStatusTone } from '../../utils/status'

interface JobStatusBadgeProps {
  status: JobStatus
}

export function JobStatusBadge({ status }: JobStatusBadgeProps) {
  const { t } = useTranslation()
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold',
        jobStatusTone(status),
      )}
    >
      {t(`common.statusValues.${status}`, { defaultValue: t('common.unknown') })}
    </span>
  )
}
