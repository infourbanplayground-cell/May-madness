import { NextRequest, NextResponse } from 'next/server'
import { cancelBooking, updateBooking } from '@/lib/store'

export async function DELETE(_: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  await cancelBooking(id)
  return NextResponse.json({ ok: true })
}

export async function PATCH(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const body = await req.json()
  await updateBooking(id, body)
  return NextResponse.json({ ok: true })
}
