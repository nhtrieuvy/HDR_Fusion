import { AlertCircle, CheckCircle2, CircleDashed, Loader2 } from 'lucide-react'
import { motion } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import type { JobStep, StepStatus } from '../../api/types'
import { cn } from '../../utils/cn'

const pipeline = [
  { key: 'decode', backend: ['raw_decode', 'decode'] },
  { key: 'exposure', backend: ['reference', 'exposure'] },
  { key: 'source', backend: ['typed_source', 'source_truth'] },
  { key: 'compositor', backend: ['compositor'] },
  { key: 'deglare', backend: ['deglare', 'finishing'] },
  { key: 'amaze', backend: ['amaze', 'demosaic', 'radiance_safety'] },
  { key: 'merge', backend: ['merge'] },
  { key: 'tonemap', backend: ['tonemap', 'finishing'] },
  { key: 'export', backend: ['export'] },
]

interface PipelineTimelineProps {
  steps?: JobStep[]
  progress?: number
}

export function PipelineTimeline({ steps = [], progress = 0 }: PipelineTimelineProps) {
  const { t } = useTranslation()

  return (
    <div className="surface-card rounded-3xl p-5">
      <div className="mb-5 flex items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-white light:text-slate-950">{t('processing.title')}</h3>
          <p className="mt-1 text-xs text-slate-400 light:text-slate-600">{Math.round(progress)}% {t('common.progress').toLowerCase()}</p>
        </div>
        <div className="h-2 w-36 overflow-hidden rounded-full bg-white/10 light:bg-slate-200">
          <motion.div
            className="h-full rounded-full bg-gradient-to-r from-cyan-300 to-violet-400"
            initial={{ width: 0 }}
            animate={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
          />
        </div>
      </div>

      <div className="space-y-3">
        {pipeline.map((item, index) => {
          const step = findStep(steps, item.backend)
          const status = inferStatus(step?.status, index, progress)
          const Icon = status === 'completed' ? CheckCircle2 : status === 'running' ? Loader2 : status === 'failed' ? AlertCircle : CircleDashed
          return (
            <motion.div
              key={item.key}
              className={cn(
                'flex items-center gap-3 rounded-2xl border p-3 transition',
                status === 'running'
                  ? 'border-cyan-300/25 bg-cyan-300/10'
                  : status === 'completed'
                    ? 'border-emerald-300/18 bg-emerald-300/7'
                    : status === 'failed'
                      ? 'border-red-300/25 bg-red-400/10'
                      : 'border-white/8 bg-white/[0.03] light:border-slate-200 light:bg-white/70',
              )}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.025 }}
            >
              <div className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-white/7 light:bg-slate-100">
                <Icon className={cn('h-4 w-4', status === 'running' && 'animate-spin text-cyan-300')} />
              </div>
              <div className="min-w-0 flex-1">
                <div className="truncate text-sm font-semibold text-white light:text-slate-950">{t(`processing.steps.${item.key}`)}</div>
                <div className="mt-0.5 text-xs text-slate-400 light:text-slate-600">{t(`common.statusValues.${status}`, { defaultValue: t('common.unknown') })}</div>
              </div>
            </motion.div>
          )
        })}
      </div>
    </div>
  )
}

function findStep(steps: JobStep[], tokens: string[]) {
  return steps.find((step) => tokens.some((token) => step.step_name.toLowerCase().includes(token)))
}

function inferStatus(status: StepStatus | undefined, index: number, progress: number): StepStatus {
  if (status) return status
  const threshold = ((index + 1) / pipeline.length) * 100
  const previous = (index / pipeline.length) * 100
  if (progress >= threshold) return 'completed'
  if (progress >= previous && progress < threshold && progress > 0) return 'running'
  return 'pending'
}
