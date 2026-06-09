import { Terminal } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { Job, JobStep } from '../../api/types'

interface LogPanelProps {
  job?: Job
  steps?: JobStep[]
}

export function LogPanel({ job, steps = [] }: LogPanelProps) {
  const { t } = useTranslation()
  const lines = [
    `[${t('log.system')}] ${job ? `${t('job.title')} ${job.id}` : t('log.waitingForJob')}`,
    `[${t('log.pipeline')}] raw_hdr_fusion · ${t('log.sourceAwareHdr')}`,
    ...steps
      .slice(-8)
      .map((step) => `[${t(`common.statusValues.${step.status}`, { defaultValue: t('common.unknown') })}] ${step.step_name} ${step.error_message ? `-> ${step.error_message}` : ''}`),
  ]

  return (
    <div className="surface-card overflow-hidden rounded-3xl">
      <div className="flex items-center gap-2 border-b border-white/10 px-5 py-4 light:border-slate-200">
        <Terminal className="h-4 w-4 text-cyan-300" />
        <h3 className="text-sm font-semibold text-white light:text-slate-950">{t('processing.terminal')}</h3>
      </div>
      <pre className="min-h-[260px] overflow-auto bg-slate-950/70 p-5 font-mono text-xs leading-6 text-cyan-100 light:bg-slate-950 light:text-cyan-100">
        {lines.join('\n')}
      </pre>
    </div>
  )
}
