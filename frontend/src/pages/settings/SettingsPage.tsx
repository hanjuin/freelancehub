import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Plus, Trash2, Pencil, X, Check } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { profileApi } from '@/api/profile'
import { servicesApi } from '@/api/services'
import { availabilityApi } from '@/api/availability'
import { useAuth } from '@/context/AuthContext'
import { cn } from '@/utils/cn'
import type { ServiceCategory, Service, ServiceCreate } from '@/types/service'
import type { WorkingHours, WorkingHoursCreate, BlockedDate, DayOfWeek } from '@/types/availability'

// ── Shared ───────────────────────────────────────────────────────────────────

const TABS = ['profile', 'services', 'workingHours', 'blockedDates'] as const
type Tab = typeof TABS[number]

const inputCls = 'w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-sm text-[var(--color-text)] placeholder:text-[var(--color-text-subtle)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/20 focus:border-[var(--color-primary)] transition'
const labelCls = 'mb-1 block text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wide'
const btnPrimary = 'rounded-lg bg-[var(--color-primary)] px-4 py-2 text-sm font-semibold text-white hover:bg-[var(--color-primary-hover)] disabled:opacity-60 disabled:cursor-not-allowed transition'
const btnSecondary = 'rounded-lg border border-[var(--color-border)] px-4 py-2 text-sm font-medium text-[var(--color-text)] hover:bg-[var(--color-surface-raised)] transition'

const DAYS: DayOfWeek[] = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

function formatPrice(cents: number): string {
  return `$${(cents / 100).toFixed(2)}`
}
function formatDuration(mins: number): string {
  if (mins < 60) return `${mins}m`
  const h = Math.floor(mins / 60)
  const m = mins % 60
  return m > 0 ? `${h}h ${m}m` : `${h}h`
}

// ── Profile Tab ──────────────────────────────────────────────────────────────

const profileSchema = z.object({
  first_name:    z.string().min(1, 'Required'),
  last_name:     z.string().min(1, 'Required'),
  business_name: z.string().max(200).nullable().optional(),
  phone:         z.string().max(30).nullable().optional(),
  bio:           z.string().nullable().optional(),
  timezone:      z.string().min(1),
  currency:      z.string().length(3),
  country:       z.string().length(2),
  city:          z.string().max(100).nullable().optional(),
  state:         z.string().max(100).nullable().optional(),
  postcode:      z.string().max(20).nullable().optional(),
  address_line1: z.string().max(255).nullable().optional(),
  address_line2: z.string().max(255).nullable().optional(),
})
type ProfileForm = z.infer<typeof profileSchema>

