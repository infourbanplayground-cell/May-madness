import { NextRequest, NextResponse } from 'next/server'
import { setCourtPrice } from '@/lib/store'
import { COURTS } from '@/lib/constants'

export async function PUT(req: NextRequest) {
  // Admin-only: enforced by proxy.ts which requires admin_session for /api/admin/*
  const session = req.cookies.get('admin_session')
  if (!session || session.value !== 'authenticated') {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const body = await req.json()
  const { courtId, pricePerHour } = body

  if (!courtId || pricePerHour === undefined || pricePerHour === null) {
    return NextResponse.json({ error: 'courtId and pricePerHour are required' }, { status: 400 })
  }

  if (!COURTS.find((c) => c.id === courtId)) {
    return NextResponse.json({ error: 'Invalid court ID' }, { status: 400 })
  }

  const price = Number(pricePerHour)
  if (isNaN(price) || price < 0) {
    return NextResponse.json({ error: 'pricePerHour must be a non-negative number' }, { status: 400 })
  }

  await setCourtPrice(courtId, price)
  return NextResponse.json({ ok: true, courtId, pricePerHour: price })
}
