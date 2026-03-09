import type { LucideIcon } from 'lucide-react'
import {
  LayoutDashboard,
  CalendarDays,
  Users,
  FileText,
  Settings,
} from 'lucide-react'

export interface NavItem {
  labelKey: string
  path: string
  icon: LucideIcon
}

export const NAV_ITEMS: NavItem[] = [
  { labelKey: 'nav.dashboard', path: '/dashboard', icon: LayoutDashboard },
  { labelKey: 'nav.bookings',  path: '/bookings',  icon: CalendarDays },
  { labelKey: 'nav.customers', path: '/customers', icon: Users },
  { labelKey: 'nav.invoices',  path: '/invoices',  icon: FileText },
  { labelKey: 'nav.settings',  path: '/settings',  icon: Settings },
]
