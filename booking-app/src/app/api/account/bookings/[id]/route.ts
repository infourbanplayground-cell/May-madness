import { NextRequest, NextResponse } from 'next/server'
import { getBookingById, cancelBooking } from '@/lib/store'
import { getMemberFromRequest } from '@/lib/memberAuth'

export async function DELETE(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const memberId = getMemberFromRequest(req)
  if (!memberId) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const { id } = await params
  const booking = await getBookingById(id)

  if (!booking) {
    return NextResponse.json({ error: 'Booking not found' }, { status: 404 })
  }

  if (booking.memberId !== memberId) {
    return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
  }

  if (booking.status === 'cancelled') {
    return NextResponse.json({ error: 'Booking is already cancelled' }, { status: 409 })
  }

  await cancelBooking(id)
  return NextResponse.json({ ok: true })
}
