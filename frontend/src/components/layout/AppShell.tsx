import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Outlet } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { Header } from './Header'
import { Sidebar } from './Sidebar'

export function AppShell() {
  const { t } = useTranslation()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="min-h-screen text-slate-100 light:text-slate-950">
      <div className="flex min-h-screen">
        <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        <AnimatePresence>
          {sidebarOpen ? (
            <motion.button
              aria-label={t('common.closeNavigationOverlay')}
              className="fixed inset-0 z-30 bg-slate-950/70 backdrop-blur-sm xl:hidden"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              type="button"
              onClick={() => setSidebarOpen(false)}
            />
          ) : null}
        </AnimatePresence>
        <div className="flex min-w-0 flex-1 flex-col">
          <Header onMenu={() => setSidebarOpen(true)} />
          <main className="w-full flex-1 px-4 py-6 md:px-6 lg:px-8">
            <motion.div
              className="mx-auto w-full max-w-[1500px]"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.22, ease: 'easeOut' }}
            >
              <Outlet />
            </motion.div>
          </main>
        </div>
      </div>
    </div>
  )
}
