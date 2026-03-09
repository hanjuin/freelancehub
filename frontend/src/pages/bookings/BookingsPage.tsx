import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Calendar, List, Plus } from 'lucide-react'
import { BookingCalendar } from '@/components/features/bookings/BookingCalendar'
import { BookingListTable } from '@/components/features/bookings/BookingListTable'
import { BookingDetailDrawer } from '@/components/features/bookings/BookingDetailDrawer'
import { ManualBookingForm } from '@/components/features/bookings/ManualBookingForm'
import type { Booking } from '@/types/booking'
import { cn } from '@/utils/cn'

type Tab = 'calendar' | 'list'

export default function BookingsPage() {
  const { t } = useTranslation()
  const [tab, setTab] = useState<Tab>('calendar')
  const [selectedBooking, setSelectedBooking] = useState<Booking | null>(null)
  const [showForm, setShowForm] = useState(false)

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-[var(--color-text)]">{t('bookings.title')}</h2>
          <p className="mt-1 text-sm text-[var(--color-text-muted)]">{t('bookings.subtitle')}</p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-2 rounded-lg bg-[var(--color-primary)] px-4 py-2.5 text-sm font-medium text-white hover:opacity-90"
        >
          <Plus size={16} />
          {t('bookings.newBooking')}
        </button>
      </div>

      {/* Tab switcher */}
      <div className="flex rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-1 w-fit gap-1">
        <TabButton active={tab === 'calendar'} onClick={() => setTab('calendar')} icon={<Calendar size={15} />}>
          {t('bookings.calendarView')}
        </TabButton>
        <TabButton active={tab === 'list'} onClick={() => setTab('list')} icon={<List size={15} />}>
          {t('bookings.listView')}
        </TabButton>
      </div>

      {/* Content */}
      {tab === 'calendar' ? (
        <BookingCalendar onSelect={setSelectedBooking} />
      ) : (
        <BookingListTable onSelect={setSelectedBooking} />
      )}

      {/* Detail drawer */}
      <BookingDetailDrawer
        booking={selectedBooking}
        onClose={() => setSelectedBooking(null)}
      />

      {/* Manual booking form */}
      {showForm && <ManualBookingForm onClose={() => setShowForm(false)} />}
    </div>
  )
}

function TabButton({
  active,
  onClick,
  icon,
  children,
}: {
  active: boolean
  onClick: () => void
  icon: React.ReactNode
  children: React.ReactNode
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-colors',
        active
          ? 'bg-[var(--color-primary)] text-white shadow-sm'
          : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]',
      )}
    >
      {icon}
      {children}
    </button>
  )
}
