import { useState, useRef, useEffect } from 'react'
import { Menu, LogOut } from 'lucide-react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { NAV_ITEMS } from '@/constants/navigation'
import { ThemeToggle } from '@/components/ui/ThemeToggle'
import { LanguageSwitcher } from '@/components/ui/LanguageSwitcher'
import { useAuth } from '@/context/AuthContext'

interface Props {
  onMenuClick: () => void
}

export function Topbar({ onMenuClick }: Props) {
  const { pathname } = useLocation()
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const { t } = useTranslation()
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  const current = NAV_ITEMS.find(n => pathname.startsWith(n.path))

  const initials = user
    ? `${user.first_name[0]}${user.last_name[0]}`.toUpperCase()
    : '?'

  useEffect(() => {
    function handler(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleLogout = async () => {
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <header className="flex h-16 items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-4 lg:px-6">
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuClick}
          aria-label="Open menu"
          className="flex h-9 w-9 items-center justify-center rounded-lg text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] lg:hidden"
        >
          <Menu size={20} />
        </button>
        <h1 className="text-base font-semibold text-[var(--color-text)]">
          {current ? t(current.labelKey) : 'FreelanceHub'}
        </h1>
      </div>

      <div className="flex items-center gap-2">
        <LanguageSwitcher className="hidden lg:flex" />
        <ThemeToggle className="hidden lg:flex" />

        <div ref={menuRef} className="relative">
          <button
            onClick={() => setMenuOpen(o => !o)}
            aria-label="User menu"
            className="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--color-primary)] text-xs font-bold text-white select-none hover:opacity-90 transition"
          >
            {initials}
          </button>

          {menuOpen && (
            <div className="absolute right-0 top-10 z-50 w-52 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-lg py-1">
              <div className="px-4 py-2.5 border-b border-[var(--color-border)]">
                <p className="text-sm font-medium text-[var(--color-text)] truncate">
                  {user ? `${user.first_name} ${user.last_name}` : ''}
                </p>
                <p className="text-xs text-[var(--color-text-muted)] truncate">{user?.email}</p>
              </div>
              <button
                onClick={handleLogout}
                className="flex w-full items-center gap-2.5 px-4 py-2.5 text-sm text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-danger)] transition-colors"
              >
                <LogOut size={15} />
                {t('auth.signOut')}
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
