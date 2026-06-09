import { useMutation, useQueryClient } from '@tanstack/react-query'
import { RotateCcw, Wand2 } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import type { Job, PresetName, ProcessingMode } from '../../api/types'
import { reenhanceJob, retryJob } from '../../api/jobs'
import { Button } from '../common/Button'

const presets: PresetName[] = [
  'real_estate_natural',
  'conservative_hdr',
  'window_control',
  'bright_interior',
  'artifact_safe',
]

interface JobActionsProps {
  job: Job
}

export function JobActions({ job }: JobActionsProps) {
  const { t } = useTranslation()
  const [preset, setPreset] = useState<PresetName>('conservative_hdr')
  const [mode, setMode] = useState<ProcessingMode>('quality')
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  const retryMutation = useMutation({
    mutationFn: () => retryJob(job.id, { strategy: 'same_params' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['job', job.id] })
      queryClient.invalidateQueries({ queryKey: ['job-steps', job.id] })
    },
  })

  const reenhanceMutation = useMutation({
    mutationFn: () =>
      reenhanceJob(job.id, {
        image_set_id: job.image_set_id,
        preset_name: preset,
        mode,
        params: { save_debug_outputs: true },
      }),
    onSuccess: (newJob) => navigate(`/jobs/${newJob.id}`),
  })

  return (
    <div className="flex flex-wrap items-center gap-2">
      <Button
        disabled={retryMutation.isPending}
        type="button"
        variant="secondary"
        onClick={() => retryMutation.mutate()}
      >
        <RotateCcw className="h-4 w-4" />
        {t('common.retry')}
      </Button>

      <select
        className="field min-w-52"
        value={preset}
        onChange={(event) => setPreset(event.target.value as PresetName)}
      >
        {presets.map((item) => (
          <option key={item} value={item}>
            {t(`preset.names.${item}`)}
          </option>
        ))}
      </select>
      <select
        className="field min-w-40"
        value={mode}
        onChange={(event) => setMode(event.target.value as ProcessingMode)}
      >
        <option value="fast_preview">{t('mode.fast_preview')}</option>
        <option value="quality">{t('mode.quality')}</option>
        <option value="ultra">{t('mode.ultra')}</option>
      </select>
      <Button
        disabled={reenhanceMutation.isPending}
        type="button"
        variant="primary"
        onClick={() => reenhanceMutation.mutate()}
      >
        <Wand2 className="h-4 w-4" />
        {t('common.reenhance')}
      </Button>
    </div>
  )
}
