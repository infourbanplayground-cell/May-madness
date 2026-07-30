import { NextRequest, NextResponse } from 'next/server'
import { getPendingMatchpointEntry, setBookingSynced } from '@/lib/store'
import { COURTS } from '@/lib/constants'

const COURT_NAME = new Map(COURTS.map((c) => [c.id, c.name]))

export async function GET() {
  const pending = await getPendingMatchpointEntry()
  return NextResponse.json({
    ok: true,
    count: pending.length,
    bookings: pending.map((b) => ({
      ...b,
      courtName: COURT_NAME.get(b.courtId) ?? b.courtId,
    })),
  })
}

export async function PATCH(req: NextRequest) {
  const body = await req.json().catch(() => ({})) as { id?: string; synced?: boolean }
  if (!body.id) {
    return NextResponse.json({ ok: false, error: 'id is required' }, { status: 400 })
  }
  const updated = await setBookingSynced(body.id, body.synced !== false)
  if (!updated) {
    return NextResponse.json({ ok: false, error: 'Booking not found' }, { status: 404 })
  }
  return NextResponse.json({ ok: true })
}
