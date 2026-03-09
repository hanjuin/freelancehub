import { useTranslation } from 'react-i18next'
import { cn } from '@/utils/cn'

interface Props {
  className?: string
}

export function LanguageSwitcher({ className }: Props) {
  const { i18n } = useTranslation()
  const isZh = i18n.language.startsWith('zh')

  const toggle = () => {
    i18n.changeLanguage(isZh ? 'en' : 'zh')
  }

  return (
    <button
      onClick={toggle}
      title={isZh ? 'Switch to English' : '切换到中文'}
      className={cn(
        'rounded-lg border border-[var(--color-border)] px-2 py-1 text-xs font-medium',
        'text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] transition',
        className,
      )}
    >
      {isZh ? 'EN' : '中文'}
    </button>
  )
}
