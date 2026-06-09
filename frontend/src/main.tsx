import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { I18nProvider } from './providers/I18nProvider'
import { QueryProvider } from './providers/QueryProvider'
import { ThemeProvider } from './providers/ThemeProvider'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <I18nProvider>
      <ThemeProvider>
        <QueryProvider>
          <App />
        </QueryProvider>
      </ThemeProvider>
    </I18nProvider>
  </StrictMode>,
)
