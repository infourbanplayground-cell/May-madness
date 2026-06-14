import { NextRequest, NextResponse } from 'next/server'
import { getMemberById, getBookingsForMember } from '@/lib/store'
import { getMemberFromRequest } from '@/lib/memberAuth'

export async function GET(req: NextRequest) {
  const memberId = getMemberFromRequest(req)
  if (!memberId) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const member = await getMemberById(memberId)
  if (!member) {
    return NextResponse.json({ error: 'Member not found' }, { status: 404 })
  }

  const allBookings = await getBookingsForMember(memberId)
  const today = new Date().toISOString().split('T')[0]

  const upcomingBookings = allBookings.filter(
    (b) => b.status === 'confirmed' && b.date >= today
  ).sort((a, b) => a.date.localeCompare(b.date) || a.startTime.localeCompare(b.startTime))

  const pastBookings = allBookings.filter(
    (b) => b.status === 'cancelled' || b.date < today
  ).sort((a, b) => b.date.localeCompare(a.date) || b.startTime.localeCompare(a.startTime))

  return NextResponse.json({ member, upcomingBookings, pastBookings })
}
