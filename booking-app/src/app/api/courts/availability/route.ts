import { NextRequest, NextResponse } from 'next/server'
import { getBookingsForDate } from '@/lib/store'
import { COURTS, TIME_SLOTS } from '@/lib/constants'

function timeToMinutes(t: string) {
  const [h, m] = t.split(':').map(Number)
  return h * 60 + m
}

function addMinutesToTime(t: string, mins: number): string {
  const total = timeToMinutes(t) + mins
  const h = Math.floor(total / 60).toString().padStart(2, '0')
  const m = (total % 60).toString().padStart(2, '0')
  return `${h}:${m}`
}

export async function GET(req: NextRequest) {
  const { searchParams } = req.nextUrl
  const date = searchParams.get('date')

  if (!date || !/^\d{4}-\d{2}-\d{2}$/.test(date)) {
    return NextResponse.json({ error: 'date query param required (YYYY-MM-DD)' }, { status: 400 })
  }

  const bookings = await getBookingsForDate(date)

  // Build availability map: courtId -> array of slot info
  const result: Record<string, Array<{ startTime: string; endTime: string; available: boolean }>> = {}

  for (const court of COURTS) {
    result[court.id] = TIME_SLOTS.map((startTime) => {
      const endTime = addMinutesToTime(startTime, 30)
      const slotStart = timeToMinutes(startTime)
      const slotEnd = timeToMinutes(endTime)

      const taken = bookings.some((b) => {
        if (b.courtId !== court.id) return false
        const bStart = timeToMinutes(b.startTime)
        const bEnd = timeToMinutes(b.endTime)
        // A slot is taken if any confirmed booking overlaps it
        return slotStart < bEnd && slotEnd > bStart
      })

      return { startTime, endTime, available: !taken }
    })
  }

  return NextResponse.json(result)
}
