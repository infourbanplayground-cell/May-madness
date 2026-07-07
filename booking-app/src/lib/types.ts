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
  memberId?: string
  priceTotal?: number
  durationMinutes?: number
  bookingSource?: string
}

export type Member = {
  id: string
  name: string
  phone: string
  createdAt: string
}

export type RecordingStatus = 'pending' | 'recording' | 'uploading' | 'ready' | 'failed'

export type Recording = {
  id: string
  courtId: string
  phone: string
  durationMinutes: number
  status: RecordingStatus
  requestedAt: string
  startedAt?: string
  finishedAt?: string
  filePath?: string
  fileSizeBytes?: number
  downloadToken?: string
  expiresAt?: string
  error?: string
}
