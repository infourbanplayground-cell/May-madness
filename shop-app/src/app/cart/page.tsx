'use client'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useCallback, useEffect, useState } from 'react'
import { readCart, setQty, clearCart, onCartChange, type CartLine } from '@/lib/cart'

type Product = {
  id: string
  slug: string
  name: string
  priceBaisa: number
  stock: number
  imageUrl: string | null
}

const fmt = (b: number) => (b / 1000).toFixed(3)

export default function CartPage() {
  const router = useRouter()
  const [lines, setLines] = useState<CartLine[]>([])
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  const [note, setNote] = useState('')
  const [error, setError] = useState('')
  const [placing, setPlacing] = useState(false)

  const load = useCallback(async () => {
    const l = readCart()
    setLines(l)
    if (l.length === 0) {
      setProducts([])
      setLoading(false)
      return
    }
    const res = await fetch(`/api/products?ids=${l.map((x) => x.productId).join(',')}`)
    setProducts(res.ok ? await res.json() : [])
    setLoading(false)
  }, [])

  useEffect(() => {
    load()
    return onCartChange(load)
  }, [load])

  // A product can be deleted or deactivated while it sits in someone's cart,
  // so only lines we could actually resolve are shown or ordered.
  const rows = lines
    .map((l) => ({ line: l, product: products.find((p) => p.id === l.productId) }))
    .filter((r): r is { line: CartLine; product: Product } => !!r.product)

  const missing = lines.length - rows.length
  const total = rows.reduce((n, r) => n + r.product.priceBaisa * r.line.qty, 0)

  async function placeOrder(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setPlacing(true)
    try {
      const res = await fetch('/api/orders', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name,
          phone,
          note,
          items: rows.map((r) => ({ productId: r.product.id, qty: r.line.qty })),
        }),
      })
      const data = await res.json()
      if (!res.ok) {
        setError(data.error ?? 'Could not place the order')
        setPlacing(false)
        // Stock may have moved under us; refresh so the page tells the truth.
        load()
        return
      }
      clearCart()
      router.push(`/order/${data.ref}`)
    } catch {
      setError('Network problem — please try again')
      setPlacing(false)
    }
  }

  if (loading) return <p className="mono text-sm text-[var(--up-steel)]">LOADING…</p>

  if (rows.length === 0) {
    return (
      <div className="plate plate-br p-8">
        <h1 className="display text-3xl">YOUR CART IS EMPTY</h1>
        <Link href="/" className="btn inline-block px-6 py-3 mt-5">
          BROWSE THE SHOP
        </Link>
      </div>
    )
  }

  return (
    <div>
      <h1 className="display text-4xl mb-6">YOUR CART</h1>

      {missing > 0 && (
        <p className="mono text-xs tracking-[.12em] text-[var(--up-orange)] mb-4">
          {missing} ITEM{missing > 1 ? 'S' : ''} NO LONGER AVAILABLE — REMOVED
        </p>
      )}

      <div className="plate p-5">
        {rows.map(({ line, product }) => (
          <div
            key={product.id}
            className="flex items-center gap-4 py-4 border-b border-[var(--up-hair)] last:border-0"
          >
            <div className="flex-1 min-w-0">
              <Link href={`/product/${product.slug}`} className="display text-xl truncate block">
                {product.name}
              </Link>
              <span className="mono text-xs text-[var(--up-steel)]">
                {fmt(product.priceBaisa)} OMR each
              </span>
              {line.qty > product.stock && (
                <span className="block mono text-xs text-[var(--up-orange)] mt-1">
                  ONLY {product.stock} LEFT
                </span>
              )}
            </div>

            <div className="flex items-center gap-2">
              <button
                aria-label="Decrease quantity"
                className="btn-ghost w-9 h-9 leading-none"
                onClick={() => setQty(product.id, line.qty - 1)}
              >
                −
              </button>
              <span className="display text-lg w-8 text-center tabular-nums">{line.qty}</span>
              <button
                aria-label="Increase quantity"
                className="btn-ghost w-9 h-9 leading-none"
                disabled={line.qty >= product.stock}
                onClick={() => setQty(product.id, line.qty + 1)}
              >
                +
              </button>
            </div>

            <span className="display text-xl w-24 text-right tabular-nums">
              {fmt(product.priceBaisa * line.qty)}
            </span>
          </div>
        ))}

        <div className="flex items-baseline justify-between pt-5">
          <span className="mono text-xs tracking-[.2em] text-[var(--up-steel)]">TOTAL</span>
          <span className="display text-3xl tabular-nums">
            {fmt(total)}
            <span className="text-[var(--up-orange)] text-xl ml-2">OMR</span>
          </span>
        </div>
      </div>

      <form onSubmit={placeOrder} className="plate plate-br p-6 mt-6">
        <h2 className="display text-2xl">WHO IS COLLECTING?</h2>
        <p className="text-sm text-[var(--up-steel)] mt-2">
          We hold the order under your name. Nothing is charged now.
        </p>

        <div className="grid gap-4 sm:grid-cols-2 mt-5">
          <label className="block">
            <span className="mono text-[11px] tracking-[.18em] text-[var(--up-steel)]">NAME</span>
            <input
              required
              minLength={2}
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full mt-2 px-3 py-3"
            />
          </label>
          <label className="block">
            <span className="mono text-[11px] tracking-[.18em] text-[var(--up-steel)]">PHONE</span>
            <input
              required
              inputMode="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              className="w-full mt-2 px-3 py-3"
            />
          </label>
        </div>

        <label className="block mt-4">
          <span className="mono text-[11px] tracking-[.18em] text-[var(--up-steel)]">
            NOTE (OPTIONAL)
          </span>
          <textarea
            rows={2}
            value={note}
            onChange={(e) => setNote(e.target.value)}
            className="w-full mt-2 px-3 py-3"
            placeholder="Grip size, colour, when you'll collect…"
          />
        </label>

        {error && (
          <p role="alert" className="mt-4 text-[var(--up-orange)] font-semibold">
            {error}
          </p>
        )}

        <button type="submit" disabled={placing} className="btn px-8 py-4 mt-6 w-full sm:w-auto">
          {placing ? 'PLACING…' : 'RESERVE THIS ORDER'}
        </button>
      </form>
    </div>
  )
}
