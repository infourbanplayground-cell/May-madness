import { NextRequest, NextResponse } from 'next/server'
import { getMergedBookingsForDate } from '@/lib/mergedBookings'
import { COURTS } from '@/lib/constants'
import { timingSafeEqual } from 'crypto'

/**
 * Read-only feed for the front-desk board. Guarded by a shared link token
 * rather than a login, so staff can open it from any phone without a password.
 * It exposes customer names and numbers, so the token is the only thing
 * standing between this and the open internet — treat it like a password.
 */
function tokenOk(supplied: string | null): boolean {
  const expected = process.env.DESK_TOKEN
  if (!expected || !supplied) return false
  const a = Buffer.from(supplied)
  const b = Buffer.from(expected)
  if (a.length !== b.length) return false
  return timingSafeEqual(a, b)
}

const COURT_BY_ID = new Map(COURTS.map((c) => [c.id, c]))

export async function GET(req: NextRequest) {
  const { searchParams } = req.nextUrl
  if (!tokenOk(searchParams.get('k'))) {
    return NextResponse.json({ error: 'Not authorised' }, { status: 401 })
  }

  const date = searchParams.get('date')
  if (!date || !/^\d{4}-\d{2}-\d{2}$/.test(date)) {
    return NextResponse.json({ error: 'date required (YYYY-MM-DD)' }, { status: 400 })
  }

  const bookings = (await getMergedBookingsForDate(date))
    .filter((b) => b.status !== 'cancelled')
    .sort((a, b) => a.startTime.localeCompare(b.startTime) || a.courtId.localeCompare(b.courtId))
    .map((b) => {
      const court = COURT_BY_ID.get(b.courtId)
      // mergedBookings falls back to the literal "MatchPoint" when a booking
      // has neither a participant nor a description. That means nothing to
      // someone on the desk, so say what it actually is.
      const name = b.playerName?.trim()
      const playerName = !name || name === 'MatchPoint' ? 'No name on booking' : name

      // MatchPoint auto-generates descriptions like
      // "Ali Nour, booking 22/10/2026 of 8:00 PM-9:00 PM" or the Spanish
      // "reserva diaria día ...". They just restate the row, so drop them and
      // keep only notes a human actually typed.
      const raw = (b.notes ?? '').trim()
      const auto =
        !raw ||
        /\b(booking|reserva)\b/i.test(raw) ||
        (!!name && raw.toLowerCase().startsWith(name.toLowerCase()))
      const notes = auto ? '' : raw

      return {
        id: b.id,
        startTime: b.startTime,
        endTime: b.endTime,
        courtName: court?.name ?? b.courtId,
        courtColor: court?.color ?? '#FF8A3D',
        sport: court?.sport ?? '',
        playerName,
        playerPhone: b.playerPhone,
        notes,
        source: b.bookingSource ?? 'matchpoint',
      }
    })

  return NextResponse.json({ ok: true, date, count: bookings.length, bookings })
}
