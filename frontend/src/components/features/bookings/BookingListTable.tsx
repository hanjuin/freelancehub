import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { format } from 'date-fns'
import { Search, ChevronLeft, ChevronRight } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { bookingsApi } from '@/api/bookings'
import { servicesApi } from '@/api/services'
import type { Booking, BookingStatus, BookingsListParams } from '@/types/booking'
import { BookingStatusBadge } from './BookingStatusBadge'
import { cn } from '@/utils/cn'

const STATUS_OPTIONS: { value: BookingStatus | ''; label: string }[] = [
  { value: '', label: 'All statuses' },
  { value: 'pending', label: 'Pending' },
  { value: 'confirmed', label: 'Confirmed' },
  { value: 'completed', label: 'Completed' },
  { value: 'cancelled', label: 'Cancelled' },
  { value: 'no_show', label: 'No-show' },
]

interface Props {
  onSelect: (booking: Booking) => void
}

export function BookingListTable({ onSelect }: Props) {
  const { t } = useTranslation()
  const [page, setPage] = useState(1)
  const [filters, setFilters] = useState<BookingsListParams>({
    page_size: 20,
    status: '',
    from_date: '',
    to_date: '',
    service_id: '',
    search: '',
  })

  const params: BookingsListParams = {
    ...filters,
    page,
    status: filters.status || undefined,
    from_date: filters.from_date || undefined,
    to_date: filters.to_date || undefined,
    service_id: filters.service_id || undefined,
    search: filters.search || undefined,
  }

  const { data, isLoading, isError } = useQuery({
    queryKey: ['bookings', params],
    queryFn: () => bookingsApi.list(params),
  })

  const { data: servicesData } = useQuery({
    queryKey: ['services'],
    queryFn: () => servicesApi.list(1, 100),
  })

  function setFilter<K extends keyof BookingsListParams>(key: K, value: BookingsListParams[K]) {
    setFilters(prev => ({ ...prev, [key]: value }))
    setPage(1)
  }

  const customerName = (b: Booking) =>
    b.customer
      ? [b.customer.first_name, b.customer.last_name].filter(Boolean).join(' ')
      : '—'

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        {/* Search */}
        <div className="relative flex-1 min-w-48">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)]" />
          <input
            type="text"
            placeholder={t('bookings.searchPlaceholder')}
            value={filters.search ?? ''}
            onChange={e => setFilter('search', e.target.value)}
            className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] pl-9 pr-3 py-2 text-sm text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
          />
        </div>

        {/* Status */}
        <select
          value={filters.status ?? ''}
          onChange={e => setFilter('status', e.target.value as BookingStatus | '')}
          className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
        >
          {STATUS_OPTIONS.map(o => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>

        {/* Service */}
        <select
          value={filters.service_id ?? ''}
          onChange={e => setFilter('service_id', e.target.value)}
          className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
        >
          <option value="">{t('bookings.allServices')}</option>
          {servicesData?.items.map(s => (
            <option key={s.id} value={s.id}>{s.name}</option>
          ))}
        </select>

        {/* Date range */}
        <input
          type="date"
          value={filters.from_date ?? ''}
          onChange={e => setFilter('from_date', e.target.value)}
          className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
        />
        <input
          type="date"
          value={filters.to_date ?? ''}
          onChange={e => setFilter('to_date', e.target.value)}
          className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
        />
      </div>

      {/* Table */}
      <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-sm text-[var(--color-text-muted)]">{t('common.loading')}</div>
        ) : isError ? (
          <div className="p-8 text-center text-sm text-red-500">{t('bookings.loadError')}</div>
        ) : !data || data.items.length === 0 ? (
          <div className="p-8 text-center text-sm text-[var(--color-text-muted)]">{t('bookings.noBookings')}</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--color-border)] bg-[var(--color-surface-raised)]">
                  <th className="px-4 py-3 text-left font-medium text-[var(--color-text-muted)]">{t('bookings.customer')}</th>
                  <th className="px-4 py-3 text-left font-medium text-[var(--color-text-muted)]">{t('bookings.service')}</th>
                  <th className="px-4 py-3 text-left font-medium text-[var(--color-text-muted)]">{t('bookings.dateTime')}</th>
                  <th className="px-4 py-3 text-left font-medium text-[var(--color-text-muted)]">{t('bookings.duration')}</th>
                  <th className="px-4 py-3 text-left font-medium text-[var(--color-text-muted)]">{t('bookings.status')}</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((booking, idx) => (
                  <tr
                    key={booking.id}
                    onClick={() => onSelect(booking)}
                    className={cn(
                      'cursor-pointer transition-colors hover:bg-[var(--color-surface-raised)]',
                      idx < data.items.length - 1 && 'border-b border-[var(--color-border)]',
                    )}
                  >
                    <td className="px-4 py-3 font-medium text-[var(--color-text)]">{customerName(booking)}</td>
                    <td className="px-4 py-3 text-[var(--color-text-muted)]">
                      <div className="flex items-center gap-2">
                        {booking.service?.color && (
                          <span
                            className="inline-block h-2 w-2 rounded-full flex-shrink-0"
                            style={{ background: booking.service.color }}
                          />
                        )}
                        {booking.service?.name ?? '—'}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-[var(--color-text-muted)]">
                      {format(new Date(booking.start_time), 'MMM d, yyyy · h:mm a')}
                    </td>
                    <td className="px-4 py-3 text-[var(--color-text-muted)]">{booking.duration_minutes} min</td>
                    <td className="px-4 py-3"><BookingStatusBadge status={booking.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Pagination */}
      {data && data.pages > 1 && (
        <div className="flex items-center justify-between text-sm text-[var(--color-text-muted)]">
          <span>{t('bookings.pageOf', { page: data.page, pages: data.pages, total: data.total })}</span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="flex h-8 w-8 items-center justify-center rounded-lg border border-[var(--color-border)] disabled:opacity-40 hover:bg-[var(--color-surface-raised)]"
            >
              <ChevronLeft size={16} />
            </button>
            <button
              onClick={() => setPage(p => Math.min(data.pages, p + 1))}
              disabled={page >= data.pages}
              className="flex h-8 w-8 items-center justify-center rounded-lg border border-[var(--color-border)] disabled:opacity-40 hover:bg-[var(--color-surface-raised)]"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
