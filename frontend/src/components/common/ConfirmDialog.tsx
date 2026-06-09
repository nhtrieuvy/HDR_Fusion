import { useTranslation } from 'react-i18next'
import { Button } from './Button'

interface ConfirmDialogProps {
  open: boolean
  title: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
  onConfirm: () => void
  onCancel: () => void
}

export function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel,
  cancelLabel,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  const { t } = useTranslation()
  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/60 p-4 backdrop-blur-sm">
      <div className="surface-card w-full max-w-md rounded-3xl p-5">
        <h2 className="text-base font-semibold text-white light:text-slate-950">{title}</h2>
        <p className="mt-2 text-sm text-slate-400 light:text-slate-600">{message}</p>
        <div className="mt-5 flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={onCancel}>
            {cancelLabel ?? t('common.cancel')}
          </Button>
          <Button type="button" variant="danger" onClick={onConfirm}>
            {confirmLabel ?? t('common.confirm')}
          </Button>
        </div>
      </div>
    </div>
  )
}
