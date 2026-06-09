import {
  Activity,
  Clock3,
  Download,
  Gauge,
  Image,
  ImageUp,
  Layers3,
  PanelLeftClose,
  Settings,
  Sparkles,
} from 'lucide-react'
import { NavLink } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { cn } from '../../utils/cn'
import { LanguageSwitcher } from './LanguageSwitcher'
import { ThemeToggle } from './ThemeToggle'

const navItems = [
  { to: '/', key: 'dashboard', icon: Gauge },
  { to: '/upload', key: 'upload', icon: ImageUp },
  { to: '/processing', key: 'processing', icon: Activity },
  { to: '/preview', key: 'preview', icon: Image },
  { to: '/export', key: 'export', icon: Download },
  { to: '/history', key: 'history', icon: Clock3 },
  { to: '/settings', key: 'settings', icon: Settings },
]

export function Sidebar({ open = true, onClose }: { open?: boolean; onClose?: () => void }) {
  const { t } = useTranslation()

  return (
    <aside
      className={cn(
        'fixed inset-y-0 left-0 z-40 w-[286px] border-r border-white/10 bg-slate-950/88 backdrop-blur-2xl transition-transform duration-300 light:border-slate-200 light:bg-white/92 xl:sticky xl:translate-x-0',
        open ? 'translate-x-0' : '-translate-x-full',
      )}
    >
      <div className="flex h-full flex-col p-5">
        <div className="flex items-center justify-between gap-3">
          <NavLink className="flex min-w-0 items-center gap-3" to="/">
            <div className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-gradient-to-br from-cyan-300 via-blue-400 to-violet-500 text-sm font-black text-slate-950 shadow-[0_16px_38px_rgba(34,211,238,0.24)]">
              HDR
            </div>
            <div className="min-w-0">
              <div className="truncate text-sm font-semibold text-white light:text-slate-950">{t('app.name')}</div>
              <div className="truncate text-xs text-slate-400 light:text-slate-500">{t('app.subtitle')}</div>
            </div>
          </NavLink>
          <button
            aria-label={t('common.closeNavigation')}
            className="focus-ring rounded-xl p-2 text-slate-400 hover:bg-white/8 xl:hidden"
            type="button"
            onClick={onClose}
          >
            <PanelLeftClose className="h-5 w-5" />
          </button>
        </div>

        <div className="mt-8 rounded-3xl border border-cyan-300/16 bg-cyan-300/8 p-4 light:bg-cyan-50">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-cyan-200 light:text-cyan-700">
            <Sparkles className="h-4 w-4" />
            {t('app.labTitle')}
          </div>
          <p className="mt-2 text-xs leading-5 text-slate-400 light:text-slate-600">
            {t('app.labCopy')}
          </p>
        </div>

        <nav className="mt-6 space-y-1.5">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              className={({ isActive }) =>
                cn(
                  'focus-ring group flex items-center gap-3 rounded-2xl px-3 py-3 text-sm font-medium transition',
                  isActive
                    ? 'bg-white/12 text-white shadow-inner shadow-white/5 light:bg-slate-950 light:text-white'
                    : 'text-slate-400 hover:bg-white/7 hover:text-slate-100 light:text-slate-600 light:hover:bg-slate-100 light:hover:text-slate-950',
                )
              }
              to={item.to}
              onClick={onClose}
            >
              <item.icon className="h-4 w-4" />
              {t(`nav.${item.key}`)}
            </NavLink>
          ))}
        </nav>

        <div className="mt-auto space-y-3">
          <div className="grid grid-cols-2 gap-2">
            <ThemeToggle />
            <LanguageSwitcher />
          </div>
          <div className="rounded-2xl border border-white/10 p-3 light:border-slate-200">
            <div className="flex items-center gap-2 text-xs text-slate-400 light:text-slate-600">
              <Layers3 className="h-4 w-4 text-cyan-300" />
              raw_hdr_fusion
            </div>
          </div>
        </div>
      </div>
    </aside>
  )
}
