import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { ThemeContext, type Theme, type ThemeContextValue } from './theme-context'

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(() => {
    const stored = localStorage.getItem('hdr-theme')
    return stored === 'light' || stored === 'dark' ? stored : 'dark'
  })

  useEffect(() => {
    const root = document.documentElement
    root.classList.toggle('dark', theme === 'dark')
    root.classList.toggle('light', theme === 'light')
    localStorage.setItem('hdr-theme', theme)
  }, [theme])

  const value = useMemo<ThemeContextValue>(
    () => ({
      theme,
      setTheme: setThemeState,
      toggleTheme: () => setThemeState((current) => (current === 'dark' ? 'light' : 'dark')),
    }),
    [theme],
  )

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}
