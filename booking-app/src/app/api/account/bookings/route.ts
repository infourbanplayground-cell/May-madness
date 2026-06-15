import { NextRequest, NextResponse } from 'next/server'
import { addBooking, getBookingsForDate, getMemberById, getCourtPrices } from '@/lib/store'
import { getMemberFromRequest } from '@/lib/memberAuth'
import { COURTS, TIME_SLOTS } from '@/lib/constants'
import { randomUUID } from 'crypto'

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

export async function POST(req: NextRequest) {
  const memberId = getMemberFromRequest(req)
  if (!memberId) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const member = await getMemberById(memberId)
  if (!member) {
    return NextResponse.json({ error: 'Member not found' }, { status: 404 })
  }

  const { courtId, date, startTime, durationMinutes } = await req.json()

  // Validate inputs
  if (!courtId || !date || !startTime || !durationMinutes) {
    return NextResponse.json({ error: 'courtId, date, startTime, and durationMinutes are required' }, { status: 400 })
  }

  if (![60, 90, 120].includes(Number(durationMinutes))) {
    return NextResponse.json({ error: 'durationMinutes must be 60, 90, or 120' }, { status: 400 })
  }

  const court = COURTS.find((c) => c.id === courtId)
  if (!court) {
    return NextResponse.json({ error: 'Invalid court' }, { status: 400 })
  }

  // Validate date is within allowed range (today + 30 days) — use local date
  function localDateStr(d: Date) {
    return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
  }
  const todayStr = localDateStr(new Date())
  const maxDate = new Date()
  maxDate.setDate(maxDate.getDate() + 30)
  const maxDateStr = localDateStr(maxDate)
  if (date < todayStr || date > maxDateStr) {
    return NextResponse.json({ error: 'Date must be within the next 30 days' }, { status: 400 })
  }

  // Validate startTime is a valid slot
  if (!TIME_SLOTS.includes(startTime)) {
    return NextResponse.json({ error: 'Invalid start time' }, { status: 400 })
  }

  const endTime = addMinutesToTime(startTime, Number(durationMinutes))

  // Validate end time doesn't exceed last slot
  const lastSlot = TIME_SLOTS[TIME_SLOTS.length - 1]
  const lastSlotEnd = addMinutesToTime(lastSlot, 30)
  if (timeToMinutes(endTime) > timeToMinutes(lastSlotEnd)) {
    return NextResponse.json({ error: 'Booking extends past closing time' }, { status: 400 })
  }

  // Check for conflicts
  const existingBookings = await getBookingsForDate(date)
  const startMins = timeToMinutes(startTime)
  const endMins = timeToMinutes(endTime)

  const conflict = existingBookings.find((b) => {
    if (b.courtId !== courtId) return false
    const bStart = timeToMinutes(b.startTime)
    const bEnd = timeToMinutes(b.endTime)
    return startMins < bEnd && endMins > bStart
  })

  if (conflict) {
    return NextResponse.json({ error: 'This slot is already booked' }, { status: 409 })
  }

  // Calculate price
  const prices = await getCourtPrices()
  const pricePerHour = prices[courtId] ?? 0
  const priceTotal = (pricePerHour * Number(durationMinutes)) / 60

  const booking = {
    id: randomUUID(),
    courtId,
    date,
    startTime,
    endTime,
    playerName: member.name,
    playerPhone: member.phone,
    notes: '',
    isRecurring: false,
    status: 'confirmed' as const,
    createdAt: new Date().toISOString(),
    memberId,
    priceTotal,
    durationMinutes: Number(durationMinutes),
    bookingSource: 'member',
  }

  await addBooking(booking)
  return NextResponse.json(booking, { status: 201 })
}
