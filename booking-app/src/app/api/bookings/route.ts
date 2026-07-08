import { NextRequest, NextResponse } from 'next/server'
import { getBookings, addBooking } from '@/lib/store'
import { getMergedBookingsForDate } from '@/lib/mergedBookings'
import { Booking } from '@/lib/types'
import { randomUUID } from 'crypto'

export async function GET(req: NextRequest) {
  const date = req.nextUrl.searchParams.get('date')
  if (date) {
    return NextResponse.json(await getMergedBookingsForDate(date))
  }
  return NextResponse.json(await getBookings())
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
