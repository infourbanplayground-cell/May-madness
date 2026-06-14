import { Court, Booking } from './types'

export const COURTS: Court[] = [
  { id: 'court-1', name: 'Court 1', sport: 'Padel', color: '#6366f1' },
  { id: 'court-2', name: 'Court 2', sport: 'Padel', color: '#10b981' },
  { id: 'court-3', name: 'Court 3', sport: 'Pickleball', color: '#f59e0b' },
  { id: 'court-4', name: 'Court 4', sport: 'Pickleball', color: '#ef4444' },
]

export const TIME_SLOTS: string[] = Array.from({ length: 28 }, (_, i) => {
  const totalMinutes = 6 * 60 + i * 30
  const h = Math.floor(totalMinutes / 60).toString().padStart(2, '0')
  const m = (totalMinutes % 60).toString().padStart(2, '0')
  return `${h}:${m}`
}) // 06:00 → 19:30 in 30-min increments

// In-memory store — replace with Supabase calls when ready
let bookings: Booking[] = []

export function getBookings(): Booking[] {
  return bookings
}

export function getBookingsForDate(date: string): Booking[] {
  return bookings.filter((b) => b.date === date && b.status !== 'cancelled')
}

export function addBooking(booking: Booking): void {
  bookings.push(booking)

  if (booking.isRecurring && booking.recurringDays && booking.recurringUntil) {
    expandRecurring(booking)
  }
}

export function cancelBooking(id: string): void {
  const b = bookings.find((x) => x.id === id)
  if (b) b.status = 'cancelled'
}

export function updateBooking(id: string, patch: Partial<Booking>): void {
  const idx = bookings.findIndex((x) => x.id === id)
  if (idx !== -1) bookings[idx] = { ...bookings[idx], ...patch }
}

function expandRecurring(original: Booking) {
  const { recurringDays, recurringUntil, date } = original
  if (!recurringDays || !recurringUntil) return

  const until = new Date(recurringUntil)
  const cursor = new Date(date)
  cursor.setDate(cursor.getDate() + 1)

  while (cursor <= until) {
    if (recurringDays.includes(cursor.getDay())) {
      const d = cursor.toISOString().split('T')[0]
      bookings.push({
        ...original,
        id: `${original.id}-${d}`,
        date: d,
        isRecurring: false,
      })
    }
    cursor.setDate(cursor.getDate() + 1)
  }
}
