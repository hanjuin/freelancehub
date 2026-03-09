import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  format,
  startOfWeek,
  endOfWeek,
  startOfMonth,
  endOfMonth,
  startOfDay,
  endOfDay,
  addDays,
  addWeeks,
  addMonths,
  subWeeks,
  subMonths,
  isSameDay,
  parseISO,
  eachDayOfInterval,
} from 'date-fns'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { bookingsApi } from '@/api/bookings'
import type { Booking } from '@/types/booking'
import { BookingStatusBadge } from './BookingStatusBadge'

type CalendarView = 'day' | 'week' | 'month'

interface Props {
  onSelect: (booking: Booking) => void
}

const HOURS = Array.from({ length: 14 }, (_, i) => i + 7) // 7am–8pm

export function BookingCalendar({ onSelect }: Props) {
  const { t } = useTranslation()
  const [view, setView] = useState<CalendarView>('week')
  const [current, setCurrent] = useState(new Date())

  const { from, to } = getRange(view, current)

  const { data, isLoading } = useQuery({
    queryKey: ['bookings-calendar', view, format(from, 'yyyy-MM-dd'), format(to, 'yyyy-MM-dd')],
    queryFn: () =>
      bookingsApi.list({
        from_date: from.toISOString(),
        to_date: to.toISOString(),
        page_size: 200,
      }),
  })

  const bookings = data?.items ?? []

  function navigate(dir: 1 | -1) {
    if (view === 'day') setCurrent(d => addDays(d, dir))
    else if (view === 'week') setCurrent(d => (dir === 1 ? addWeeks(d, 1) : subWeeks(d, 1)))
    else setCurrent(d => (dir === 1 ? addMonths(d, 1) : subMonths(d, 1)))
  }

  const headerLabel =
    view === 'day'
      ? format(current, 'EEEE, MMMM d, yyyy')
      : view === 'week'
      ? `${format(from, 'MMM d')} – ${format(to, 'MMM d, yyyy')}`
      : format(current, 'MMMM yyyy')

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button
            onClick={() => navigate(-1)}
            className="flex h-8 w-8 items-center justify-center rounded-lg border border-[var(--color-border)] hover:bg-[var(--color-surface-raised)]"
          >
            <ChevronLeft size={16} />
          </button>
          <span className="min-w-48 text-center text-sm font-medium text-[var(--color-text)]">{headerLabel}</span>
          <button
            onClick={() => navigate(1)}
            className="flex h-8 w-8 items-center justify-center rounded-lg border border-[var(--color-border)] hover:bg-[var(--color-surface-raised)]"
          >
            <ChevronRight size={16} />
          </button>
          <button
            onClick={() => setCurrent(new Date())}
            className="ml-2 rounded-lg border border-[var(--color-border)] px-3 py-1.5 text-xs text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)]"
          >
            {t('bookings.today')}
          </button>
        </div>

        {/* View switcher */}
        <div className="flex rounded-lg border border-[var(--color-border)] overflow-hidden">
          {(['day', 'week', 'month'] as CalendarView[]).map(v => (
            <button
              key={v}
              onClick={() => setView(v)}
              className={`px-3 py-1.5 text-xs font-medium transition-colors ${
                view === v
                  ? 'bg-[var(--color-primary)] text-white'
                  : 'text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)]'
              }`}
            >
              {t(`bookings.view.${v}`)}
            </button>
          ))}
        </div>
      </div>

      {/* Calendar body */}
      {isLoading ? (
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-8 text-center text-sm text-[var(--color-text-muted)]">
          {t('common.loading')}
        </div>
      ) : view === 'month' ? (
        <MonthView current={current} bookings={bookings} onSelect={onSelect} />
      ) : (
        <TimeGrid days={getDays(view, current)} bookings={bookings} onSelect={onSelect} hours={HOURS} />
      )}
    </div>
  )
}

// ── Month View ───────────────────────────────────────────────────────────────

