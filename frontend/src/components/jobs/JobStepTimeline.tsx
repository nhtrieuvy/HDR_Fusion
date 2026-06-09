import type { JobStep } from '../../api/types'
import { useTranslation } from 'react-i18next'
import { EmptyState } from '../common/EmptyState'
import { JobStepRow } from './JobStepRow'

interface JobStepTimelineProps {
  steps: JobStep[]
}

export function JobStepTimeline({ steps }: JobStepTimelineProps) {
  const { t } = useTranslation()
  if (!steps.length) {
    return <EmptyState title={t('job.noStepsTitle')} description={t('job.noStepsDesc')} />
  }

  return (
    <div className="space-y-2">
      {steps.map((step) => (
        <JobStepRow key={step.id} step={step} />
      ))}
    </div>
  )
}
