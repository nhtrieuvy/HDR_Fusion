import { useTranslation } from 'react-i18next'
import { progressLabelKey } from '../../utils/status'

interface JobProgressBarProps {
  progress: number
}

export function JobProgressBar({ progress }: JobProgressBarProps) {
  const { t } = useTranslation()
  const value = Math.max(0, Math.min(100, progress || 0))
  return (
    <div>
      <div className="mb-2 flex items-center justify-between text-xs text-neutral-600">
        <span>{t(`progress.${progressLabelKey(value)}`)}</span>
        <span className="font-semibold text-neutral-900">{Math.round(value)}%</span>
      </div>
      <div className="h-3 overflow-hidden rounded-full bg-neutral-200">
        <div className="h-full rounded-full bg-teal-700 transition-all" style={{ width: `${value}%` }} />
      </div>
    </div>
  )
}
