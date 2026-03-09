import { api } from './client'
import type {
  Booking,
  BookingCreate,
  BookingNotesUpdate,
  BookingStatusUpdate,
  BookingsListParams,
  PaginatedBookings,
} from '@/types/booking'

function buildQuery(params: BookingsListParams): string {
  const q = new URLSearchParams()
  if (params.page) q.set('page', String(params.page))
  if (params.page_size) q.set('page_size', String(params.page_size))
  if (params.status) q.set('status', params.status)
  if (params.from_date) q.set('from_date', params.from_date)
  if (params.to_date) q.set('to_date', params.to_date)
  if (params.customer_id) q.set('customer_id', params.customer_id)
  if (params.service_id) q.set('service_id', params.service_id)
  if (params.search) q.set('search', params.search)
  const s = q.toString()
  return s ? `?${s}` : ''
}

export const bookingsApi = {
  list: (params: BookingsListParams = {}) =>
    api.get<PaginatedBookings>(`/bookings/${buildQuery(params)}`),

  get: (id: string) => api.get<Booking>(`/bookings/${id}`),

  create: (data: BookingCreate) => api.post<Booking>('/bookings/', data),

  updateStatus: (id: string, data: BookingStatusUpdate) =>
    api.patch<Booking>(`/bookings/${id}/status`, data),

  updateNotes: (id: string, data: BookingNotesUpdate) =>
    api.put<Booking>(`/bookings/${id}`, data),

  delete: (id: string) => api.delete<void>(`/bookings/${id}`),
}
