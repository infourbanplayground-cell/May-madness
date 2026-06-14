export type Court = {
  id: string
  name: string
  sport: string
  color: string
}

export type BookingStatus = 'confirmed' | 'cancelled'

export type Booking = {
  id: string
  courtId: string
  date: string        // YYYY-MM-DD
  startTime: string   // HH:MM (24h)
  endTime: string     // HH:MM (24h)
  playerName: string
  playerPhone: string
  notes: string
  isRecurring: boolean
  recurringDays?: number[] // 0=Sun ... 6=Sat
  recurringUntil?: string  // YYYY-MM-DD
  status: BookingStatus
  createdAt: string
}
