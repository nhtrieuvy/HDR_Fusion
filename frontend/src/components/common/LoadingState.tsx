import { Loader2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'

interface LoadingStateProps {
  label?: string
}

export function LoadingState({ label }: LoadingStateProps) {
  const { t } = useTranslation()
  return (
    <div className="flex items-center justify-center gap-3 rounded-3xl border border-white/10 bg-white/5 p-8 text-sm text-slate-300 light:border-slate-200 light:bg-white light:text-slate-600">
      <Loader2 className="h-4 w-4 animate-spin text-cyan-300" />
      {label ?? t('common.loading')}
    </div>
  )
}
