import { AlertTriangle } from 'lucide-react'
import { useTranslation } from 'react-i18next'

interface ErrorStateProps {
  title?: string
  message: string
}

export function ErrorState({ title, message }: ErrorStateProps) {
  const { t } = useTranslation()
  return (
    <div className="rounded-2xl border border-red-400/25 bg-red-500/10 p-4 text-sm text-red-100 light:border-red-200 light:bg-red-50 light:text-red-800">
      <div className="flex items-center gap-2 font-semibold">
        <AlertTriangle className="h-4 w-4" />
        {title ?? t('common.somethingFailed')}
      </div>
      <p className="mt-2 leading-6 text-red-200 light:text-red-700">{t(message, { defaultValue: message })}</p>
    </div>
  )
}
