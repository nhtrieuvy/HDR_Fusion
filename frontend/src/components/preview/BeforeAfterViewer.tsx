import 'img-comparison-slider'
import { createElement } from 'react'
import { Image } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { EmptyState } from '../common/EmptyState'

interface BeforeAfterViewerProps {
  beforeUrl?: string
  afterUrl?: string
  zoom?: number
}

export function BeforeAfterViewer({ beforeUrl, afterUrl, zoom = 1 }: BeforeAfterViewerProps) {
  const { t } = useTranslation()

  if (!afterUrl) {
    return <EmptyState icon={Image} title={t('preview.emptyTitle')} description={t('preview.emptyDesc')} />
  }

  if (!beforeUrl) {
    return (
      <div className="overflow-auto rounded-3xl border border-white/10 bg-slate-950/60 light:border-slate-200 light:bg-white">
        <img
          alt={t('preview.hdrResultAlt')}
          className="max-h-[680px] w-full origin-center object-contain transition-transform"
          src={afterUrl}
          style={{ transform: `scale(${zoom})` }}
        />
      </div>
    )
  }

  return (
    <div className="overflow-auto rounded-3xl border border-white/10 bg-slate-950/60 light:border-slate-200 light:bg-white">
      <div className="origin-center transition-transform" style={{ transform: `scale(${zoom})` }}>
      {createElement(
        'img-comparison-slider',
        { class: 'block w-full' },
        <img alt={t('preview.beforeAlt')} key="before" slot="first" src={beforeUrl} />,
        <img alt={t('preview.afterAlt')} key="after" slot="second" src={afterUrl} />,
      )}
      </div>
    </div>
  )
}
