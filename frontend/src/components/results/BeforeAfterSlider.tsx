import { useState } from 'react'
import { useTranslation } from 'react-i18next'

interface BeforeAfterSliderProps {
  beforeUrl?: string
  afterUrl?: string
}

export function BeforeAfterSlider({ beforeUrl, afterUrl }: BeforeAfterSliderProps) {
  const { t } = useTranslation()
  const [value, setValue] = useState(50)

  if (!afterUrl) return null
  if (!beforeUrl) {
    return (
      <div className="rounded-3xl border border-white/10 bg-slate-950/50 p-3 light:border-slate-200 light:bg-white">
        <img className="max-h-[70vh] w-full rounded-md object-contain" src={afterUrl} alt={t('results.finalOutputAlt')} />
      </div>
    )
  }

  return (
    <div className="rounded-3xl border border-white/10 bg-slate-950/50 p-3 light:border-slate-200 light:bg-white">
      <div className="relative overflow-hidden rounded-2xl bg-slate-900 light:bg-slate-100">
        <img className="w-full object-contain" src={afterUrl} alt={t('preview.afterAlt')} />
        <div className="absolute inset-0 overflow-hidden" style={{ width: `${value}%` }}>
          <img className="h-full w-full object-cover" src={beforeUrl} alt={t('preview.beforeAlt')} />
        </div>
        <div className="absolute inset-y-0 w-0.5 bg-white shadow" style={{ left: `${value}%` }} />
      </div>
      <input
        className="mt-3 w-full accent-cyan-300"
        max={100}
        min={0}
        type="range"
        value={value}
        onChange={(event) => setValue(Number(event.target.value))}
      />
    </div>
  )
}
