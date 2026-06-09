import { useTranslation } from 'react-i18next'
import { useState } from 'react'
import { Button } from '../common/Button'
import { useAppStore } from '../../store/appStore'

export function ProcessingSettingsPanel() {
  const { t } = useTranslation()
  const [saved, setSaved] = useState(false)
  const settings = useAppStore((state) => state.processingSettings)
  const update = useAppStore((state) => state.updateProcessingSettings)
  const reset = useAppStore((state) => state.resetProcessingSettings)

  return (
    <div className="surface-card rounded-3xl p-5">
      <div className="grid gap-5 lg:grid-cols-3">
        <SliderControl label={t('settings.exposureStrength')} value={settings.exposureStrength} onChange={(value) => update({ exposureStrength: value })} />
        <SliderControl label={t('settings.deglareStrength')} value={settings.deglareStrength} onChange={(value) => update({ deglareStrength: value })} />
        <SliderControl label={t('settings.toneMapping')} value={settings.toneMappingIntensity} onChange={(value) => update({ toneMappingIntensity: value })} />
      </div>

      <div className="mt-6 grid gap-3 md:grid-cols-2">
        <SwitchControl label={t('settings.enableAmaze')} checked={settings.enableAmaze} onChange={(value) => update({ enableAmaze: value })} />
        <SwitchControl label={t('settings.enableSourceTruth')} checked={settings.enableSourceTruth} onChange={(value) => update({ enableSourceTruth: value })} />
        <SwitchControl label={t('settings.enableCompositor')} checked={settings.enableCompositor} onChange={(value) => update({ enableCompositor: value })} />
        <SwitchControl label={t('settings.enableDeglare')} checked={settings.enableDeglare} onChange={(value) => update({ enableDeglare: value })} />
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <label className="block">
          <span className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">{t('settings.outputFormat')}</span>
          <select
            className="focus-ring mt-2 w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-sm text-white light:border-slate-200 light:bg-white light:text-slate-950"
            value={settings.outputFormat}
            onChange={(event) => update({ outputFormat: event.target.value as typeof settings.outputFormat })}
          >
            <option value="jpg">{t('settings.formatJpg')}</option>
            <option value="png">{t('settings.formatPng')}</option>
            <option value="tiff">{t('settings.formatTiff')}</option>
          </select>
        </label>
        <label className="block">
          <span className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">{t('settings.quality')}</span>
          <select
            className="focus-ring mt-2 w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-sm text-white light:border-slate-200 light:bg-white light:text-slate-950"
            value={settings.quality}
            onChange={(event) => update({ quality: event.target.value as typeof settings.quality })}
          >
            <option value="draft">{t('settings.draft')}</option>
            <option value="balanced">{t('settings.balanced')}</option>
            <option value="high">{t('settings.high')}</option>
          </select>
        </label>
      </div>

      <div className="mt-6 flex flex-wrap gap-3">
        <Button type="button" variant="secondary" onClick={reset}>
          {t('common.reset')}
        </Button>
        <Button
          type="button"
          variant="primary"
          onClick={() => {
            localStorage.setItem('hdr-processing-preset', JSON.stringify(settings))
            setSaved(true)
            window.setTimeout(() => setSaved(false), 2200)
          }}
        >
          {t('common.savePreset')}
        </Button>
        {saved ? <span className="inline-flex items-center rounded-full border border-emerald-300/25 bg-emerald-400/10 px-3 py-2 text-sm font-semibold text-emerald-200 light:bg-emerald-50 light:text-emerald-700">{t('settings.saved')}</span> : null}
      </div>
    </div>
  )
}

function SliderControl({ label, value, onChange }: { label: string; value: number; onChange: (value: number) => void }) {
  return (
    <label className="block rounded-2xl border border-white/10 bg-white/[0.03] p-4 light:border-slate-200 light:bg-white/70">
      <span className="flex items-center justify-between gap-3 text-sm font-semibold text-white light:text-slate-950">
        {label}
        <span className="text-cyan-300 light:text-cyan-700">{value}</span>
      </span>
      <input
        className="mt-4 w-full accent-cyan-300"
        max={100}
        min={0}
        type="range"
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
      />
    </label>
  )
}

function SwitchControl({ label, checked, onChange }: { label: string; checked: boolean; onChange: (value: boolean) => void }) {
  return (
    <label className="flex items-center justify-between gap-4 rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-sm font-semibold text-white light:border-slate-200 light:bg-white/70 light:text-slate-950">
      {label}
      <button
        aria-pressed={checked}
        className={`relative h-7 w-12 rounded-full transition ${checked ? 'bg-cyan-400' : 'bg-slate-700 light:bg-slate-300'}`}
        type="button"
        onClick={() => onChange(!checked)}
      >
        <span className={`absolute top-1 h-5 w-5 rounded-full bg-white transition ${checked ? 'left-6' : 'left-1'}`} />
      </button>
    </label>
  )
}
