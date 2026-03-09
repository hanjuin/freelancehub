import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { ThemeToggle } from '@/components/ui/ThemeToggle'
import { useAuth } from '@/context/AuthContext'
import { cn } from '@/utils/cn'

const schema = z.object({
  email:    z.string().email('Enter a valid email'),
  password: z.string().min(1, 'Password is required'),
})

type FormValues = z.infer<typeof schema>

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [serverError, setServerError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) })

  const onSubmit = async (values: FormValues) => {
    setServerError(null)
    try {
      await login(values.email, values.password)
      navigate('/dashboard', { replace: true })
    } catch (err) {
      setServerError(err instanceof Error ? err.message : 'Login failed')
    }
  }

  const inputClass = (hasError: boolean) =>
    cn(
      'w-full rounded-lg border bg-[var(--color-bg)] px-3 py-2.5 text-sm text-[var(--color-text)]',
      'placeholder:text-[var(--color-text-subtle)] transition',
      'focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/20 focus:border-[var(--color-primary)]',
      hasError ? 'border-red-400 dark:border-red-600' : 'border-[var(--color-border)]',
    )

  return (
    <div className="min-h-dvh flex flex-col bg-[var(--color-bg)]">
      <header className="flex items-center justify-between px-6 py-4">
        <span className="text-lg font-bold text-[var(--color-primary)]">FreelanceHub</span>
        <ThemeToggle />
      </header>

      <div className="flex flex-1 items-center justify-center px-4">
        <div className="w-full max-w-sm rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-8 shadow-sm">
          <h1 className="text-2xl font-bold text-[var(--color-text)]">Sign in</h1>
          <p className="mt-1 text-sm text-[var(--color-text-muted)]">
            {"Don't have an account? "}
            <Link to="/register" className="text-[var(--color-primary)] font-medium hover:underline">
              Sign up
            </Link>
          </p>

          <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-4" noValidate>
            {serverError && (
              <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-950/30 dark:text-red-400">
                {serverError}
              </div>
            )}

            <div>
              <label className="mb-1.5 block text-sm font-medium text-[var(--color-text)]">Email</label>
              <input
                {...register('email')}
                type="email"
                placeholder="you@example.com"
                autoComplete="email"
                className={inputClass(!!errors.email)}
              />
              {errors.email && <p className="mt-1 text-xs text-red-500">{errors.email.message}</p>}
            </div>

            <div>
              <label className="mb-1.5 block text-sm font-medium text-[var(--color-text)]">Password</label>
              <input
                {...register('password')}
                type="password"
                placeholder="••••••••"
                autoComplete="current-password"
                className={inputClass(!!errors.password)}
              />
              {errors.password && <p className="mt-1 text-xs text-red-500">{errors.password.message}</p>}
            </div>

            <div className="flex justify-end">
              <Link to="/forgot-password" className="text-xs text-[var(--color-text-muted)] hover:text-[var(--color-primary)]">
                Forgot password?
              </Link>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full rounded-lg bg-[var(--color-primary)] py-2.5 text-sm font-semibold text-white transition-colors hover:bg-[var(--color-primary-hover)] disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isSubmitting ? 'Signing in…' : 'Sign in'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