function ProfileTab() {
  const { t } = useTranslation()
  const { user, refreshUser } = useAuth()
  const [categories, setCategories] = useState<ServiceCategory[]>([])
  const [catId, setCatId] = useState<string>('')
  const [saved, setSaved] = useState(false)
  const [serverErr, setServerErr] = useState<string | null>(null)

  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<ProfileForm>({
    resolver: zodResolver(profileSchema),
  })

  useEffect(() => {
    profileApi.getCategories().then(setCategories).catch(() => {})
  }, [])

  useEffect(() => {
    if (user) {
      reset({
        first_name:    user.first_name,
        last_name:     user.last_name,
        business_name: user.business_name,
        phone:         user.phone,
        bio:           user.bio,
        timezone:      user.timezone,
        currency:      user.currency,
        country:       user.country,
        city:          user.city,
        state:         user.state,
        postcode:      user.postcode,
        address_line1: user.address_line1,
        address_line2: user.address_line2,
      })
      setCatId(user.service_category_id ?? '')
    }
  }, [user, reset])

  const onSubmit = async (values: ProfileForm) => {
    setServerErr(null)
    try {
      await profileApi.updateMe({
        ...values,
        service_category_id: catId || null,
      })
      await refreshUser()
      setSaved(true)
      setTimeout(() => setSaved(false), 2500)
    } catch (e) {
      setServerErr(e instanceof Error ? e.message : t('settings.profile.failedToSave'))
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6 max-w-2xl">
      {serverErr && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-950/30 dark:text-red-400">
          {serverErr}
        </div>
      )}

      <div>
        <h3 className="text-sm font-semibold text-[var(--color-text)] mb-4">{t('settings.profile.personalInfo')}</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className={labelCls}>{t('settings.profile.firstName')}</label>
            <input {...register('first_name')} className={inputCls} />
            {errors.first_name && <p className="mt-1 text-xs text-red-500">{errors.first_name.message}</p>}
          </div>
          <div>
            <label className={labelCls}>{t('settings.profile.lastName')}</label>
            <input {...register('last_name')} className={inputCls} />
            {errors.last_name && <p className="mt-1 text-xs text-red-500">{errors.last_name.message}</p>}
          </div>
          <div>
            <label className={labelCls}>{t('settings.profile.phone')}</label>
            <input {...register('phone')} className={inputCls} placeholder="+61 400 000 000" />
          </div>
          <div>
            <label className={labelCls}>{t('settings.profile.businessName')}</label>
            <input {...register('business_name')} className={inputCls} />
          </div>
        </div>
        <div className="mt-4">
          <label className={labelCls}>{t('settings.profile.bio')}</label>
          <textarea
            {...register('bio')}
            rows={3}
            className={inputCls + ' resize-none'}
            placeholder={t('settings.profile.bioPlaceholder')}
          />
        </div>
      </div>

      <div>
        <h3 className="text-sm font-semibold text-[var(--color-text)] mb-4">{t('settings.profile.businessCategory')}</h3>
        <select value={catId} onChange={e => setCatId(e.target.value)} className={inputCls}>
          <option value="">{t('settings.profile.selectCategory')}</option>
          {categories.map(c => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>
      </div>

      <div>
        <h3 className="text-sm font-semibold text-[var(--color-text)] mb-4">{t('settings.profile.locationLocale')}</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="sm:col-span-2">
            <label className={labelCls}>{t('settings.profile.addressLine1')}</label>
            <input {...register('address_line1')} className={inputCls} />
          </div>
          <div className="sm:col-span-2">
            <label className={labelCls}>{t('settings.profile.addressLine2')}</label>
            <input {...register('address_line2')} className={inputCls} />
          </div>
          <div>
            <label className={labelCls}>{t('settings.profile.city')}</label>
            <input {...register('city')} className={inputCls} />
          </div>
          <div>
            <label className={labelCls}>{t('settings.profile.stateProvince')}</label>
            <input {...register('state')} className={inputCls} />
          </div>
          <div>
            <label className={labelCls}>{t('settings.profile.postcode')}</label>
            <input {...register('postcode')} className={inputCls} />
          </div>
          <div>
            <label className={labelCls}>{t('settings.profile.country')}</label>
            <input {...register('country')} className={inputCls} maxLength={2} placeholder="AU" />
            {errors.country && <p className="mt-1 text-xs text-red-500">{errors.country.message}</p>}
          </div>
          <div>
            <label className={labelCls}>{t('settings.profile.timezone')}</label>
            <input {...register('timezone')} className={inputCls} placeholder="Australia/Sydney" />
          </div>
          <div>
            <label className={labelCls}>{t('settings.profile.currency')}</label>
            <input {...register('currency')} className={inputCls} maxLength={3} placeholder="AUD" />
          </div>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <button type="submit" disabled={isSubmitting} className={btnPrimary}>
          {isSubmitting ? t('common.saving') : t('settings.profile.saveChanges')}
        </button>
        {saved && (
          <span className="flex items-center gap-1 text-sm text-green-600">
            <Check size={14} /> {t('common.saved')}
          </span>
        )}
      </div>
    </form>
  )
}

// ── Services Tab ─────────────────────────────────────────────────────────────

const serviceSchema = z.object({
  name:               z.string().min(1, 'Required').max(200),
  description:        z.string().optional(),
  duration_minutes:   z.coerce.number().int().min(1, 'Min 1 min'),
  buffer_minutes:     z.coerce.number().int().min(0).default(0),
  price_cents:        z.coerce.number().int().min(0),
  is_active:          z.boolean().default(true),
  is_bookable_online: z.boolean().default(true),
  color:              z.string().regex(/^#[0-9A-Fa-f]{6}$/).or(z.literal('')).optional(),
})
type ServiceForm = z.infer<typeof serviceSchema>

function ServiceModal({
  service,
  onClose,
  onSaved,
}: {
  service: Service | null
  onClose: () => void
  onSaved: () => void
}) {
  const { t } = useTranslation()
  const [serverErr, setServerErr] = useState<string | null>(null)
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<ServiceForm>({
    resolver: zodResolver(serviceSchema),
    defaultValues: service
      ? {
          name:               service.name,
          description:        service.description ?? '',
          duration_minutes:   service.duration_minutes,
          buffer_minutes:     service.buffer_minutes,
          price_cents:        service.price_cents,
          is_active:          service.is_active,
          is_bookable_online: service.is_bookable_online,
          color:              service.color ?? '',
        }
      : { is_active: true, is_bookable_online: true, buffer_minutes: 0 },
  })

  const onSubmit = async (values: ServiceForm) => {
    setServerErr(null)
    const payload: ServiceCreate = {
      ...values,
      color: values.color || null,
    }
    try {
      if (service) {
        await servicesApi.update(service.id, payload)
      } else {
        await servicesApi.create(payload)
      }
      onSaved()
    } catch (e) {
      setServerErr(e instanceof Error ? e.message : t('settings.services.failedToSave'))
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-xl"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-base font-semibold text-[var(--color-text)]">
            {service ? t('settings.services.editService') : t('settings.services.newService')}
          </h2>
          <button onClick={onClose} className="text-[var(--color-text-muted)] hover:text-[var(--color-text)]">
            <X size={18} />
          </button>
        </div>

        {serverErr && (
          <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-950/30 dark:text-red-400">
            {serverErr}
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
          <div>
            <label className={labelCls}>{t('settings.services.name')}</label>
            <input {...register('name')} className={inputCls} />
            {errors.name && <p className="mt-1 text-xs text-red-500">{errors.name.message}</p>}
          </div>
          <div>
            <label className={labelCls}>{t('settings.services.description')}</label>
            <textarea {...register('description')} rows={2} className={inputCls + ' resize-none'} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={labelCls}>{t('settings.services.durationMin')}</label>
              <input {...register('duration_minutes')} type="number" min={1} className={inputCls} />
              {errors.duration_minutes && (
                <p className="mt-1 text-xs text-red-500">{errors.duration_minutes.message}</p>
              )}
            </div>
            <div>
              <label className={labelCls}>{t('settings.services.bufferMin')}</label>
              <input {...register('buffer_minutes')} type="number" min={0} className={inputCls} />
            </div>
          </div>
          <div>
            <label className={labelCls}>{t('settings.services.priceCents')}</label>
            <input {...register('price_cents')} type="number" min={0} className={inputCls} />
            {errors.price_cents && (
              <p className="mt-1 text-xs text-red-500">{errors.price_cents.message}</p>
            )}
          </div>
          <div>
            <label className={labelCls}>{t('settings.services.colourHex')}</label>
            <input {...register('color')} className={inputCls} placeholder="#6366f1" maxLength={7} />
          </div>
          <div className="flex items-center gap-4 pt-1">
            <label className="flex items-center gap-2 text-sm text-[var(--color-text)]">
              <input {...register('is_active')} type="checkbox" />
              {t('settings.services.active')}
            </label>
            <label className="flex items-center gap-2 text-sm text-[var(--color-text)]">
              <input {...register('is_bookable_online')} type="checkbox" />
              {t('settings.services.bookableOnline')}
            </label>
          </div>
          <div className="flex gap-3 pt-2">
            <button type="submit" disabled={isSubmitting} className={btnPrimary}>
              {isSubmitting ? t('common.saving') : t('settings.services.saveService')}
            </button>
            <button type="button" onClick={onClose} className={btnSecondary}>{t('common.cancel')}</button>
          </div>
        </form>
      </div>
    </div>
  )
}

function ServicesTab() {
  const { t } = useTranslation()
  const [services, setServices] = useState<Service[]>([])
  const [loading, setLoading] = useState(true)
  const [editTarget, setEditTarget] = useState<Service | null | undefined>(undefined)

  const load = async () => {
    setLoading(true)
    try {
      const data = await servicesApi.list()
      setServices(data.items)
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const handleDelete = async (id: string) => {
    if (!confirm(t('settings.services.deleteConfirm'))) return
    await servicesApi.delete(id).catch(() => {})
    load()
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-[var(--color-text-muted)]">{t('settings.services.manageServices')}</p>
        <button onClick={() => setEditTarget(null)} className={btnPrimary + ' flex items-center gap-1.5'}>
          <Plus size={15} /> {t('settings.services.addService')}
        </button>
      </div>

      {loading ? (
        <p className="text-sm text-[var(--color-text-muted)]">{t('common.loading')}</p>
      ) : services.length === 0 ? (
        <div className="rounded-xl border border-dashed border-[var(--color-border)] p-10 text-center text-[var(--color-text-muted)] text-sm">
          {t('settings.services.noServices')}
        </div>
      ) : (
        <div className="space-y-2">
          {services.map(s => (
            <div
              key={s.id}
              className={cn(
                'flex items-center justify-between rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3 gap-3',
                !s.is_active && 'opacity-50',
              )}
            >
              <div className="flex items-center gap-3 min-w-0">
                {s.color && (
                  <span className="h-3 w-3 rounded-full flex-shrink-0" style={{ background: s.color }} />
                )}
                <div className="min-w-0">
                  <p className="text-sm font-medium text-[var(--color-text)] truncate">{s.name}</p>
                  <p className="text-xs text-[var(--color-text-muted)]">
                    {formatDuration(s.duration_minutes)} · {formatPrice(s.price_cents)}
                    {!s.is_bookable_online && ` · ${t('settings.services.notOnline')}`}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-1 flex-shrink-0">
                <button
                  onClick={() => setEditTarget(s)}
                  className="flex h-8 w-8 items-center justify-center rounded-lg text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)]"
                >
                  <Pencil size={14} />
                </button>
                <button
                  onClick={() => handleDelete(s.id)}
                  className="flex h-8 w-8 items-center justify-center rounded-lg text-[var(--color-text-muted)] hover:text-[var(--color-danger)] hover:bg-[var(--color-surface-raised)]"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {editTarget !== undefined && (
        <ServiceModal
          service={editTarget}
          onClose={() => setEditTarget(undefined)}
          onSaved={() => { setEditTarget(undefined); load() }}
        />
      )}
    </div>
  )
}

// ── Working Hours Tab ────────────────────────────────────────────────────────

type DayRow = WorkingHoursCreate & { changed: boolean }

function WorkingHoursTab() {
  const { t } = useTranslation()
  const [rows, setRows] = useState<DayRow[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    availabilityApi.getWorkingHours().then((data: WorkingHours[]) => {
      const map = new Map(data.map(h => [h.day_of_week, h]))
      setRows(DAYS.map(day => {
        const existing = map.get(day)
        return {
          day_of_week:     day,
          is_open:         existing?.is_open ?? (day !== 'saturday' && day !== 'sunday'),
          open_time:       existing?.open_time ?? '09:00:00',
          close_time:      existing?.close_time ?? '17:00:00',
          break_start:     existing?.break_start ?? null,
          break_end:       existing?.break_end ?? null,
          staff_member_id: null,
          changed:         false,
        }
      }))
    }).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const update = (idx: number, patch: Partial<DayRow>) => {
    setRows(prev => prev.map((r, i) => i === idx ? { ...r, ...patch, changed: true } : r))
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      const payload: WorkingHoursCreate[] = rows.map(r => ({
        day_of_week:     r.day_of_week,
        is_open:         r.is_open,
        open_time:       r.is_open ? r.open_time : null,
        close_time:      r.is_open ? r.close_time : null,
        break_start:     r.is_open ? r.break_start : null,
        break_end:       r.is_open ? r.break_end : null,
        staff_member_id: null,
      }))
      await availabilityApi.upsertWorkingHours(payload)
      setSaved(true)
      setTimeout(() => setSaved(false), 2500)
    } catch {
      // ignore
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <p className="text-sm text-[var(--color-text-muted)]">{t('common.loading')}</p>

  return (
    <div className="space-y-4 max-w-2xl">
      <p className="text-sm text-[var(--color-text-muted)]">
        {t('settings.workingHours.setAvailability')}
      </p>
      <div className="space-y-2">
        {rows.map((row, idx) => (
          <div
            key={row.day_of_week}
            className="flex flex-wrap items-center gap-3 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3"
          >
            <div className="w-24 flex-shrink-0">
              <span className="text-sm font-medium text-[var(--color-text)]">
                {t(`settings.workingHours.days.${row.day_of_week}`)}
              </span>
            </div>
            <label className="flex items-center gap-2 text-sm text-[var(--color-text-muted)]">
              <input type="checkbox" checked={row.is_open} onChange={e => update(idx, { is_open: e.target.checked })} />
              {t('settings.workingHours.open')}
            </label>
            {row.is_open && (
              <>
                <div className="flex items-center gap-1.5">
                  <input
                    type="time"
                    value={(row.open_time ?? '09:00:00').slice(0, 5)}
                    onChange={e => update(idx, { open_time: e.target.value + ':00' })}
                    className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] px-2 py-1 text-sm text-[var(--color-text)] focus:outline-none focus:ring-1 focus:ring-[var(--color-primary)]"
                  />
                  <span className="text-xs text-[var(--color-text-muted)]">{t('settings.workingHours.to')}</span>
                  <input
                    type="time"
                    value={(row.close_time ?? '17:00:00').slice(0, 5)}
                    onChange={e => update(idx, { close_time: e.target.value + ':00' })}
                    className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] px-2 py-1 text-sm text-[var(--color-text)] focus:outline-none focus:ring-1 focus:ring-[var(--color-primary)]"
                  />
                </div>
                <div className="flex items-center gap-1.5 text-xs text-[var(--color-text-muted)]">
                  <span>{t('settings.workingHours.break')}</span>
                  <input
                    type="time"
                    value={(row.break_start ?? '').slice(0, 5)}
                    onChange={e => update(idx, { break_start: e.target.value ? e.target.value + ':00' : null })}
                    className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] px-2 py-1 text-sm text-[var(--color-text)] focus:outline-none focus:ring-1 focus:ring-[var(--color-primary)]"
                  />
                  <span>–</span>
                  <input
                    type="time"
                    value={(row.break_end ?? '').slice(0, 5)}
                    onChange={e => update(idx, { break_end: e.target.value ? e.target.value + ':00' : null })}
                    className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] px-2 py-1 text-sm text-[var(--color-text)] focus:outline-none focus:ring-1 focus:ring-[var(--color-primary)]"
                  />
                </div>
              </>
            )}
          </div>
        ))}
      </div>
      <div className="flex items-center gap-3">
        <button onClick={handleSave} disabled={saving} className={btnPrimary}>
          {saving ? t('common.saving') : t('settings.workingHours.saveHours')}
        </button>
        {saved && (
          <span className="flex items-center gap-1 text-sm text-green-600">
            <Check size={14} /> {t('common.saved')}
          </span>
        )}
      </div>
    </div>
  )
}

// ── Blocked Dates Tab ────────────────────────────────────────────────────────

const blockedSchema = z.object({
  start_date: z.string().min(1, 'Required'),
  end_date:   z.string().min(1, 'Required'),
  reason:     z.string().optional(),
})
type BlockedForm = z.infer<typeof blockedSchema>

function BlockedDatesTab() {
  const { t } = useTranslation()
  const [blocked, setBlocked] = useState<BlockedDate[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)

  const { register, handleSubmit, reset, formState: { isSubmitting } } = useForm<BlockedForm>({
    resolver: zodResolver(blockedSchema),
  })

  const load = async () => {
    setLoading(true)
    try {
      setBlocked(await availabilityApi.getBlockedDates())
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const onSubmit = async (values: BlockedForm) => {
    await availabilityApi.createBlockedDate({
      start_date: values.start_date,
      end_date:   values.end_date,
      reason:     values.reason || null,
      all_day:    true,
    })
    reset()
    setShowForm(false)
    load()
  }

  const handleDelete = async (id: string) => {
    await availabilityApi.deleteBlockedDate(id).catch(() => {})
    load()
  }

  return (
    <div className="space-y-4 max-w-lg">
      <div className="flex items-center justify-between">
        <p className="text-sm text-[var(--color-text-muted)]">{t('settings.blockedDates.blockHolidays')}</p>
        <button onClick={() => setShowForm(s => !s)} className={btnPrimary + ' flex items-center gap-1.5'}>
          <Plus size={15} /> {t('settings.blockedDates.addBlock')}
        </button>
      </div>
      {showForm && (
        <form
          onSubmit={handleSubmit(onSubmit)}
          className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 space-y-3"
        >
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={labelCls}>{t('settings.blockedDates.startDate')}</label>
              <input {...register('start_date')} type="date" className={inputCls} />
            </div>
            <div>
              <label className={labelCls}>{t('settings.blockedDates.endDate')}</label>
              <input {...register('end_date')} type="date" className={inputCls} />
            </div>
          </div>
          <div>
            <label className={labelCls}>{t('settings.blockedDates.reason')}</label>
            <input {...register('reason')} className={inputCls} placeholder={t('settings.blockedDates.reasonPlaceholder')} />
          </div>
          <div className="flex gap-3">
            <button type="submit" disabled={isSubmitting} className={btnPrimary}>
              {isSubmitting ? t('settings.blockedDates.adding') : t('settings.blockedDates.addBlock')}
            </button>
            <button type="button" onClick={() => setShowForm(false)} className={btnSecondary}>{t('common.cancel')}</button>
          </div>
        </form>
      )}
      {loading ? (
        <p className="text-sm text-[var(--color-text-muted)]">{t('common.loading')}</p>
      ) : blocked.length === 0 ? (
        <div className="rounded-xl border border-dashed border-[var(--color-border)] p-8 text-center text-[var(--color-text-muted)] text-sm">
          {t('settings.blockedDates.noBlockedDates')}
        </div>
      ) : (
        <div className="space-y-2">
          {blocked.map(b => (
            <div
              key={b.id}
              className="flex items-center justify-between rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3"
            >
              <div>
                <p className="text-sm text-[var(--color-text)]">
                  {b.start_date === b.end_date ? b.start_date : `${b.start_date} → ${b.end_date}`}
                </p>
                {b.reason && <p className="text-xs text-[var(--color-text-muted)]">{b.reason}</p>}
              </div>
              <button
                onClick={() => handleDelete(b.id)}
                className="flex h-8 w-8 items-center justify-center rounded-lg text-[var(--color-text-muted)] hover:text-[var(--color-danger)] hover:bg-[var(--color-surface-raised)]"
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ── Main Page ────────────────────────────────────────────────────────────────

export default function SettingsPage() {
  const { t } = useTranslation()
  const [activeTab, setActiveTab] = useState<Tab>('profile')

  return (
    <div className="space-y-6">
      <div className="flex gap-1 border-b border-[var(--color-border)]">
        {TABS.map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={cn(
              'px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors',
              activeTab === tab
                ? 'border-[var(--color-primary)] text-[var(--color-primary)]'
                : 'border-transparent text-[var(--color-text-muted)] hover:text-[var(--color-text)]',
            )}
          >
            {t(`settings.tabs.${tab}`)}
          </button>
        ))}
      </div>
      <div>
        {activeTab === 'profile'       && <ProfileTab />}
        {activeTab === 'services'      && <ServicesTab />}
        {activeTab === 'workingHours'  && <WorkingHoursTab />}
        {activeTab === 'blockedDates'  && <BlockedDatesTab />}
      </div>
    </div>
  )
}
