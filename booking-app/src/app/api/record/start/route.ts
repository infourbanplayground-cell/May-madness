import { NextRequest, NextResponse } from 'next/server'
import { createRecordingJob, initDB } from '@/lib/store'
import { COURTS } from '@/lib/constants'

const ALLOWED_DURATIONS = [60, 90, 120]

export async function POST(req: NextRequest) {
  const body = await req.json()
  const { courtId, phone, durationMinutes } = body

  if (!COURTS.some((c) => c.id === courtId)) {
    return NextResponse.json({ error: 'unknown court' }, { status: 400 })
  }
  if (!phone || typeof phone !== 'string' || phone.trim().length < 5) {
    return NextResponse.json({ error: 'phone number required' }, { status: 400 })
  }
  if (!ALLOWED_DURATIONS.includes(durationMinutes)) {
    return NextResponse.json({ error: 'invalid duration' }, { status: 400 })
  }

  await initDB()
  const job = await createRecordingJob(courtId, phone.trim(), durationMinutes)
  return NextResponse.json(job, { status: 201 })
}
