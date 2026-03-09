/**
 * Public booking API — no authentication required.
 * Uses raw fetch (not the authenticated `api` client).
 */

import type { Service } from '@/types/service'
import type { AvailableSlot } from '@/types/availability'

const BASE = '/api/v1/public'

async function publicGet<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error((body as { detail?: string }).detail ?? `HTTP ${res.status}`)
  }
  return res.json() as Promise<T>
}

async function publicPost<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const b = await res.json().catch(() => ({}))
    throw new Error((b as { detail?: string }).detail ?? `HTTP ${res.status}`)
  }
  return res.json() as Promise<T>
}

export interface PublicProfile {
  id: string
  username: string
  first_name: string
  last_name: string
  business_name: string | null
  bio: string | null
  avatar_url: string | null
  timezone: string
  currency: string
  average_rating: number | null
  services: Service[]
}

export interface PublicBookingCreate {
  service_id: string
  start_time: string   // ISO datetime
  first_name: string
  last_name: string
  email: string
  phone?: string | null
  customer_notes?: string | null
  staff_member_id?: string | null
  custom_answers?: { field_id: string; answer: string }[]
}

export interface BookingConfirmation {
  booking_id: string
  cancel_token: string
  message: string
  status: string
}

export const publicApi = {
  getProfile: (username: string) =>
    publicGet<PublicProfile>(`/${username}`),

  getServices: (username: string) =>
    publicGet<Service[]>(`/${username}/services`),

  getAvailableSlots: (username: string, serviceId: string, date: string) =>
    publicGet<AvailableSlot[]>(
      `/${username}/available-slots?service_id=${serviceId}&date=${date}`,
    ),

  createBooking: (username: string, data: PublicBookingCreate) =>
    publicPost<BookingConfirmation>(`/${username}/bookings`, data),
}
