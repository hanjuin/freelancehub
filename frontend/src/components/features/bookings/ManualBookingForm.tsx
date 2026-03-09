import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { X, Search } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { bookingsApi } from '@/api/bookings'
import { servicesApi } from '@/api/services'
import { customersApi } from '@/api/customers'
import type { CustomerSummary } from '@/api/customers'

interface Props {
  onClose: () => void
}

export function ManualBookingForm({ onClose }: Props) {
  const { t } = useTranslation()
  const queryClient = useQueryClient()

  const [customerSearch, setCustomerSearch] = useState('')
  const [selectedCustomer, setSelectedCustomer] = useState<CustomerSummary | null>(null)
  const [serviceId, setServiceId] = useState('')
  const [startTime, setStartTime] = useState('')
  const [notes, setNotes] = useState('')
  const [error, setError] = useState('')

  const { data: servicesData } = useQuery({
    queryKey: ['services'],
    queryFn: () => servicesApi.list(1, 100),
  })

  const { data: customersData } = useQuery({
    queryKey: ['customer-search', customerSearch],
    queryFn: () => customersApi.list(customerSearch || undefined),
    enabled: customerSearch.length >= 1 || !selectedCustomer,
  })

  const createMutation = useMutation({
    mutationFn: () =>
      bookingsApi.create({
        customer_id: selectedCustomer!.id,
        service_id: serviceId,
        start_time: new Date(startTime).toISOString(),
        customer_notes: notes || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bookings'] })
      queryClient.invalidateQueries({ queryKey: ['bookings-calendar'] })
      onClose()
    },
    onError: (err: Error) => setError(err.message),
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    if (!selectedCustomer) { setError(t('bookings.form.errorNoCustomer')); return }
    if (!serviceId) { setError(t('bookings.form.errorNoService')); return }
    if (!startTime) { setError(t('bookings.form.errorNoTime')); return }
    createMutation.mutate()
  }

  const customerName = (c: CustomerSummary) =>
    [c.first_name, c.last_name].filter(Boolean).join(' ')

  const showDropdown = !selectedCustomer && customersData && customersData.items.length > 0

  return (
    <>
      <div className="fixed inset-0 z-40 bg-black/40" onClick={onClose} />
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className="w-full max-w-md rounded-2xl bg-[var(--color-surface)] shadow-2xl">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-[var(--color-border)] px-6 py-4">
            <h2 className="text-lg font-semibold text-[var(--color-text)]">
              {t('bookings.form.title')}
            </h2>
            <button
              onClick={onClose}
              className="flex h-8 w-8 items-center justify-center rounded-lg text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)]"
            >
              <X size={18} />
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5 px-6 py-5">
            {/* Customer picker */}
            <div>
              <label className="mb-1.5 block text-sm font-medium text-[var(--color-text)]">
                {t('bookings.customer')} <span className="text-red-500">*</span>
              </label>
              {selectedCustomer ? (
                <div className="flex items-center justify-between rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-2">
                  <div>
                    <p className="text-sm font-medium text-[var(--color-text)]">{customerName(selectedCustomer)}</p>
                    {selectedCustomer.email && (
                      <p className="text-xs text-[var(--color-text-muted)]">{selectedCustomer.email}</p>
                    )}
                  </div>
                  <button
                    type="button"
                    onClick={() => { setSelectedCustomer(null); setCustomerSearch('') }}
                    className="text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text)]"
                  >
                    {t('common.edit')}
                  </button>
                </div>
              ) : (
                <div className="relative">
                  <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)]" />
                  <input
                    type="text"
                    placeholder={t('bookings.form.searchCustomer')}
                    value={customerSearch}
                    onChange={e => setCustomerSearch(e.target.value)}
                    className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] pl-9 pr-3 py-2 text-sm text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
                  />
                  {showDropdown && (
                    <div className="absolute top-full left-0 right-0 z-10 mt-1 max-h-48 overflow-y-auto rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] shadow-lg">
                      {customersData.items.map(c => (
                        <button
                          key={c.id}
                          type="button"
                          onClick={() => { setSelectedCustomer(c); setCustomerSearch('') }}
                          className="w-full px-4 py-2.5 text-left hover:bg-[var(--color-surface-raised)]"
                        >
                          <p className="text-sm font-medium text-[var(--color-text)]">{customerName(c)}</p>
                          {c.email && <p className="text-xs text-[var(--color-text-muted)]">{c.email}</p>}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Service */}
            <div>
              <label className="mb-1.5 block text-sm font-medium text-[var(--color-text)]">
                {t('bookings.service')} <span className="text-red-500">*</span>
              </label>
              <select
                value={serviceId}
                onChange={e => setServiceId(e.target.value)}
                required
                className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
              >
                <option value="">{t('bookings.form.selectService')}</option>
                {servicesData?.items
                  .filter(s => s.is_active)
                  .map(s => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({s.duration_minutes} min)
                    </option>
                  ))}
              </select>
            </div>

            {/* Date & Time */}
            <div>
              <label className="mb-1.5 block text-sm font-medium text-[var(--color-text)]">
                {t('bookings.dateTime')} <span className="text-red-500">*</span>
              </label>
              <input
                type="datetime-local"
                value={startTime}
                onChange={e => setStartTime(e.target.value)}
                required
                className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
              />
            </div>

            {/* Notes */}
            <div>
              <label className="mb-1.5 block text-sm font-medium text-[var(--color-text)]">
                {t('bookings.form.notes')}
              </label>
              <textarea
                rows={3}
                value={notes}
                onChange={e => setNotes(e.target.value)}
                placeholder={t('bookings.form.notesPlaceholder')}
                className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
              />
            </div>

            {error && (
              <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600 dark:bg-red-950/20 dark:text-red-400">
                {error}
              </p>
            )}

            {/* Actions */}
            <div className="flex gap-3 pt-1">
              <button
                type="submit"
                disabled={createMutation.isPending}
                className="flex-1 rounded-lg bg-[var(--color-primary)] py-2.5 text-sm font-medium text-white hover:opacity-90 disabled:opacity-60"
              >
                {createMutation.isPending ? t('bookings.form.creating') : t('bookings.form.createBooking')}
              </button>
              <button
                type="button"
                onClick={onClose}
                className="rounded-lg border border-[var(--color-border)] px-4 py-2.5 text-sm text-[var(--color-text)] hover:bg-[var(--color-surface-raised)]"
              >
                {t('common.cancel')}
              </button>
            </div>
          </form>
        </div>
      </div>
    </>
  )
}
