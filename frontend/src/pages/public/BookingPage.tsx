import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useTranslation } from 'react-i18next'
import { ChevronLeft, ChevronRight, Check, Calendar, Clock, User } from 'lucide-react'
import { LanguageSwitcher } from '@/components/ui/LanguageSwitcher'
import { publicApi } from '@/api/public'
import type { PublicProfile } from '@/api/public'
import type { Service } from '@/types/service'
import type { AvailableSlot } from '@/types/availability'

// ── Helpers ──────────────────────────────────────────────────────────────────

function formatPrice(cents: number, currency = 'AUD'): string {
  return new Intl.NumberFormat('en-AU', { style: 'currency', currency }).format(cents / 100)
}
function formatDuration(mins: number): string {
  if (mins < 60) return `${mins} min`
  const h = Math.floor(mins / 60)
  const m = mins % 60
  return m > 0 ? `${h}h ${m}m` : `${h}h`
}
function formatTime(iso: string, tz?: string): string {
  return new Date(iso).toLocaleTimeString('en-AU', { hour: '2-digit', minute: '2-digit', hour12: true, timeZone: tz })
}
function formatDateFull(d: Date, tz?: string): string {
  return d.toLocaleDateString('en-AU', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric', timeZone: tz })
}
function toDateStr(d: Date): string {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

const inputCls = 'w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2.5 text-sm text-gray-900 dark:text-gray-100 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition'
const labelCls = 'mb-1.5 block text-sm font-medium text-gray-700 dark:text-gray-300'

// ── Step indicator ────────────────────────────────────────────────────────────

type Step = 0 | 1 | 2 | 3

function StepBar({ step }: { step: Step }) {
  const { t } = useTranslation()
  const STEPS = [
    t('booking.steps.service'),
    t('booking.steps.dateTime'),
    t('booking.steps.yourDetails'),
    t('booking.steps.confirmed'),
  ]

  return (
    <div className="flex items-center justify-center gap-0 mb-8">
      {STEPS.map((label, i) => (
        <div key={label} className="flex items-center">
          <div className="flex flex-col items-center">
            <div className={[
              'flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold transition-colors',
              i < step ? 'bg-indigo-600 text-white' :
              i === step ? 'bg-indigo-600 text-white ring-4 ring-indigo-100' :
              'bg-gray-100 dark:bg-gray-700 text-gray-400',
            ].join(' ')}>
              {i < step ? <Check size={14} /> : i + 1}
            </div>
            <span className={[
              'mt-1 hidden sm:block text-xs',
              i === step ? 'text-indigo-600 font-medium' : 'text-gray-400',
            ].join(' ')}>{label}</span>
          </div>
          {i < STEPS.length - 1 && (
            <div className={[
              'mx-2 h-0.5 w-12 sm:w-16 rounded',
              i < step ? 'bg-indigo-600' : 'bg-gray-200 dark:bg-gray-700',
            ].join(' ')} />
          )}
        </div>
      ))}
    </div>
  )
}

// ── Step 1: Service selection ─────────────────────────────────────────────────

function ServiceStep({
  services,
  currency,
  onSelect,
}: {
  services: Service[]
  currency: string
  onSelect: (s: Service) => void
}) {
  const { t } = useTranslation()

  return (
    <div className="space-y-3">
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">{t('booking.chooseService')}</h2>
      {services.length === 0 ? (
        <p className="text-sm text-gray-500">{t('booking.noServices')}</p>
      ) : (
        services.map(s => (
          <button
            key={s.id}
            onClick={() => onSelect(s)}
            className="w-full flex items-center justify-between rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-4 text-left hover:border-indigo-400 hover:shadow-sm transition group"
          >
            <div className="flex items-center gap-3">
              {s.color && (
                <span className="h-3 w-3 rounded-full flex-shrink-0" style={{ background: s.color }} />
              )}
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white group-hover:text-indigo-600 transition-colors">
                  {s.name}
                </p>
                {s.description && (
                  <p className="mt-0.5 text-xs text-gray-500 line-clamp-1">{s.description}</p>
                )}
              </div>
            </div>
            <div className="text-right flex-shrink-0 ml-4">
              <p className="text-sm font-semibold text-gray-900 dark:text-white">
                {formatPrice(s.price_cents, currency)}
              </p>
              <p className="text-xs text-gray-500">{formatDuration(s.duration_minutes)}</p>
            </div>
          </button>
        ))
      )}
    </div>
  )
}

// ── Step 2: Date & Time ───────────────────────────────────────────────────────

function DateTimeStep({
  username,
  service,
  freelancerTz,
  onSelect,
  onBack,
}: {
  username: string
  service: Service
  freelancerTz: string
  onSelect: (slot: AvailableSlot) => void
  onBack: () => void
}) {
  const { t } = useTranslation()
  const today = new Date()
  today.setHours(0, 0, 0, 0)

  const [viewDate, setViewDate] = useState(() => {
    const d = new Date()
    d.setDate(1)
    return d
  })
  const [selectedDate, setSelectedDate] = useState<Date | null>(null)
  const [slots, setSlots] = useState<AvailableSlot[]>([])
  const [loadingSlots, setLoadingSlots] = useState(false)

  const prevMonth = () => setViewDate(d => new Date(d.getFullYear(), d.getMonth() - 1, 1))
  const nextMonth = () => setViewDate(d => new Date(d.getFullYear(), d.getMonth() + 1, 1))

  // Build calendar grid
  const year = viewDate.getFullYear()
  const month = viewDate.getMonth()
  const firstDay = new Date(year, month, 1).getDay() // 0=Sun
  const daysInMonth = new Date(year, month + 1, 0).getDate()
  const cells: (Date | null)[] = Array(firstDay).fill(null)
  for (let d = 1; d <= daysInMonth; d++) {
    cells.push(new Date(year, month, d))
  }

  useEffect(() => {
    if (!selectedDate) return
    setLoadingSlots(true)
    setSlots([])
    publicApi.getAvailableSlots(username, service.id, toDateStr(selectedDate))
      .then(setSlots)
      .catch(() => setSlots([]))
      .finally(() => setLoadingSlots(false))
  }, [selectedDate, username, service.id])

  return (
    <div className="space-y-5">
      <button onClick={onBack} className="flex items-center gap-1 text-sm text-indigo-600 hover:text-indigo-800">
        <ChevronLeft size={16} /> {t('booking.back')}
      </button>
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white">{t('booking.pickDateTime')}</h2>
      <div className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4">
        <div className="flex items-center justify-between mb-3">
          <button onClick={prevMonth} className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">
            <ChevronLeft size={16} />
          </button>
          <span className="text-sm font-semibold text-gray-800 dark:text-gray-100">
            {viewDate.toLocaleDateString('en-AU', { month: 'long', year: 'numeric' })}
          </span>
          <button onClick={nextMonth} className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">
            <ChevronRight size={16} />
          </button>
        </div>

        <div className="grid grid-cols-7 gap-0.5 mb-1">
          {['Su','Mo','Tu','We','Th','Fr','Sa'].map(d => (
            <div key={d} className="text-center text-xs font-medium text-gray-400 py-1">{d}</div>
          ))}
        </div>

        <div className="grid grid-cols-7 gap-0.5">
          {cells.map((date, i) => {
            if (!date) return <div key={i} />
            const isPast = date < today
            const isSelected = selectedDate?.toDateString() === date.toDateString()
            return (
              <button
                key={i}
                disabled={isPast}
                onClick={() => setSelectedDate(date)}
                className={[
                  'rounded-lg py-2 text-sm transition-colors',
                  isPast ? 'text-gray-300 dark:text-gray-600 cursor-not-allowed' :
                  isSelected ? 'bg-indigo-600 text-white font-semibold' :
                  'text-gray-700 dark:text-gray-300 hover:bg-indigo-50 dark:hover:bg-indigo-900/30',
                ].join(' ')}
              >
                {date.getDate()}
              </button>
            )
          })}
        </div>
      </div>

      {selectedDate && (
        <div>
          <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-1.5">
            <Clock size={14} className="text-indigo-500" />
            {formatDateFull(selectedDate, freelancerTz)}
          </p>
          {loadingSlots ? (
            <p className="text-sm text-gray-400">{t('booking.loadingSlots')}</p>
          ) : slots.length === 0 ? (
            <p className="text-sm text-gray-400">{t('booking.noSlots')}</p>
          ) : (
            <div className="grid grid-cols-3 sm:grid-cols-4 gap-2">
              {slots.map(slot => (
                <button
                  key={slot.start_time}
                  onClick={() => onSelect(slot)}
                  className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm font-medium text-gray-800 dark:text-gray-200 hover:border-indigo-400 hover:text-indigo-600 transition"
                >
                  {formatTime(slot.start_time, freelancerTz)}
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ── Step 3: Customer details ──────────────────────────────────────────────────

const detailsSchema = z.object({
  first_name:     z.string().min(1, 'Required'),
  last_name:      z.string().min(1, 'Required'),
  email:          z.string().email('Enter a valid email'),
  phone:          z.string().optional(),
  customer_notes: z.string().optional(),
})
type DetailsForm = z.infer<typeof detailsSchema>

function DetailsStep({
  service,
  slot,
  currency,
  freelancerTz,
  onSubmit,
  onBack,
  submitting,
  error,
}: {
  service: Service
  slot: AvailableSlot
  currency: string
  freelancerTz: string
  onSubmit: (values: DetailsForm) => void
  onBack: () => void
  submitting: boolean
  error: string | null
}) {
  const { t } = useTranslation()
  const { register, handleSubmit, formState: { errors } } = useForm<DetailsForm>({
    resolver: zodResolver(detailsSchema),
  })

  return (
    <div className="space-y-5">
      <button onClick={onBack} className="flex items-center gap-1 text-sm text-indigo-600 hover:text-indigo-800">
        <ChevronLeft size={16} /> {t('booking.back')}
      </button>
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white">{t('booking.yourDetails')}</h2>

      {/* Booking summary */}
      <div className="rounded-xl border border-indigo-100 dark:border-indigo-900 bg-indigo-50 dark:bg-indigo-950/30 p-4 space-y-1">
        <div className="flex items-center gap-2 text-sm text-indigo-800 dark:text-indigo-200">
          <Calendar size={14} /> {formatDateFull(new Date(slot.start_time), freelancerTz)}
        </div>
        <div className="flex items-center gap-2 text-sm text-indigo-800 dark:text-indigo-200">
          <Clock size={14} /> {formatTime(slot.start_time, freelancerTz)} · {formatDuration(service.duration_minutes)}
        </div>
        <div className="flex items-center gap-2 text-sm text-indigo-800 dark:text-indigo-200">
          <User size={14} /> {service.name} · {formatPrice(service.price_cents, currency)}
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-950/30 dark:text-red-400">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className={labelCls}>{t('booking.firstName')}</label>
            <input {...register('first_name')} className={inputCls} autoComplete="given-name" />
            {errors.first_name && <p className="mt-1 text-xs text-red-500">{errors.first_name.message}</p>}
          </div>
          <div>
            <label className={labelCls}>{t('booking.lastName')}</label>
            <input {...register('last_name')} className={inputCls} autoComplete="family-name" />
            {errors.last_name && <p className="mt-1 text-xs text-red-500">{errors.last_name.message}</p>}
          </div>
        </div>
        <div>
          <label className={labelCls}>{t('booking.email')}</label>
          <input {...register('email')} type="email" className={inputCls} autoComplete="email" />
          {errors.email && <p className="mt-1 text-xs text-red-500">{errors.email.message}</p>}
        </div>
        <div>
          <label className={labelCls}>{t('booking.phone')}</label>
          <input {...register('phone')} type="tel" className={inputCls} autoComplete="tel" />
        </div>
        <div>
          <label className={labelCls}>{t('booking.notes')}</label>
          <textarea {...register('customer_notes')} rows={2} className={inputCls + ' resize-none'} placeholder={t('booking.notesPlaceholder')} />
        </div>
        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-lg bg-indigo-600 py-3 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-60 disabled:cursor-not-allowed transition"
        >
          {submitting ? t('booking.bookingInProgress') : t('booking.confirmBooking')}
        </button>
      </form>
    </div>
  )
}

// ── Step 4: Confirmation ──────────────────────────────────────────────────────

function ConfirmedStep({
  service,
  slot,
  currency,
  freelancerTz,
}: {
  service: Service
  slot: AvailableSlot
  currency: string
  freelancerTz: string
}) {
  const { t } = useTranslation()

  return (
    <div className="text-center space-y-5 py-4">
      <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-green-100 dark:bg-green-900/30">
        <Check size={28} className="text-green-600" />
      </div>
      <div>
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">{t('booking.bookingConfirmed')}</h2>
        <p className="mt-1 text-sm text-gray-500">{t('booking.confirmationEmail')}</p>
      </div>
      <div className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5 text-left space-y-2 max-w-xs mx-auto">
        <div className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
          <User size={14} className="text-indigo-500" /> {service.name}
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
          <Calendar size={14} className="text-indigo-500" /> {formatDateFull(new Date(slot.start_time), freelancerTz)}
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
          <Clock size={14} className="text-indigo-500" /> {formatTime(slot.start_time, freelancerTz)} · {formatDuration(service.duration_minutes)}
        </div>
        <p className="pt-1 text-sm font-semibold text-gray-900 dark:text-white">
          {formatPrice(service.price_cents, currency)}
        </p>
      </div>
    </div>
  )
}

// ── Main Page ────────────────────────────────────────────────────────────────

type DetailsFormValues = {
  first_name: string
  last_name: string
  email: string
  phone?: string
  customer_notes?: string
}

export default function BookingPage() {
  const { username } = useParams<{ username: string }>()
  const { t } = useTranslation()

  const [profile, setProfile] = useState<PublicProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)

  const [step, setStep] = useState<Step>(0)
  const [service, setService] = useState<Service | null>(null)
  const [slot, setSlot] = useState<AvailableSlot | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [bookingError, setBookingError] = useState<string | null>(null)

  useEffect(() => {
    if (!username) return
    publicApi.getProfile(username)
      .then(setProfile)
      .catch(() => setNotFound(true))
      .finally(() => setLoading(false))
  }, [username])

  const handleSelectService = (s: Service) => {
    setService(s)
    setStep(1)
  }

  const handleSelectSlot = (s: AvailableSlot) => {
    setSlot(s)
    setStep(2)
  }

  const handleSubmitDetails = async (values: DetailsFormValues) => {
    if (!username || !service || !slot) return
    setSubmitting(true)
    setBookingError(null)
    try {
      await publicApi.createBooking(username, {
        service_id:     service.id,
        start_time:     slot.start_time,
        first_name:     values.first_name,
        last_name:      values.last_name,
        email:          values.email,
        phone:          values.phone || null,
        customer_notes: values.customer_notes || null,
      })
      setStep(3)
    } catch (e) {
      setBookingError(e instanceof Error ? e.message : t('booking.bookingFailed'))
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-dvh flex items-center justify-center bg-gray-50 dark:bg-gray-950">
        <p className="text-sm text-gray-400">{t('common.loading')}</p>
      </div>
    )
  }

  if (notFound || !profile) {
    return (
      <div className="min-h-dvh flex items-center justify-center bg-gray-50 dark:bg-gray-950">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{t('booking.notFound')}</h1>
          <p className="mt-2 text-sm text-gray-500">{t('booking.notFoundDesc')}</p>
        </div>
      </div>
    )
  }

  const displayName = profile.business_name ?? `${profile.first_name} ${profile.last_name}`

  return (
    <div className="min-h-dvh bg-gray-50 dark:bg-gray-950 py-8 px-4">
      <div className="mx-auto max-w-lg">
        {/* Language switcher */}
        <div className="flex justify-end mb-4">
          <LanguageSwitcher className="border-gray-200 dark:border-gray-700 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800" />
        </div>

        {/* Header */}
        <div className="mb-8 text-center">
          {profile.avatar_url ? (
            <img
              src={profile.avatar_url}
              alt={displayName}
              className="mx-auto mb-3 h-16 w-16 rounded-full object-cover"
            />
          ) : (
            <div className="mx-auto mb-3 flex h-16 w-16 items-center justify-center rounded-full bg-indigo-600 text-2xl font-bold text-white">
              {profile.first_name[0]}{profile.last_name[0]}
            </div>
          )}
          <h1 className="text-xl font-bold text-gray-900 dark:text-white">{displayName}</h1>
          {profile.bio && <p className="mt-1 text-sm text-gray-500 max-w-xs mx-auto">{profile.bio}</p>}
        </div>

        {/* Steps */}
        <StepBar step={step} />

        {/* Card */}
        <div className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-6 shadow-sm">
          {step === 0 && (
            <ServiceStep
              services={profile.services}
              currency={profile.currency}
              onSelect={handleSelectService}
            />
          )}
          {step === 1 && service && (
            <DateTimeStep
              username={profile.username}
              service={service}
              freelancerTz={profile.timezone}
              onSelect={handleSelectSlot}
              onBack={() => setStep(0)}
            />
          )}
          {step === 2 && service && slot && (
            <DetailsStep
              service={service}
              slot={slot}
              currency={profile.currency}
              freelancerTz={profile.timezone}
              onSubmit={handleSubmitDetails}
              onBack={() => setStep(1)}
              submitting={submitting}
              error={bookingError}
            />
          )}
          {step === 3 && service && slot && (
            <ConfirmedStep
              service={service}
              slot={slot}
              currency={profile.currency}
              freelancerTz={profile.timezone}
            />
          )}
        </div>

        <p className="mt-6 text-center text-xs text-gray-400">
          {t('booking.poweredBy')}
        </p>
      </div>
    </div>
  )
}
