import { RotateCcw, Trash2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { UploadFileItem } from '../../hooks/useUploadRawFiles'
import { formatBytes, fileExtension } from '../../utils/file'
import { Button } from '../common/Button'
import { StatusBadge } from '../common/StatusBadge'
import { UploadProgress } from './UploadProgress'

interface UploadFileListProps {
  items: UploadFileItem[]
  onRemove: (id: string) => void
  onRetry?: (item: UploadFileItem) => void
  disabled?: boolean
}

export function UploadFileList({ items, onRemove, onRetry, disabled }: UploadFileListProps) {
  const { t } = useTranslation()
  if (items.length === 0) return null

  return (
    <div className="overflow-hidden rounded-3xl border border-white/10 bg-slate-950/35 light:border-slate-200 light:bg-white/80">
      <div className="grid grid-cols-[1fr_120px_120px_160px_52px] gap-3 border-b border-white/10 px-4 py-3 text-xs font-semibold uppercase tracking-[0.16em] text-slate-500 light:border-slate-200">
        <span>{t('upload.file')}</span>
        <span>{t('upload.size')}</span>
        <span>{t('common.status')}</span>
        <span>{t('common.progress')}</span>
        <span />
      </div>
      <div className="divide-y divide-white/7 light:divide-slate-100">
        {items.map((item) => (
          <div key={item.id} className="grid items-center gap-3 px-4 py-4 md:grid-cols-[1fr_120px_120px_160px_52px]">
            <div className="min-w-0">
              <div className="truncate text-sm font-semibold text-white light:text-slate-950">{item.file.name}</div>
              <div className="mt-1 text-xs uppercase text-slate-500">{fileExtension(item.file.name)}</div>
              {item.error ? <div className="mt-1 text-xs text-red-300 light:text-red-700">{item.error}</div> : null}
            </div>
            <div className="text-sm text-slate-400 light:text-slate-600">{formatBytes(item.file.size)}</div>
            <StatusBadge status={item.status} />
            <UploadProgress value={item.progress} />
            <div className="flex justify-end gap-1">
              {item.status === 'failed' && onRetry ? (
                <Button aria-label={t('upload.retryUpload')} disabled={disabled} size="icon" type="button" variant="ghost" onClick={() => onRetry(item)}>
                  <RotateCcw className="h-4 w-4" />
                </Button>
              ) : null}
              <Button aria-label={t('upload.remove')} disabled={disabled || item.status === 'uploading'} size="icon" type="button" variant="ghost" onClick={() => onRemove(item.id)}>
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
