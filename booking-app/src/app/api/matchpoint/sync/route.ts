import { NextRequest, NextResponse } from 'next/server'
import { fetchMpBookings, MpBooking } from '@/lib/matchpoint'
import { addBooking, getBookings } from '@/lib/store'
import { COURTS } from '@/lib/constants'
import { Booking } from '@/lib/types'

function extractDate(b: MpBooking): string {
  const raw = b.date ?? b.startDate ?? b.start ?? ''
  return typeof raw === 'string' ? raw.slice(0, 10) : ''
}

function extractTime(val: unknown): string {
  const s = String(val ?? '').trim()
  // Accept HH:MM or HH:MM:SS or ISO datetime
  const m = s.match(/(\d{2}:\d{2})/)
  return m ? m[1] : ''
}

function guessCourt(b: MpBooking): string {
  const name = String(b.courtName ?? b.courtId ?? '').toLowerCase()
  for (const c of COURTS) {
    if (name.includes(c.id) || name.includes(c.name.toLowerCase())) return c.id
  }
  // Map by index if courtId is numeric
  const idx = parseInt(String(b.courtId ?? '1'), 10)
  if (idx >= 1 && idx <= COURTS.length) return `court-${idx}`
  return COURTS[0].id
}

function mpBookingToLocal(b: MpBooking, existingIds: Set<string>): Booking | null {
  const id = `mp-${b.id}`
  if (existingIds.has(id)) return null

  const date = extractDate(b)
  const startTime = extractTime(b.startTime ?? b.start)
  const endTime = extractTime(b.endTime ?? b.end)

  if (!date || !startTime || !endTime) return null

  const customerName = String(b.customerName ?? b.name ?? 'MatchPoint Import').trim()
  const customerPhone = String(b.customerPhone ?? b.phone ?? '').trim()

  return {
    id,
    courtId: guessCourt(b),
    date,
    startTime,
    endTime,
    playerName: customerName,
    playerPhone: customerPhone,
    notes: String(b.notes ?? '').trim(),
    isRecurring: false,
    status: b.status === 'cancelled' ? 'cancelled' : 'confirmed',
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
