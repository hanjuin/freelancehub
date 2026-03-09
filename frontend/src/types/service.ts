export interface ServiceCategory {
  id: string
  name: string
  slug: string
  icon: string | null
  is_system: boolean
}

export interface Service {
  id: string
  freelancer_id: string
  name: string
  description: string | null
  duration_minutes: number
  buffer_minutes: number
  price_cents: number
  is_active: boolean
  is_bookable_online: boolean
  sort_order: number
  color: string | null
  created_at: string
  updated_at: string
}

export interface ServiceCreate {
  name: string
  description?: string | null
  duration_minutes: number
  buffer_minutes?: number
  price_cents: number
  is_active?: boolean
  is_bookable_online?: boolean
  sort_order?: number
  color?: string | null
}

export interface ServiceUpdate {
  name?: string
  description?: string | null
  duration_minutes?: number
  buffer_minutes?: number
  price_cents?: number
  is_active?: boolean
  is_bookable_online?: boolean
  sort_order?: number
  color?: string | null
}
