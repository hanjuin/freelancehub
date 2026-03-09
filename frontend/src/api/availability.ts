import { api } from './client'
import type { WorkingHours, WorkingHoursCreate, BlockedDate, BlockedDateCreate } from '@/types/availability'

export const availabilityApi = {
  getWorkingHours: () =>
    api.get<WorkingHours[]>('/availability/working-hours'),

  upsertWorkingHours: (items: WorkingHoursCreate[]) =>
    api.put<WorkingHours[]>('/availability/working-hours', items),

  getBlockedDates: () =>
    api.get<BlockedDate[]>('/availability/blocked-dates'),

  createBlockedDate: (data: BlockedDateCreate) =>
    api.post<BlockedDate>('/availability/blocked-dates', data),

  deleteBlockedDate: (id: string) =>
    api.delete<void>(`/availability/blocked-dates/${id}`),
}
