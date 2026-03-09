export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-[var(--color-text)]">Welcome back</h2>
        <p className="text-sm text-[var(--color-text-muted)] mt-1">Here's what's happening today.</p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {[
          { label: "Today's Bookings", value: '—' },
          { label: 'Pending Confirmations', value: '—' },
          { label: 'Revenue This Month', value: '—' },
          { label: 'Outstanding Invoices', value: '—' },
        ].map(card => (
          <div
            key={card.label}
            className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5"
          >
            <p className="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wide">{card.label}</p>
            <p className="mt-2 text-3xl font-bold text-[var(--color-text)]">{card.value}</p>
          </div>
        ))}
      </div>

      {/* Placeholder content area */}
      <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 text-center text-[var(--color-text-muted)]">
        Calendar and recent activity will appear here.
      </div>
    </div>
  )
}
