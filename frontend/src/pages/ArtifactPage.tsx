import { useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { EmptyState } from '../components/common/EmptyState'
import { PageHeader } from '../components/common/PageHeader'
import { useAppStore } from '../store/appStore'

export function ArtifactPage() {
  const { t } = useTranslation()
  const { artifactId } = useParams()
  const jobs = useAppStore((state) => state.recentJobs)

  return (
    <div className="space-y-6">
      <PageHeader
        title={t('artifacts.title')}
        description={t('artifacts.description')}
        eyebrow={t('artifacts.eyebrow')}
      />
      <EmptyState
        title={artifactId ? t('artifacts.openFromJob') : t('artifacts.scoped')}
        description={
          artifactId
            ? t('artifacts.directLookup')
            : jobs.length
              ? t('artifacts.selectJob')
              : t('artifacts.createComplete')
        }
      />
    </div>
  )
}
