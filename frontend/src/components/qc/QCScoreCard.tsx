import { compactNumber } from '../../utils/format'

interface QCScoreCardProps {
  label: string
  value: unknown
}

export function QCScoreCard({ label, value }: QCScoreCardProps) {
  const numeric = typeof value === 'number' ? compactNumber(value) : String(value ?? '-')
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-3 light:border-slate-200 light:bg-white/80">
      <div className="text-xs font-medium uppercase text-slate-500">{label}</div>
      <div className="mt-2 text-lg font-semibold text-white light:text-slate-950">{numeric}</div>
    </div>
  )
}
