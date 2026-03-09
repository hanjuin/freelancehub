import { useTranslation } from 'react-i18next'

export default function DashboardPage() {
  const { t } = useTranslation()

  const cards = [
    { labelKey: 'dashboard.todaysBookings',      value: '—' },
    { labelKey: 'dashboard.pendingConfirmations', value: '—' },
    { labelKey: 'dashboard.revenueThisMonth',     value: '—' },
    { labelKey: 'dashboard.outstandingInvoices',  value: '—' },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-[var(--color-text)]">{t('dashboard.welcomeBack')}</h2>
        <p className="text-sm text-[var(--color-text-muted)] mt-1">{t('dashboard.happeningToday')}</p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {cards.map(card => (
          <div
            key={card.labelKey}
            className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5"
          >
            <p className="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wide">{t(card.labelKey)}</p>
            <p className="mt-2 text-3xl font-bold text-[var(--color-text)]">{card.value}</p>
          </div>
        ))}
      </div>

      {/* Placeholder content area */}
      <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 text-center text-[var(--color-text-muted)]">
        {t('dashboard.calendarPlaceholder')}
      </div>
    </div>
  )
}
