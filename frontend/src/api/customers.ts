import { api } from './client'

export interface CustomerSummary {
  id: string
  first_name: string
  last_name: string | null
  email: string | null
  phone: string | null
}

interface PaginatedCustomers {
  items: CustomerSummary[]
  total: number
  page: number
  pages: number
}

export const customersApi = {
  list: (search?: string, page = 1, pageSize = 50) => {
    const q = new URLSearchParams({ page: String(page), page_size: String(pageSize) })
    if (search) q.set('search', search)
    return api.get<PaginatedCustomers>(`/customers/?${q}`)
  },
}
