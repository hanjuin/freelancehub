import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { format } from 'date-fns'
import { X, Clock, User, Briefcase, FileText, DollarSign } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { bookingsApi } from '@/api/bookings'
import type { Booking, BookingStatus } from '@/types/booking'
import { BookingStatusBadge } from './BookingStatusBadge'

interface Props {
  booking: Booking | null
  onClose: () => void
}

const ACTION_TRANSITIONS: Partial<Record<BookingStatus, { label: string; next: BookingStatus; variant: 'primary' | 'danger' | 'secondary' }[]>> = {
  pending: [
    { label: 'Confirm', next: 'confirmed', variant: 'primary' },
    { label: 'Cancel', next: 'cancelled', variant: 'danger' },
  ],
  confirmed: [
    { label: 'Mark Completed', next: 'completed', variant: 'primary' },
    { label: 'Mark No-show', next: 'no_show', variant: 'secondary' },
    { label: 'Cancel', next: 'cancelled', variant: 'danger' },
  ],
}

const VARIANT_CLASSES = {
  primary: 'bg-[var(--color-primary)] text-white hover:opacity-90',
  danger: 'bg-red-600 text-white hover:bg-red-700',
  secondary: 'border border-[var(--color-border)] text-[var(--color-text)] hover:bg-[var(--color-surface-raised)]',
}

