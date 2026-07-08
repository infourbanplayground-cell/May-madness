import 'server-only'
import { fetchMpBookings, MpBooking } from './matchpoint'
import { getBookingsForDate } from './store'
import { COURTS } from './constants'
import { Booking } from './types'

export function guessCourt(resourceName: string): string {
  const lower = (resourceName ?? '').toLowerCase()
  for (const c of COURTS) {
    if (lower.includes(c.name.toLowerCase())) return c.id
  }
  const m = lower.match(/\d+/)
  if (m) {
    const idx = parseInt(m[0], 10)
    if (idx >= 1 && idx <= COURTS.length) return `court-${idx}`
  }
  return COURTS[0].id
}

export function mpToBooking(b: MpBooking): Booking {
  const first = b.Participants?.[0]
  return {
    id: `mp-${b.Id}`,
    courtId: guessCourt(b.ResourceName ?? ''),
    date: b.Date,
    startTime: b.StartTime,
    endTime: b.EndTime,
    playerName: first?.Name || b.Description || 'MatchPoint',
    playerPhone: first?.Phone || '',
    notes: b.Description ?? '',
    isRecurring: false,
    status: b.Status === 'CANCELED' ? 'cancelled' : 'confirmed',
    createdAt: new Date().toISOString(),
    bookingSource: 'matchpoint',
  }
}

/**
 * Live bookings for a date: MatchPoint (source of truth) merged with
 * local-only bookings made through this app. If MatchPoint is
 * unreachable we degrade gracefully to local data.
 */
export async function getMergedBookingsForDate(date: string): Promise<Booking[]> {
  const [mpBookings, localBookings] = await Promise.all([
    fetchMpBookings(date, date).catch(() => [] as MpBooking[]),
    getBookingsForDate(date),
  ])
  const mpIds = new Set(mpBookings.map((b) => `mp-${b.Id}`))
  const localOnly = localBookings.filter((b) => !mpIds.has(b.id))
  return [...mpBookings.map(mpToBooking), ...localOnly]
}
