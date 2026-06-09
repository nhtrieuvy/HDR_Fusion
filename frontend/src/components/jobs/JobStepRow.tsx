import { ChevronDown } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { JobStep } from '../../api/types'
import { compactNumber, formatDuration } from '../../utils/format'
import { stepStatusTone } from '../../utils/status'

interface JobStepRowProps {
  step: JobStep
}

export function JobStepRow({ step }: JobStepRowProps) {
  const { t } = useTranslation()
  const warningsCount = Array.isArray(step.warnings) ? step.warnings.length : step.warnings ? 1 : 0
  const metricsSummary = summarizeMetrics(step.metrics)

  return (
    <details className="group rounded-lg border border-neutral-200 bg-white">
      <summary className="grid cursor-pointer list-none items-center gap-3 px-4 py-3 md:grid-cols-[18px_1fr_100px_90px_90px_24px]">
        <span className={`h-3 w-3 rounded-full ${stepStatusTone(step.status)}`} />
        <div className="min-w-0">
          <div className="truncate text-sm font-semibold text-neutral-950">{step.step_name}</div>
          {metricsSummary ? <div className="mt-1 truncate text-xs text-neutral-500">{metricsSummary}</div> : null}
        </div>
        <span className="text-xs font-medium text-neutral-600">{t(`common.statusValues.${step.status}`, { defaultValue: t('common.unknown') })}</span>
        <span className="text-xs text-neutral-500">{compactNumber(step.progress)}%</span>
        <span className="text-xs text-neutral-500">{formatDuration(step.started_at, step.completed_at)}</span>
        <ChevronDown className="h-4 w-4 text-neutral-400 transition group-open:rotate-180" />
      </summary>
      <div className="border-t border-neutral-100 p-4">
        {warningsCount > 0 ? (
          <div className="mb-3 rounded-md border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">
            {t('common.warningCount', { count: warningsCount })}
          </div>
        ) : null}
        {step.error_message ? (
          <div className="mb-3 rounded-md border border-red-200 bg-red-50 p-3 text-xs text-red-800">
            {step.error_message}
          </div>
        ) : null}
        <div className="grid gap-3 lg:grid-cols-2">
          <JsonBlock label={t('job.metrics')} value={step.metrics} />
          <JsonBlock label={t('job.artifacts')} value={step.artifacts} />
        </div>
      </div>
    </details>
  )
}

function summarizeMetrics(metrics: JobStep['metrics']): string {
  if (!metrics || typeof metrics !== 'object' || Array.isArray(metrics)) return ''
  const entries = Object.entries(metrics).slice(0, 3)
  return entries.map(([key, value]) => `${key}: ${String(value).slice(0, 24)}`).join(' · ')
}

function JsonBlock({ label, value }: { label: string; value: unknown }) {
  return (
    <div>
      <div className="mb-1 text-xs font-semibold uppercase text-neutral-500">{label}</div>
      <pre className="max-h-72 overflow-auto rounded-md bg-neutral-950 p-3 text-xs text-neutral-100">
        {JSON.stringify(value ?? {}, null, 2)}
      </pre>
    </div>
  )
}
