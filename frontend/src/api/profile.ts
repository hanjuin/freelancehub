import { api } from './client'
import type { FreelancerMe, FreelancerUpdate } from '@/types/auth'
import type { ServiceCategory } from '@/types/service'

export const profileApi = {
  getMe: () => api.get<FreelancerMe>('/freelancers/me'),

  updateMe: (data: FreelancerUpdate) => api.put<FreelancerMe>('/freelancers/me', data),

  getCategories: () => api.get<ServiceCategory[]>('/services/categories'),
}
