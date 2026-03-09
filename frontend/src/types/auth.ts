export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
  refresh_token: string
}

export interface FreelancerMe {
  id: string
  email: string
  username: string
  first_name: string
  last_name: string
  phone: string | null
  business_name: string | null
  bio: string | null
  avatar_url: string | null
  address_line1: string | null
  address_line2: string | null
  city: string | null
  state: string | null
  postcode: string | null
  country: string
  timezone: string
  currency: string
  service_category_id: string | null
  is_active: boolean
  is_verified: boolean
  created_at: string
  updated_at: string
}

export interface FreelancerUpdate {
  first_name?: string
  last_name?: string
  phone?: string | null
  business_name?: string | null
  bio?: string | null
  address_line1?: string | null
  address_line2?: string | null
  city?: string | null
  state?: string | null
  postcode?: string | null
  country?: string
  timezone?: string
  currency?: string
  avatar_url?: string | null
  service_category_id?: string | null
}

export interface ApiError {
  detail: string
  code?: string
}
