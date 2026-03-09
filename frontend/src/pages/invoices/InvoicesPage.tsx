import { useTranslation } from 'react-i18next'

export default function InvoicesPage() {
  const { t } = useTranslation()
  return (
    <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 text-center text-[var(--color-text-muted)]">
      {t('invoices.placeholder')}
    </div>
  )
}