export function BookingDetailDrawer({ booking, onClose }: Props) {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [notes, setNotes] = useState(booking?.internal_notes ?? '')
  const [editingNotes, setEditingNotes] = useState(false)

  const statusMutation = useMutation({
    mutationFn: (status: BookingStatus) =>
      bookingsApi.updateStatus(booking!.id, { status }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['bookings'] }),
  })

  const notesMutation = useMutation({
    mutationFn: () => bookingsApi.updateNotes(booking!.id, { internal_notes: notes }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bookings'] })
      setEditingNotes(false)
    },
  })

  if (!booking) return null

  const customerName = booking.customer
    ? [booking.customer.first_name, booking.customer.last_name].filter(Boolean).join(' ')
    : '—'

  const actions = ACTION_TRANSITIONS[booking.status] ?? []

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-black/40"
        onClick={onClose}
      />

      {/* Drawer */}
      <div className="fixed right-0 top-0 z-50 h-full w-full max-w-md overflow-y-auto bg-[var(--color-surface)] shadow-xl flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[var(--color-border)] px-6 py-4">
          <div>
            <h2 className="text-lg font-semibold text-[var(--color-text)]">{t('bookings.bookingDetail')}</h2>
            <BookingStatusBadge status={booking.status} className="mt-1" />
          </div>
          <button
            onClick={onClose}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)]"
          >
            <X size={18} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 space-y-5 px-6 py-5">
          {/* Customer */}
          <InfoRow icon={<User size={16} />} label={t('bookings.customer')}>
            <p className="font-medium text-[var(--color-text)]">{customerName}</p>
            {booking.customer?.email && (
              <p className="text-sm text-[var(--color-text-muted)]">{booking.customer.email}</p>
            )}
            {booking.customer?.phone && (
              <p className="text-sm text-[var(--color-text-muted)]">{booking.customer.phone}</p>
            )}
          </InfoRow>

          {/* Service */}
          <InfoRow icon={<Briefcase size={16} />} label={t('bookings.service')}>
            <div className="flex items-center gap-2">
              {booking.service?.color && (
                <span
                  className="h-3 w-3 rounded-full flex-shrink-0"
                  style={{ background: booking.service.color }}
                />
              )}
              <p className="font-medium text-[var(--color-text)]">{booking.service?.name ?? '—'}</p>
            </div>
            <p className="text-sm text-[var(--color-text-muted)]">
              {formatCents(booking.price_cents)}
            </p>
          </InfoRow>

          {/* Time */}
          <InfoRow icon={<Clock size={16} />} label={t('bookings.dateTime')}>
            <p className="font-medium text-[var(--color-text)]">
              {format(new Date(booking.start_time), 'EEEE, MMMM d, yyyy')}
            </p>
            <p className="text-sm text-[var(--color-text-muted)]">
              {format(new Date(booking.start_time), 'h:mm a')} – {format(new Date(booking.end_time), 'h:mm a')} ({booking.duration_minutes} min)
            </p>
          </InfoRow>

          {/* Price */}
          <InfoRow icon={<DollarSign size={16} />} label={t('bookings.price')}>
            <p className="font-medium text-[var(--color-text)]">{formatCents(booking.price_cents)}</p>
          </InfoRow>

          {/* Customer notes */}
          {booking.customer_notes && (
            <InfoRow icon={<FileText size={16} />} label={t('bookings.customerNotes')}>
              <p className="text-sm text-[var(--color-text)]">{booking.customer_notes}</p>
            </InfoRow>
          )}

          {/* Internal notes */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <p className="text-xs font-medium uppercase tracking-wide text-[var(--color-text-muted)]">
                {t('bookings.internalNotes')}
              </p>
              {!editingNotes && (
                <button
                  onClick={() => { setNotes(booking.internal_notes ?? ''); setEditingNotes(true) }}
                  className="text-xs text-[var(--color-primary)] hover:underline"
                >
                  {t('common.edit')}
                </button>
              )}
            </div>
            {editingNotes ? (
              <div className="space-y-2">
                <textarea
                  rows={4}
                  value={notes}
                  onChange={e => setNotes(e.target.value)}
                  className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-2 text-sm text-[var(--color-text)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
                />
                <div className="flex gap-2">
                  <button
                    onClick={() => notesMutation.mutate()}
                    disabled={notesMutation.isPending}
                    className="rounded-lg bg-[var(--color-primary)] px-3 py-1.5 text-xs font-medium text-white hover:opacity-90 disabled:opacity-60"
                  >
                    {notesMutation.isPending ? t('common.saving') : t('common.save')}
                  </button>
                  <button
                    onClick={() => setEditingNotes(false)}
                    className="rounded-lg border border-[var(--color-border)] px-3 py-1.5 text-xs font-medium text-[var(--color-text)] hover:bg-[var(--color-surface-raised)]"
                  >
                    {t('common.cancel')}
                  </button>
                </div>
              </div>
            ) : (
              <p className="text-sm text-[var(--color-text-muted)]">
                {booking.internal_notes || <span className="italic">{t('bookings.noNotes')}</span>}
              </p>
            )}
          </div>

          {/* Cancellation info */}
          {booking.cancellation_reason && (
            <div className="rounded-lg bg-red-50 p-3 dark:bg-red-950/20">
              <p className="text-xs font-medium text-red-700 dark:text-red-400">{t('bookings.cancellationReason')}</p>
              <p className="mt-1 text-sm text-red-600 dark:text-red-300">{booking.cancellation_reason}</p>
            </div>
          )}
        </div>

        {/* Actions */}
        {actions.length > 0 && (
          <div className="border-t border-[var(--color-border)] px-6 py-4 space-y-2">
            {statusMutation.isError && (
              <p className="text-xs text-red-500">{t('bookings.actionFailed')}</p>
            )}
            <div className="flex flex-wrap gap-2">
              {actions.map(action => (
                <button
                  key={action.next}
                  onClick={() => statusMutation.mutate(action.next)}
                  disabled={statusMutation.isPending}
                  className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors disabled:opacity-60 ${VARIANT_CLASSES[action.variant]}`}
                >
                  {action.label}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </>
  )
}

function InfoRow({ icon, label, children }: { icon: React.ReactNode; label: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="flex items-center gap-1.5 mb-1">
        <span className="text-[var(--color-text-muted)]">{icon}</span>
        <p className="text-xs font-medium uppercase tracking-wide text-[var(--color-text-muted)]">{label}</p>
      </div>
      <div className="pl-5">{children}</div>
    </div>
  )
}

function formatCents(cents: number): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(cents / 100)
}
