import type { ReactNode } from 'react'
import type { LucideIcon } from 'lucide-react'
import { Inbox } from 'lucide-react'

interface EmptyStateProps {
  title: string
  description?: string
  icon?: LucideIcon
  action?: ReactNode
}

export function EmptyState({ title, description, icon: Icon = Inbox, action }: EmptyStateProps) {
  return (
    <div className="image-grid-bg rounded-3xl border border-dashed border-white/12 bg-slate-950/30 p-10 text-center light:border-slate-200 light:bg-white/60">
      <div className="mx-auto grid h-12 w-12 place-items-center rounded-2xl border border-cyan-300/20 bg-cyan-300/10 text-cyan-200 light:bg-cyan-50 light:text-cyan-700">
        <Icon className="h-6 w-6" />
      </div>
      <h3 className="mt-4 text-base font-semibold text-white light:text-slate-950">{title}</h3>
      {description ? <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-slate-400 light:text-slate-600">{description}</p> : null}
      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  )
}
