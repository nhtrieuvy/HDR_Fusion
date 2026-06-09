import type { JobStatus, StepStatus } from '../api/types'

export const TERMINAL_JOB_STATUSES = new Set<JobStatus>([
  'completed',
  'failed',
  'qc_failed',
  'manual_review',
  'cancelled',
])

export function isTerminalJobStatus(status: JobStatus | undefined): boolean {
  return Boolean(status && TERMINAL_JOB_STATUSES.has(status))
}

export function jobStatusTone(status: JobStatus): string {
  if (status === 'completed') return 'bg-emerald-100 text-emerald-800 border-emerald-200'
  if (status === 'running') return 'bg-teal-100 text-teal-800 border-teal-200'
  if (status === 'queued') return 'bg-amber-100 text-amber-800 border-amber-200'
  if (status === 'manual_review') return 'bg-orange-100 text-orange-800 border-orange-200'
  if (status === 'qc_failed' || status === 'failed') return 'bg-red-100 text-red-800 border-red-200'
  return 'bg-neutral-100 text-neutral-700 border-neutral-200'
}

export function stepStatusTone(status: StepStatus): string {
  if (status === 'completed') return 'bg-emerald-500'
  if (status === 'running') return 'bg-teal-500'
  if (status === 'failed') return 'bg-red-500'
  if (status === 'skipped') return 'bg-neutral-400'
  return 'bg-neutral-300'
}

export function progressLabelKey(progress: number): string {
  if (progress >= 100) return 'completed'
  if (progress >= 97) return 'exportComplete'
  if (progress >= 92) return 'qcComplete'
  if (progress >= 85) return 'finishingComplete'
  if (progress >= 78) return 'demosaicComplete'
  if (progress >= 70) return 'compositorSafetyComplete'
  if (progress >= 60) return 'rawMergeComplete'
  if (progress >= 50) return 'sourceTruthComplete'
  if (progress >= 40) return 'alignmentComplete'
  if (progress >= 30) return 'referenceExposureComplete'
  if (progress >= 20) return 'rawDecodeComplete'
  if (progress >= 10) return 'inputAuditComplete'
  if (progress >= 5) return 'jobInitialized'
  return 'queued'
}
