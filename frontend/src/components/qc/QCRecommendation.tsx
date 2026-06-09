import { AlertTriangle, CheckCircle2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { QCReport } from '../../api/types'

interface QCRecommendationProps {
  report?: QCReport | null
}

export function QCRecommendation({ report }: QCRecommendationProps) {
  const { t } = useTranslation()
  const status = report?.status ?? 'unknown'
  const pass = status === 'pass'
  const recommendation = report?.recommended_action
    ? t(`qc.actions.${report.recommended_action}`, { defaultValue: recommendedAction(status, t) })
    : recommendedAction(status, t)

  return (
    <div
      className={`rounded-2xl border p-4 ${
        pass
          ? 'border-emerald-300/25 bg-emerald-400/10 text-emerald-100 light:border-emerald-200 light:bg-emerald-50 light:text-emerald-900'
          : 'border-amber-300/25 bg-amber-400/10 text-amber-100 light:border-amber-200 light:bg-amber-50 light:text-amber-900'
      }`}
    >
      <div className="flex items-center gap-2 text-sm font-semibold">
        {pass ? <CheckCircle2 className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />}
        {t('qc.status')}: {t(`common.statusValues.${status}`, { defaultValue: t('common.unknown') })}
      </div>
      <p className="mt-1 text-sm">{recommendation}</p>
    </div>
  )
}

function recommendedAction(status: string, t: (key: string) => string): string {
  if (status === 'qc_failed') return t('qc.retryArtifactSafe')
  if (status === 'manual_review') return t('qc.manualReview')
  if (status === 'warning') return t('qc.warning')
  return t('qc.noAction')
}
