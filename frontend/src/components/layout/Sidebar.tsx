import { NavLink } from 'react-router-dom'
import { X } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { NAV_ITEMS } from '@/constants/navigation'
import { ThemeToggle } from '@/components/ui/ThemeToggle'
import { LanguageSwitcher } from '@/components/ui/LanguageSwitcher'
import { cn } from '@/utils/cn'

interface Props {
  open: boolean
  onClose: () => void
}

export function Sidebar({ open, onClose }: Props) {
  const { t } = useTranslation()

  return (
    <>
      {/* Mobile backdrop */}
      {open && (
        <div
          className="fixed inset-0 z-20 bg-black/40 backdrop-blur-sm lg:hidden"
          onClick={onClose}
          aria-hidden
        />
      )}

      {/* Sidebar panel */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-30 flex w-64 flex-col',
          'bg-[var(--color-surface)] border-r border-[var(--color-border)]',
          'transition-transform duration-300 ease-in-out',
          // mobile: slide in/out; desktop: always visible
          open ? 'translate-x-0' : '-translate-x-full',
          'lg:translate-x-0 lg:static lg:z-auto',
        )}
      >
        {/* Brand */}
        <div className="flex h-16 items-center justify-between px-5 border-b border-[var(--color-border)]">
          <span className="text-lg font-bold text-[var(--color-primary)]">
            FreelanceHub
          </span>
          {/* Close button — mobile only */}
          <button
            onClick={onClose}
            aria-label="Close menu"
            className="lg:hidden flex h-8 w-8 items-center justify-center rounded-lg text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)]"
          >
            <X size={18} />
          </button>
        </div>

        {/* Nav links */}
        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
          {NAV_ITEMS.map(({ labelKey, path, icon: Icon }) => (
            <NavLink
              key={path}
              to={path}
              onClick={onClose}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-[var(--color-primary-light)] text-[var(--color-primary)]'
                    : 'text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)]',
                )
              }
            >
              <Icon size={18} />
              {t(labelKey)}
            </NavLink>
          ))}
        </nav>

        {/* Bottom: theme + language */}
        <div className="flex items-center justify-between px-5 py-4 border-t border-[var(--color-border)]">
          <div className="flex items-center gap-2">
            <span className="text-xs text-[var(--color-text-subtle)]">{t('common.appearance')}</span>
            <ThemeToggle />
          </div>
          <LanguageSwitcher />
        </div>
      </aside>
    </>
  )
}
