import type { ReactNode } from 'react'

interface PageHeaderProps {
  eyebrow?: string
  title: string
  description?: string
  actions?: ReactNode
}

export function PageHeader({ eyebrow, title, description, actions }: PageHeaderProps) {
  return (
    <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
      <div className="max-w-3xl">
        {eyebrow ? <p className="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-300 light:text-cyan-700">{eyebrow}</p> : null}
        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-white light:text-slate-950 md:text-4xl">{title}</h1>
        {description ? <p className="mt-3 text-sm leading-6 text-slate-400 light:text-slate-600">{description}</p> : null}
      </div>
      {actions ? <div className="flex flex-wrap items-center gap-3">{actions}</div> : null}
    </div>
  )
}
