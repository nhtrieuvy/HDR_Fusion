import { Download, Maximize2, ZoomIn, ZoomOut, BarChart3 } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { Button } from '../common/Button'

interface ImageToolbarProps {
  histogramEnabled: boolean
  onDownload?: () => void
  onFit: () => void
  onToggleHistogram: () => void
  onZoomIn: () => void
  onZoomOut: () => void
}

export function ImageToolbar({
  histogramEnabled,
  onDownload,
  onFit,
  onToggleHistogram,
  onZoomIn,
  onZoomOut,
}: ImageToolbarProps) {
  const { t } = useTranslation()
  return (
    <div className="flex flex-wrap items-center gap-2">
      <Button aria-label={t('preview.zoomIn')} size="icon" type="button" variant="secondary" onClick={onZoomIn}>
        <ZoomIn className="h-4 w-4" />
      </Button>
      <Button aria-label={t('preview.zoomOut')} size="icon" type="button" variant="secondary" onClick={onZoomOut}>
        <ZoomOut className="h-4 w-4" />
      </Button>
      <Button aria-label={t('preview.fit')} size="icon" type="button" variant="secondary" onClick={onFit}>
        <Maximize2 className="h-4 w-4" />
      </Button>
      <Button type="button" variant={histogramEnabled ? 'soft' : 'secondary'} onClick={onToggleHistogram}>
        <BarChart3 className="h-4 w-4" />
        {t('preview.histogram')}
      </Button>
      <Button disabled={!onDownload} type="button" variant="primary" onClick={onDownload}>
        <Download className="h-4 w-4" />
        {t('common.download')}
      </Button>
    </div>
  )
}
