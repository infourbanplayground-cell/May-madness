import { NextRequest, NextResponse } from 'next/server'
import { getBookings, getBookingsForDate, addBooking } from '@/lib/store'
import { fetchMpBookings, MpBooking } from '@/lib/matchpoint'
import { Booking } from '@/lib/types'
import { COURTS } from '@/lib/constants'
import { randomUUID } from 'crypto'

function guessCourt(resourceName: string): string {
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

function mpToBooking(b: MpBooking): Booking {
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

export async function GET(req: NextRequest) {
  const date = req.nextUrl.searchParams.get('date')

  // Fetch MatchPoint bookings for the requested date (or today)
  const target = date ?? new Date().toISOString().slice(0, 10)
  const [mpBookings, localBookings] = await Promise.all([
    fetchMpBookings(target, target).catch(() => [] as MpBooking[]),
    date ? getBookingsForDate(date) : getBookings(),
  ])

  const mpIds = new Set(mpBookings.map((b) => `mp-${b.Id}`))
  // Merge: MatchPoint bookings + any local-only bookings not in MatchPoint
  const localOnly = localBookings.filter((b) => !mpIds.has(b.id))
  const merged = [...mpBookings.map(mpToBooking), ...localOnly]

  return NextResponse.json(merged)
}

export async function POST(req: NextRequest) {
  const body = await req.json()

  const booking: Booking = {
    id: randomUUID(),
    courtId: body.courtId,
    date: body.date,
    startTime: body.startTime,
    endTime: body.endTime,
    playerName: body.playerName,
    playerPhone: body.playerPhone ?? '',
    notes: body.notes ?? '',
    isRecurring: body.isRecurring ?? false,
    recurringDays: body.recurringDays,
    recurringUntil: body.recurringUntil,
    status: 'confirmed',
    createdAt: new Date().toISOString(),
  }

  await addBooking(booking)
  return NextResponse.json(booking, { status: 201 })
}
