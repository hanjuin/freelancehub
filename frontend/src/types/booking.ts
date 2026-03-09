export type BookingStatus = 'pending' | 'confirmed' | 'completed' | 'cancelled' | 'no_show'

export interface CustomerSummary {
  id: string
  first_name: string
  last_name: string | null
  email: string | null
  phone: string | null
}

export interface ServiceSummary {
  id: string
  name: string
  color: string | null
  duration_minutes: number
  price_cents: number
}

export interface Booking {
  id: string
  freelancer_id: string
  customer_id: string
  service_id: string
  staff_member_id: string | null
  recurring_rule_id: string | null
  start_time: string
  end_time: string
  duration_minutes: number
  status: BookingStatus
  price_cents: number
  cancel_token: string
  customer_notes: string | null
  internal_notes: string | null
  cancellation_reason: string | null
  cancelled_by: string | null
  reminder_24h_sent: boolean
  reminder_2h_sent: boolean
  created_at: string
  updated_at: string
  customer: CustomerSummary | null
  service: ServiceSummary | null
}

export interface BookingCreate {
  customer_id: string
  service_id: string
  start_time: string
  customer_notes?: string | null
  staff_member_id?: string | null
}

export interface BookingStatusUpdate {
  status: BookingStatus
  cancellation_reason?: string | null
}

export interface BookingNotesUpdate {
  internal_notes?: string | null
}

export interface BookingsListParams {
  page?: number
  page_size?: number
  status?: BookingStatus | ''
  from_date?: string
  to_date?: string
  customer_id?: string
  service_id?: string
  search?: string
}

export interface PaginatedBookings {
  items: Booking[]
  total: number
  page: number
  pages: number
}
