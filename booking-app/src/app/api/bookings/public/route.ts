import { NextRequest, NextResponse } from 'next/server'
import { randomUUID } from 'crypto'
import { addBooking, getCourtPrices, countUpcomingBookingsForPhone } from '@/lib/store'
import { getMergedBookingsForDate } from '@/lib/mergedBookings'
import { COURTS, TIME_SLOTS } from '@/lib/constants'

/**
 * Booking without an account. Players give only a name and mobile; account
 * setup is offered afterwards, never as a gate in front of booking.
 *
 * Because this is unauthenticated it needs guardrails, or it could be used to
 * block out every court:
 *   - the mobile must look like a real Omani number
 *   - a number may hold only MAX_UPCOMING_PER_PHONE future bookings
 *   - a burst limit per IP
 */

const MAX_UPCOMING_PER_PHONE = 3
const IP_WINDOW_MS = 60 * 60 * 1000
const MAX_PER_IP_PER_WINDOW = 6

// In-process counter. Resets on deploy, which is fine for burst control; the
// per-phone cap is the durable limit.
const ipHits = new Map<string, number[]>()

function rateLimited(ip: string): boolean {
  const now = Date.now()
  const hits = (ipHits.get(ip) ?? []).filter((t) => now - t < IP_WINDOW_MS)
  hits.push(now)
  ipHits.set(ip, hits)
  if (ipHits.size > 5000) ipHits.clear() // crude guard against unbounded growth
  return hits.length > MAX_PER_IP_PER_WINDOW
}

/** Oman mobiles are 8 digits starting 7, 9 or 8; tolerate a +968 prefix. */
function normalisePhone(raw: string): string | null {
  let d = raw.replace(/\D/g, '')
  if (d.startsWith('00968')) d = d.slice(5)
  else if (d.startsWith('968') && d.length > 8) d = d.slice(3)
  if (!/^[789]\d{7}$/.test(d)) return null
  return d
}

function timeToMinutes(t: string): number {
  const [h, m] = t.split(':').map(Number)
  return h * 60 + m
}

function addMinutes(t: string, mins: number): string {
  const total = timeToMinutes(t) + mins
  return `${String(Math.floor(total / 60)).padStart(2, '0')}:${String(total % 60).padStart(2, '0')}`
}

function localDateStr(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

export async function POST(req: NextRequest) {
  const ip =
    req.headers.get('x-forwarded-for')?.split(',')[0].trim() ??
    req.headers.get('x-real-ip') ??
    'unknown'

  if (rateLimited(ip)) {
    return NextResponse.json(
      { error: 'Too many booking attempts. Please try again later or call the club.' },
      { status: 429 }
    )
  }

  const body = await req.json().catch(() => ({})) as {
    courtId?: string; date?: string; startTime?: string
    durationMinutes?: number; playerName?: string; playerPhone?: string
  }

  const { courtId, date, startTime } = body
  const duration = Number(body.durationMinutes)
  const playerName = (body.playerName ?? '').trim()

  if (!courtId || !date || !startTime || !duration || !playerName || !body.playerPhone) {
    return NextResponse.json({ error: 'Please fill in every field.' }, { status: 400 })
  }
  if (playerName.length < 2 || playerName.length > 80) {
    return NextResponse.json({ error: 'Please enter your full name.' }, { status: 400 })
  }

  const phone = normalisePhone(body.playerPhone)
  if (!phone) {
    return NextResponse.json(
      { error: 'Enter a valid Omani mobile number, for example 9123 4567.' },
      { status: 400 }
    )
  }

  if (![60, 90, 120].includes(duration)) {
    return NextResponse.json({ error: 'Choose a duration of 60, 90 or 120 minutes.' }, { status: 400 })
  }
  if (!COURTS.some((c) => c.id === courtId)) {
    return NextResponse.json({ error: 'Unknown court.' }, { status: 400 })
  }
  if (!TIME_SLOTS.includes(startTime)) {
    return NextResponse.json({ error: 'Invalid start time.' }, { status: 400 })
  }

  const today = localDateStr(new Date())
  const maxDate = new Date()
  maxDate.setDate(maxDate.getDate() + 30)
  if (date < today || date > localDateStr(maxDate)) {
    return NextResponse.json({ error: 'Bookings open for the next 30 days only.' }, { status: 400 })
  }

  const endTime = addMinutes(startTime, duration)
  const closing = timeToMinutes(TIME_SLOTS[TIME_SLOTS.length - 1]) + 30
  if (timeToMinutes(endTime) > closing) {
    return NextResponse.json({ error: 'That would run past closing time.' }, { status: 400 })
  }

  // Don't allow booking a slot that has already started today.
  if (date === today) {
    const now = new Date()
    if (timeToMinutes(startTime) <= now.getHours() * 60 + now.getMinutes()) {
      return NextResponse.json({ error: 'That time has already passed.' }, { status: 400 })
    }
  }

  const upcoming = await countUpcomingBookingsForPhone(phone, today)
  if (upcoming >= MAX_UPCOMING_PER_PHONE) {
    return NextResponse.json(
      {
        error: `This number already has ${upcoming} upcoming bookings. Please call the club to book more.`,
      },
      { status: 409 }
    )
  }

  // Conflict check against MatchPoint + local bookings.
  const existing = (await getMergedBookingsForDate(date)).filter((b) => b.status !== 'cancelled')
  const startM = timeToMinutes(startTime)
  const endM = timeToMinutes(endTime)
  const clash = existing.some((b) => {
    if (b.courtId !== courtId) return false
    return startM < timeToMinutes(b.endTime) && endM > timeToMinutes(b.startTime)
  })
  if (clash) {
    return NextResponse.json(
      { error: 'Sorry, that slot was just taken. Please pick another.' },
      { status: 409 }
    )
  }

  const prices = await getCourtPrices()
  const priceTotal = ((prices[courtId] ?? 0) * duration) / 60

  const booking = {
    id: randomUUID(),
    courtId,
    date,
    startTime,
    endTime,
    playerName,
    playerPhone: phone,
    notes: '',
    isRecurring: false,
    status: 'confirmed' as const,
    createdAt: new Date().toISOString(),
    priceTotal,
    durationMinutes: duration,
    bookingSource: 'online',
  }

  await addBooking(booking)

  return NextResponse.json(
    {
      ok: true,
      booking: {
        id: booking.id,
        courtId, date, startTime, endTime,
        playerName, playerPhone: phone, priceTotal,
      },
    },
    { status: 201 }
  )
}
