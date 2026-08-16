import { NextRequest, NextResponse } from 'next/server'
import { createOrder, initDB, OutOfStock } from '@/lib/shop'

export const dynamic = 'force-dynamic'

const MAX_QTY = 20

export async function POST(req: NextRequest) {
  await initDB()

  let body: unknown
  try {
    body = await req.json()
  } catch {
    return NextResponse.json({ error: 'Malformed request' }, { status: 400 })
  }

  const b = body as {
    name?: unknown
    phone?: unknown
    note?: unknown
    items?: unknown
  }

  const name = typeof b.name === 'string' ? b.name.trim() : ''
  const phone = typeof b.phone === 'string' ? b.phone.trim() : ''
  const note = typeof b.note === 'string' ? b.note.trim().slice(0, 500) : ''

  if (name.length < 2) return NextResponse.json({ error: 'Please give your name' }, { status: 400 })
  // Omani mobiles are 8 digits; allow +968 and spacing but insist on 8-15 digits.
  const digits = phone.replace(/\D/g, '')
  if (digits.length < 8 || digits.length > 15) {
    return NextResponse.json({ error: 'Please give a valid phone number' }, { status: 400 })
  }

  if (!Array.isArray(b.items) || b.items.length === 0) {
    return NextResponse.json({ error: 'Your cart is empty' }, { status: 400 })
  }

  const items: { productId: string; qty: number }[] = []
  for (const raw of b.items) {
    const l = raw as { productId?: unknown; qty?: unknown }
    if (typeof l.productId !== 'string') {
      return NextResponse.json({ error: 'Bad cart contents' }, { status: 400 })
    }
    const qty = Math.floor(Number(l.qty))
    if (!Number.isFinite(qty) || qty < 1 || qty > MAX_QTY) {
      return NextResponse.json({ error: 'Bad quantity' }, { status: 400 })
    }
    // Collapse duplicates so the same product cannot be decremented twice.
    const found = items.find((i) => i.productId === l.productId)
    if (found) found.qty = Math.min(MAX_QTY, found.qty + qty)
    else items.push({ productId: l.productId, qty })
  }

  try {
    const order = await createOrder({ name, phone, note, items })
    return NextResponse.json({ ref: order.ref })
  } catch (e) {
    if (e instanceof OutOfStock) {
      return NextResponse.json({ error: e.message }, { status: 409 })
    }
    console.error('order failed', e)
    return NextResponse.json({ error: 'Could not place the order' }, { status: 500 })
  }
}
