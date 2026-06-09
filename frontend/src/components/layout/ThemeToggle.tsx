import { Moon, Sun } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useTheme } from '../../providers/theme-context'
import { Button } from '../common/Button'

export function ThemeToggle() {
  const { t } = useTranslation()
  const { theme, toggleTheme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <Button
      aria-label={t('common.toggleTheme')}
      size="icon"
      type="button"
      variant="secondary"
      onClick={toggleTheme}
    >
      {isDark ? <Moon className="h-4 w-4 text-cyan-200" /> : <Sun className="h-4 w-4 text-amber-500" />}
    </Button>
  )
}
