import 'server-only'
import { Pool, types } from 'pg'

// pg hands NUMERIC back as a string to avoid float precision loss. Keep that —
// OMR has THREE decimal places (1 rial = 1000 baisa), so 0.1 + 0.2 style
// binary-float error is a real risk on a currency this granular. Money moves
// around this file as integer BAISA and is only formatted at the edge.
types.setTypeParser(types.builtins.NUMERIC, (v: string) => v)
types.setTypeParser(types.builtins.DATE, (v: string) => v)

const pool = new Pool({ connectionString: process.env.DATABASE_URL })

export type Product = {
  id: string
  slug: string
  name: string
  category: string
  description: string
  priceBaisa: number
  stock: number
  imageUrl: string | null
  active: boolean
}

export type OrderItem = {
  productId: string
  name: string
  qty: number
  unitBaisa: number
}

export type Order = {
  id: string
  ref: string
  name: string
  phone: string
  note: string | null
  status: OrderStatus
  totalBaisa: number
  createdAt: string
  items: OrderItem[]
}

export const ORDER_STATUSES = ['pending', 'paid', 'collected', 'cancelled'] as const
export type OrderStatus = (typeof ORDER_STATUSES)[number]

export const fmtOMR = (baisa: number) => (baisa / 1000).toFixed(3)

export async function initDB(): Promise<void> {
  await pool.query(`
    CREATE TABLE IF NOT EXISTS shop_products (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      slug TEXT UNIQUE NOT NULL,
      name TEXT NOT NULL,
      category TEXT NOT NULL DEFAULT 'Gear',
      description TEXT NOT NULL DEFAULT '',
      price_baisa INTEGER NOT NULL CHECK (price_baisa >= 0),
      stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
      image_url TEXT,
      active BOOLEAN NOT NULL DEFAULT true,
      created_at TIMESTAMPTZ DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS shop_orders (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      ref TEXT UNIQUE NOT NULL,
      name TEXT NOT NULL,
      phone TEXT NOT NULL,
      note TEXT,
      status TEXT NOT NULL DEFAULT 'pending',
      total_baisa INTEGER NOT NULL,
      created_at TIMESTAMPTZ DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS shop_order_items (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      order_id UUID NOT NULL REFERENCES shop_orders(id) ON DELETE CASCADE,
      product_id UUID REFERENCES shop_products(id) ON DELETE SET NULL,
      name TEXT NOT NULL,
      qty INTEGER NOT NULL CHECK (qty > 0),
      unit_baisa INTEGER NOT NULL
    );
    CREATE INDEX IF NOT EXISTS shop_order_items_order_idx ON shop_order_items(order_id);
  `)
}

const toProduct = (r: Record<string, unknown>): Product => ({
  id: String(r.id),
  slug: String(r.slug),
  name: String(r.name),
  category: String(r.category),
  description: String(r.description ?? ''),
  priceBaisa: Number(r.price_baisa),
  stock: Number(r.stock),
  imageUrl: (r.image_url as string) ?? null,
  active: Boolean(r.active),
})

export async function listProducts(includeInactive = false): Promise<Product[]> {
  const { rows } = await pool.query(
    `SELECT * FROM shop_products ${includeInactive ? '' : 'WHERE active'}
     ORDER BY category, name`,
  )
  return rows.map(toProduct)
}

export async function getProduct(slug: string): Promise<Product | null> {
  const { rows } = await pool.query('SELECT * FROM shop_products WHERE slug=$1', [slug])
  return rows[0] ? toProduct(rows[0]) : null
}

// Human-friendly and unambiguous when read aloud over the phone or written on
// a bag: no O/0, no I/1.
function makeRef(): string {
  const a = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
  let s = ''
  for (let i = 0; i < 5; i++) s += a[Math.floor(Math.random() * a.length)]
  return `UP-${s}`
}

export class OutOfStock extends Error {
  constructor(public readonly productName: string, public readonly available: number) {
    super(`${productName}: only ${available} left`)
  }
}

/**
 * Creates an order inside one transaction.
 *
 * Prices are re-read from the database and NEVER taken from the request — a
 * client that posts its own unit price could otherwise buy a racket for 1 baisa.
 * Stock is decremented with a conditional UPDATE so two people checking out the
 * last item at the same time cannot both succeed.
 */
