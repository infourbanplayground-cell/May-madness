import { NextRequest, NextResponse } from 'next/server'
import { fetchMpBookings, MpBooking } from '@/lib/matchpoint'
import { addBooking, getBookings } from '@/lib/store'
import { COURTS } from '@/lib/constants'
import { Booking } from '@/lib/types'

function guessCourt(resourceName: string): string {
  const lower = resourceName.toLowerCase()
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

function mpBookingToLocal(b: MpBooking, existingIds: Set<string>): Booking | null {
  const id = `mp-${b.Id}`
  if (existingIds.has(id)) return null
  if (!b.Date || !b.StartTime || !b.EndTime) return null

  const firstParticipant = b.Participants?.[0]
  const playerName = firstParticipant?.Name || b.Description || 'MatchPoint Import'
  const playerPhone = firstParticipant?.Phone || ''

  return {
    id,
    courtId: guessCourt(b.ResourceName ?? ''),
    date: b.Date,
    startTime: b.StartTime,
    endTime: b.EndTime,
    playerName,
    playerPhone,
    notes: b.Description ?? '',
    isRecurring: false,
    status: b.Status === 'CANCELED' ? 'cancelled' : 'confirmed',
    createdAt: new Date().toISOString(),
    bookingSource: 'matchpoint',
  }
}

export async function POST(req: NextRequest) {
  const body = await req.json().catch(() => ({})) as { dateFrom?: string; dateTo?: string }
  const today = new Date()
  const yyyy = today.getFullYear()
  const mm = String(today.getMonth() + 1).padStart(2, '0')
  const dd = String(today.getDate()).padStart(2, '0')
  const dateFrom = body.dateFrom ?? `${yyyy}-${mm}-01`
  const dateTo = body.dateTo ?? `${yyyy}-${mm}-${dd}`

  try {
    const [mpBookings, existing] = await Promise.all([
      fetchMpBookings(dateFrom, dateTo),
      getBookings(),
    ])

    const existingIds = new Set(existing.map((b) => b.id))
    const toImport: Booking[] = []

    for (const b of mpBookings) {
      const local = mpBookingToLocal(b, existingIds)
      if (local) toImport.push(local)
    }

    for (const b of toImport) {
      await addBooking(b)
    }

    return NextResponse.json({
      ok: true,
      fetched: mpBookings.length,
      imported: toImport.length,
      skipped: mpBookings.length - toImport.length,
      dateFrom,
      dateTo,
    })
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    return NextResponse.json({ ok: false, error: message }, { status: 502 })
  }
}
