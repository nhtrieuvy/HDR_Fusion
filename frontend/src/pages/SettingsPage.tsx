import { useTranslation } from 'react-i18next'
import { PageHeader } from '../components/common/PageHeader'
import { ProcessingSettingsPanel } from '../components/settings/ProcessingSettingsPanel'

export function SettingsPage() {
  const { t } = useTranslation()
  return (
    <div className="space-y-6">
      <PageHeader title={t('settings.title')} description={t('settings.description')} />
      <ProcessingSettingsPanel />
    </div>
  )
}