export async function createOrder(input: {
  name: string
  phone: string
  note?: string
  items: { productId: string; qty: number }[]
}): Promise<Order> {
  const client = await pool.connect()
  try {
    await client.query('BEGIN')

    const lines: OrderItem[] = []
    let total = 0

    for (const { productId, qty } of input.items) {
      const { rows } = await client.query(
        'SELECT id, name, price_baisa, stock, active FROM shop_products WHERE id=$1 FOR UPDATE',
        [productId],
      )
      const p = rows[0]
      if (!p || !p.active) throw new Error('That item is no longer available')
      if (Number(p.stock) < qty) throw new OutOfStock(String(p.name), Number(p.stock))

      const upd = await client.query(
        'UPDATE shop_products SET stock = stock - $2 WHERE id=$1 AND stock >= $2 RETURNING stock',
        [productId, qty],
      )
      if (upd.rowCount === 0) throw new OutOfStock(String(p.name), Number(p.stock))

      const unit = Number(p.price_baisa)
      total += unit * qty
      lines.push({ productId, name: String(p.name), qty, unitBaisa: unit })
    }

    // Retry on the astronomically unlikely ref collision rather than 500ing.
    let ref = makeRef()
    for (let attempt = 0; attempt < 5; attempt++) {
      const { rows } = await client.query('SELECT 1 FROM shop_orders WHERE ref=$1', [ref])
      if (rows.length === 0) break
      ref = makeRef()
    }

    const { rows: orows } = await client.query(
      `INSERT INTO shop_orders (ref, name, phone, note, total_baisa)
       VALUES ($1,$2,$3,$4,$5) RETURNING id, created_at`,
      [ref, input.name, input.phone, input.note ?? null, total],
    )
    const orderId = String(orows[0].id)

    for (const l of lines) {
      await client.query(
        `INSERT INTO shop_order_items (order_id, product_id, name, qty, unit_baisa)
         VALUES ($1,$2,$3,$4,$5)`,
        [orderId, l.productId, l.name, l.qty, l.unitBaisa],
      )
    }

    await client.query('COMMIT')
    return {
      id: orderId,
      ref,
      name: input.name,
      phone: input.phone,
      note: input.note ?? null,
      status: 'pending',
      totalBaisa: total,
      createdAt: String(orows[0].created_at),
      items: lines,
    }
  } catch (e) {
    await client.query('ROLLBACK')
    throw e
  } finally {
    client.release()
  }
}

export async function getOrderByRef(ref: string): Promise<Order | null> {
  const { rows } = await pool.query('SELECT * FROM shop_orders WHERE ref=$1', [ref])
  if (!rows[0]) return null
  const o = rows[0]
  const { rows: items } = await pool.query(
    'SELECT product_id, name, qty, unit_baisa FROM shop_order_items WHERE order_id=$1',
    [o.id],
  )
  return {
    id: String(o.id),
    ref: String(o.ref),
    name: String(o.name),
    phone: String(o.phone),
    note: (o.note as string) ?? null,
    status: String(o.status) as OrderStatus,
    totalBaisa: Number(o.total_baisa),
    createdAt: String(o.created_at),
    items: items.map((i) => ({
      productId: String(i.product_id),
      name: String(i.name),
      qty: Number(i.qty),
      unitBaisa: Number(i.unit_baisa),
    })),
  }
}

export async function listOrders(): Promise<Order[]> {
  const { rows } = await pool.query('SELECT ref FROM shop_orders ORDER BY created_at DESC LIMIT 200')
  const out: Order[] = []
  for (const r of rows) {
    const o = await getOrderByRef(String(r.ref))
    if (o) out.push(o)
  }
  return out
}

/**
 * Cancelling returns the items to stock; every other transition just moves the
 * status. Guarded so a double-click cannot restock an order twice.
 */
export async function setOrderStatus(ref: string, status: OrderStatus): Promise<void> {
  const client = await pool.connect()
  try {
    await client.query('BEGIN')
    const { rows } = await client.query(
      'SELECT id, status FROM shop_orders WHERE ref=$1 FOR UPDATE',
      [ref],
    )
    if (!rows[0]) throw new Error('No such order')
    const prev = String(rows[0].status)
    if (prev === status) {
      await client.query('COMMIT')
      return
    }
    if (status === 'cancelled' && prev !== 'cancelled') {
      await client.query(
        `UPDATE shop_products p SET stock = p.stock + i.qty
         FROM shop_order_items i
         WHERE i.order_id = $1 AND i.product_id = p.id`,
        [rows[0].id],
      )
    }
    await client.query('UPDATE shop_orders SET status=$2 WHERE id=$1', [rows[0].id, status])
    await client.query('COMMIT')
  } catch (e) {
    await client.query('ROLLBACK')
    throw e
  } finally {
    client.release()
  }
}

export async function upsertProduct(p: {
  id?: string
  slug: string
  name: string
  category: string
  description: string
  priceBaisa: number
  stock: number
  imageUrl: string | null
  active: boolean
}): Promise<void> {
  if (p.id) {
    await pool.query(
      `UPDATE shop_products SET slug=$2,name=$3,category=$4,description=$5,
       price_baisa=$6,stock=$7,image_url=$8,active=$9 WHERE id=$1`,
      [p.id, p.slug, p.name, p.category, p.description, p.priceBaisa, p.stock, p.imageUrl, p.active],
    )
  } else {
    await pool.query(
      `INSERT INTO shop_products (slug,name,category,description,price_baisa,stock,image_url,active)
       VALUES ($1,$2,$3,$4,$5,$6,$7,$8)`,
      [p.slug, p.name, p.category, p.description, p.priceBaisa, p.stock, p.imageUrl, p.active],
    )
  }
}

export async function deleteProduct(id: string): Promise<void> {
  await pool.query('DELETE FROM shop_products WHERE id=$1', [id])
}
