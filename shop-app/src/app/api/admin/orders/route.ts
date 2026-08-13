import { NextRequest, NextResponse } from 'next/server'
import { isAdmin } from '@/lib/adminAuth'
import { initDB, listOrders, ORDER_STATUSES, setOrderStatus, type OrderStatus } from '@/lib/shop'

export const dynamic = 'force-dynamic'

export async function GET() {
  if (!(await isAdmin())) return NextResponse.json({ error: 'Unauthorised' }, { status: 401 })
  await initDB()
  return NextResponse.json(await listOrders())
}

export async function POST(req: NextRequest) {
  if (!(await isAdmin())) return NextResponse.json({ error: 'Unauthorised' }, { status: 401 })
  await initDB()
  const b = (await req.json().catch(() => ({}))) as { ref?: unknown; status?: unknown }
  if (typeof b.ref !== 'string') return NextResponse.json({ error: 'Missing ref' }, { status: 400 })
  if (!ORDER_STATUSES.includes(b.status as OrderStatus)) {
    return NextResponse.json({ error: 'Unknown status' }, { status: 400 })
  }
  try {
    await setOrderStatus(b.ref, b.status as OrderStatus)
  } catch {
    return NextResponse.json({ error: 'Could not update that order' }, { status: 400 })
  }
  return NextResponse.json({ ok: true })
}