function MonthView({
  current,
  bookings,
  onSelect,
}: {
  current: Date
  bookings: Booking[]
  onSelect: (b: Booking) => void
}) {
  const monthStart = startOfMonth(current)
  const monthEnd = endOfMonth(current)
  const gridStart = startOfWeek(monthStart)
  const gridEnd = endOfWeek(monthEnd)
  const days = eachDayOfInterval({ start: gridStart, end: gridEnd })
  const today = new Date()

  return (
    <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden">
      <div className="grid grid-cols-7 border-b border-[var(--color-border)]">
        {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(d => (
          <div key={d} className="py-2 text-center text-xs font-medium text-[var(--color-text-muted)]">{d}</div>
        ))}
      </div>
      <div className="grid grid-cols-7">
        {days.map((day, idx) => {
          const dayBookings = bookings.filter(b => isSameDay(parseISO(b.start_time), day))
          const isCurrentMonth = day.getMonth() === current.getMonth()
          const isToday = isSameDay(day, today)
          return (
            <div
              key={idx}
              className={`min-h-24 border-b border-r border-[var(--color-border)] p-1.5 ${
                !isCurrentMonth ? 'opacity-40' : ''
              }`}
            >
              <p className={`mb-1 flex h-6 w-6 items-center justify-center rounded-full text-xs font-medium ${
                isToday
                  ? 'bg-[var(--color-primary)] text-white'
                  : 'text-[var(--color-text-muted)]'
              }`}>
                {format(day, 'd')}
              </p>
              <div className="space-y-0.5">
                {dayBookings.slice(0, 3).map(b => (
                  <button
                    key={b.id}
                    onClick={() => onSelect(b)}
                    className="w-full truncate rounded px-1 py-0.5 text-left text-xs text-white"
                    style={{ background: b.service?.color ?? 'var(--color-primary)' }}
                  >
                    {format(parseISO(b.start_time), 'h:mm')} {b.customer?.first_name}
                  </button>
                ))}
                {dayBookings.length > 3 && (
                  <p className="text-xs text-[var(--color-text-muted)] pl-1">+{dayBookings.length - 3} more</p>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ── Time Grid (Day / Week) ───────────────────────────────────────────────────

function TimeGrid({
  days,
  bookings,
  onSelect,
  hours,
}: {
  days: Date[]
  bookings: Booking[]
  onSelect: (b: Booking) => void
  hours: number[]
}) {
  const today = new Date()
  const CELL_HEIGHT = 56 // px per hour

  return (
    <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden">
      {/* Day headers */}
      <div className="flex border-b border-[var(--color-border)]">
        <div className="w-14 shrink-0" />
        {days.map(day => (
          <div key={day.toISOString()} className="flex-1 py-2 text-center">
            <p className="text-xs font-medium text-[var(--color-text-muted)]">{format(day, 'EEE')}</p>
            <p className={`mx-auto mt-0.5 flex h-7 w-7 items-center justify-center rounded-full text-sm font-semibold ${
              isSameDay(day, today)
                ? 'bg-[var(--color-primary)] text-white'
                : 'text-[var(--color-text)]'
            }`}>
              {format(day, 'd')}
            </p>
          </div>
        ))}
      </div>

      {/* Scrollable grid */}
      <div className="overflow-y-auto max-h-[600px]">
        <div className="relative flex">
          {/* Hour labels */}
          <div className="w-14 shrink-0">
            {hours.map(h => (
              <div key={h} style={{ height: CELL_HEIGHT }} className="flex items-start justify-end pr-2 pt-1">
                <span className="text-xs text-[var(--color-text-muted)]">{format(new Date(2000, 0, 1, h), 'h a')}</span>
              </div>
            ))}
          </div>

          {/* Day columns */}
          {days.map(day => {
            const dayBookings = bookings.filter(b => isSameDay(parseISO(b.start_time), day))
            return (
              <div key={day.toISOString()} className="relative flex-1 border-l border-[var(--color-border)]">
                {hours.map(h => (
                  <div
                    key={h}
                    style={{ height: CELL_HEIGHT }}
                    className="border-b border-[var(--color-border)] border-dashed"
                  />
                ))}
                {/* Booking blocks */}
                {dayBookings.map(b => {
                  const start = parseISO(b.start_time)
                  const end = parseISO(b.end_time)
                  const startHour = start.getHours() + start.getMinutes() / 60
                  const endHour = end.getHours() + end.getMinutes() / 60
                  const gridStart = hours[0]
                  const top = (startHour - gridStart) * CELL_HEIGHT
                  const height = Math.max((endHour - startHour) * CELL_HEIGHT, 20)
                  return (
                    <button
                      key={b.id}
                      onClick={() => onSelect(b)}
                      style={{
                        top,
                        height,
                        background: b.service?.color ?? 'var(--color-primary)',
                      }}
                      className="absolute left-0.5 right-0.5 overflow-hidden rounded p-1 text-left text-xs text-white opacity-90 hover:opacity-100 transition-opacity"
                    >
                      <p className="font-medium truncate">{b.customer?.first_name} {b.customer?.last_name}</p>
                      {height > 30 && <p className="truncate opacity-80">{b.service?.name}</p>}
                    </button>
                  )
                })}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function getRange(view: CalendarView, date: Date): { from: Date; to: Date } {
  if (view === 'day') return { from: startOfDay(date), to: endOfDay(date) }
  if (view === 'week') return { from: startOfWeek(date), to: endOfWeek(date) }
  return { from: startOfMonth(date), to: endOfMonth(date) }
}

function getDays(view: CalendarView, date: Date): Date[] {
  if (view === 'day') return [date]
  const start = startOfWeek(date)
  return Array.from({ length: 7 }, (_, i) => addDays(start, i))
}
