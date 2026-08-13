import { NextRequest, NextResponse } from 'next/server'
import { isAdmin } from '@/lib/adminAuth'
import { deleteProduct, initDB, listProducts, upsertProduct } from '@/lib/shop'

export const dynamic = 'force-dynamic'

const slugify = (s: string) =>
  s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 60)

export async function GET() {
  if (!(await isAdmin())) return NextResponse.json({ error: 'Unauthorised' }, { status: 401 })
  await initDB()
  return NextResponse.json(await listProducts(true))
}

export async function POST(req: NextRequest) {
  if (!(await isAdmin())) return NextResponse.json({ error: 'Unauthorised' }, { status: 401 })
  await initDB()

  const b = (await req.json().catch(() => ({}))) as Record<string, unknown>
  const name = typeof b.name === 'string' ? b.name.trim() : ''
  if (!name) return NextResponse.json({ error: 'Name is required' }, { status: 400 })

  // Prices arrive as OMR (e.g. "12.500") and are stored as integer baisa —
  // rounding once, here, rather than carrying a float through the system.
  const priceOmr = Number(b.price)
  if (!Number.isFinite(priceOmr) || priceOmr < 0) {
    return NextResponse.json({ error: 'Price must be a number' }, { status: 400 })
  }
  const priceBaisa = Math.round(priceOmr * 1000)

  const stock = Math.floor(Number(b.stock))
  if (!Number.isFinite(stock) || stock < 0) {
    return NextResponse.json({ error: 'Stock must be zero or more' }, { status: 400 })
  }

  const slug = typeof b.slug === 'string' && b.slug.trim() ? slugify(b.slug) : slugify(name)
  if (!slug) return NextResponse.json({ error: 'Could not build a URL for that name' }, { status: 400 })

  try {
    await upsertProduct({
      id: typeof b.id === 'string' && b.id ? b.id : undefined,
      slug,
      name,
      category: typeof b.category === 'string' && b.category.trim() ? b.category.trim() : 'Gear',
      description: typeof b.description === 'string' ? b.description.trim() : '',
      priceBaisa,
      stock,
      imageUrl: typeof b.imageUrl === 'string' && b.imageUrl.trim() ? b.imageUrl.trim() : null,
      active: b.active !== false,
    })
  } catch (e) {
    const msg = e instanceof Error && /unique/i.test(e.message)
      ? 'Another product already uses that URL'
      : 'Could not save the product'
    return NextResponse.json({ error: msg }, { status: 400 })
  }
  return NextResponse.json({ ok: true })
}

export async function DELETE(req: NextRequest) {
  if (!(await isAdmin())) return NextResponse.json({ error: 'Unauthorised' }, { status: 401 })
  const id = req.nextUrl.searchParams.get('id')
  if (!id) return NextResponse.json({ error: 'Missing id' }, { status: 400 })
  await deleteProduct(id)
  return NextResponse.json({ ok: true })
}
