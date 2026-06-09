import { Languages } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { Button } from '../common/Button'

export function LanguageSwitcher() {
  const { i18n, t } = useTranslation()
  const nextLanguage = i18n.language.startsWith('vi') ? 'en' : 'vi'

  async function toggleLanguage() {
    await i18n.changeLanguage(nextLanguage)
    localStorage.setItem('hdr-language', nextLanguage)
  }

  return (
    <Button aria-label={t('common.switchLanguage')} size="md" type="button" variant="secondary" onClick={toggleLanguage}>
      <Languages className="h-4 w-4" />
      <span className="text-xs font-bold uppercase">{i18n.language.startsWith('vi') ? 'VI' : 'EN'}</span>
    </Button>
  )
}
