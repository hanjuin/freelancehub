export type DayOfWeek = 'monday' | 'tuesday' | 'wednesday' | 'thursday' | 'friday' | 'saturday' | 'sunday'

export interface WorkingHours {
  id: string
  freelancer_id: string
  staff_member_id: string | null
  day_of_week: DayOfWeek
  is_open: boolean
  open_time: string | null   // "HH:MM:SS"
  close_time: string | null
  break_start: string | null
  break_end: string | null
}

export interface WorkingHoursCreate {
  day_of_week: DayOfWeek
  is_open: boolean
  open_time?: string | null
  close_time?: string | null
  break_start?: string | null
  break_end?: string | null
  staff_member_id?: string | null
}

export interface BlockedDate {
  id: string
  freelancer_id: string
  staff_member_id: string | null
  start_date: string   // "YYYY-MM-DD"
  end_date: string
  reason: string | null
  all_day: boolean
  block_start_time: string | null
  block_end_time: string | null
  created_at: string
  updated_at: string
}

export interface BlockedDateCreate {
  start_date: string
  end_date: string
  reason?: string | null
  all_day?: boolean
  block_start_time?: string | null
  block_end_time?: string | null
}

export interface AvailableSlot {
  start_time: string  // ISO datetime
  end_time: string
}
