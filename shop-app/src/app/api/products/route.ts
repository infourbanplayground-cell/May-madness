import { NextRequest, NextResponse } from 'next/server'
import { initDB, listProducts } from '@/lib/shop'

export const dynamic = 'force-dynamic'

// The cart holds ids only, so it needs to look names and prices back up.
// Returns active products; ?ids= filters to the ones in the cart.
export async function GET(req: NextRequest) {
  await initDB()
  const ids = req.nextUrl.searchParams.get('ids')
  const all = await listProducts()
  if (!ids) return NextResponse.json(all)
  const want = new Set(ids.split(',').filter(Boolean))
  return NextResponse.json(all.filter((p) => want.has(p.id)))
}
