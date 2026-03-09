import { api } from './client'
import type { Service, ServiceCreate, ServiceUpdate } from '@/types/service'

interface PaginatedServices {
  items: Service[]
  total: number
  page: number
  pages: number
}

export const servicesApi = {
  list: (page = 1, pageSize = 100) =>
    api.get<PaginatedServices>(`/services/?page=${page}&page_size=${pageSize}`),

  create: (data: ServiceCreate) => api.post<Service>('/services/', data),

  update: (id: string, data: ServiceUpdate) => api.put<Service>(`/services/${id}`, data),

  delete: (id: string) => api.delete<void>(`/services/${id}`),
}
