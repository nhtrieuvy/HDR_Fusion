import { Menu, Plus, Radio, UserCircle } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { Link, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { getData } from '../../api/client'
import { LanguageSwitcher } from './LanguageSwitcher'
import { ThemeToggle } from './ThemeToggle'

function pageKey(pathname: string) {
  if (pathname.startsWith('/upload') || pathname.startsWith('/jobs/new')) return 'upload'
  if (pathname.startsWith('/processing')) return 'processing'
  if (pathname.startsWith('/preview')) return 'preview'
  if (pathname.startsWith('/export')) return 'export'
  if (pathname.startsWith('/history')) return 'history'
  if (pathname.startsWith('/settings')) return 'settings'
  if (pathname.startsWith('/projects')) return 'projects'
  if (pathname.startsWith('/artifacts')) return 'artifacts'
  return 'dashboard'
}

export function Header({ onMenu }: { onMenu?: () => void }) {
  const { t } = useTranslation()
  const location = useLocation()
  const healthQuery = useQuery({
    queryKey: ['backend-health'],
    queryFn: () => getData<{ status: string }>('/health'),
    refetchInterval: 10000,
    retry: 0,
  })
  const online = healthQuery.data?.status === 'ok'

  return (
    <header className="sticky top-0 z-30 border-b border-white/10 bg-slate-950/70 backdrop-blur-2xl light:border-slate-200 light:bg-white/76">
      <div className="flex min-h-20 items-center justify-between gap-4 px-4 md:px-6">
        <div className="flex min-w-0 items-center gap-3">
          <button
            aria-label={t('common.openNavigation')}
            className="focus-ring rounded-xl border border-white/10 p-2 text-slate-300 xl:hidden"
            type="button"
            onClick={onMenu}
          >
            <Menu className="h-5 w-5" />
          </button>
          <div>
            <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.20em] text-cyan-300 light:text-cyan-700">
              <Radio className="h-3.5 w-3.5" />
              {t('app.pipeline')}
            </p>
            <h2 className="mt-1 text-sm text-slate-400 light:text-slate-600">
              {t(`nav.${pageKey(location.pathname)}`)} / <span className="font-semibold text-white light:text-slate-950">/v1</span> / {t('app.upload')}
            </h2>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="hidden items-center gap-2 rounded-full border border-white/10 bg-white/7 px-3 py-2 text-xs font-semibold text-slate-200 light:border-slate-200 light:bg-white light:text-slate-700 sm:inline-flex">
            <span className={online ? 'h-2 w-2 rounded-full bg-emerald-400' : 'h-2 w-2 rounded-full bg-red-400'} />
            {online ? t('common.online') : t('common.offline')}
          </span>
          <div className="hidden gap-2 md:flex">
            <ThemeToggle />
            <LanguageSwitcher />
          </div>
          <span className="hidden min-h-10 items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/8 px-4 text-sm font-semibold text-slate-100 light:border-slate-200 light:bg-white light:text-slate-900 sm:inline-flex">
            <UserCircle className="h-4 w-4" />
            {t('common.user')}
          </span>
          <Link
            className="focus-ring hidden min-h-10 items-center justify-center gap-2 rounded-xl border border-cyan-400/40 bg-cyan-400 px-4 text-sm font-semibold text-slate-950 shadow-[0_12px_32px_rgba(34,211,238,0.22)] transition hover:bg-cyan-300 md:inline-flex"
            to="/upload"
          >
            <Plus className="h-4 w-4" />
            {t('common.newJob')}
          </Link>
        </div>
      </div>
    </header>
  )
}
