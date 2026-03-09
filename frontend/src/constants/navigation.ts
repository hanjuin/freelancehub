import type { LucideIcon } from 'lucide-react'
import {
  LayoutDashboard,
  CalendarDays,
  Users,
  FileText,
  Settings,
} from 'lucide-react'

export interface NavItem {
  label: string
  path: string
  icon: LucideIcon
}

export const NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard',  path: '/dashboard',  icon: LayoutDashboard },
  { label: 'Bookings',   path: '/bookings',   icon: CalendarDays },
  { label: 'Customers',  path: '/customers',  icon: Users },
  { label: 'Invoices',   path: '/invoices',   icon: FileText },
  { label: 'Settings',   path: '/settings',   icon: Settings },
]
