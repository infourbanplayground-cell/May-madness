'use client'
import { useCallback, useEffect, useState } from 'react'
import ProductsTab, { type Product } from '@/components/ProductsTab'

type OrderItem = { name: string; qty: number; unitBaisa: number }
type Order = {
  ref: string
  name: string
  phone: string
  note: string | null
  status: string
  totalBaisa: number
  createdAt: string
  items: OrderItem[]
}

const fmt = (b: number) => (b / 1000).toFixed(3)

export default function Admin() {
  const [authed, setAuthed] = useState<boolean | null>(null)
  const [password, setPassword] = useState('')
  const [loginError, setLoginError] = useState('')
  const [tab, setTab] = useState<'orders' | 'stock' | 'products' | 'photos'>('orders')
  const [busy, setBusy] = useState<string | null>(null)
  const [products, setProducts] = useState<Product[]>([])
  const [orders, setOrders] = useState<Order[]>([])
  const [error, setError] = useState('')

  const pendingCount = orders.filter((o) => o.status === 'pending').length
  const lowStockCount = products.filter((p) => p.active && p.stock > 0 && p.stock <= 2).length
  const noPhotoCount = products.filter((p) => p.active && !p.imageUrl).length

  const load = useCallback(async () => {
    const [p, o] = await Promise.all([
      fetch('/api/admin/products'),
      fetch('/api/admin/orders'),
    ])
    if (p.status === 401 || o.status === 401) {
      setAuthed(false)
      return
    }
    setProducts(await p.json())
    setOrders(await o.json())
    setAuthed(true)
  }, [])

  useEffect(() => { load() }, [load])

  async function login(e: React.FormEvent) {
    e.preventDefault()
    setLoginError('')
    const res = await fetch('/api/admin/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password }),
    })
    if (!res.ok) {
      setLoginError('Wrong password')
      return
    }
    setPassword('')
    load()
  }

  async function setStatus(ref: string, status: string) {
    await fetch('/api/admin/orders', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ref, status }),
    })
    load()
  }

  async function bumpStock(id: string, next: number) {
    if (next < 0) return
    setBusy(id)
    try {
      await fetch('/api/admin/products', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ids: [id], stock: next }),
      })
      await load()
    } finally {
      setBusy(null)
    }
  }

  if (authed === null) return <p className="mono text-sm text-[var(--up-steel)]">LOADING…</p>

  if (!authed) {
    return (
      <form onSubmit={login} className="card p-7 max-w-md">
        <h1 className="display text-3xl">Shop admin</h1>
        <input
          type="password"
          autoFocus
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          className="w-full mt-5 px-3 py-3"
        />
        {loginError && <p className="text-[var(--up-orange)] mt-3 font-semibold">{loginError}</p>}
        <button className="btn px-6 py-3 mt-5 w-full">Sign in</button>
      </form>
    )
  }

  return (
    <div>
      <div className="flex items-center gap-3 mb-7">
        <h1 className="display text-4xl flex-1">Shop admin</h1>
        <button
          className="btn-ghost px-4 py-2 mono text-[11px] tracking-[.16em]"
          onClick={async () => {
            await fetch('/api/admin/login', { method: 'DELETE' })
            setAuthed(false)
          }}
        >
          SIGN OUT
        </button>
      </div>

      {(pendingCount > 0 || lowStockCount > 0 || noPhotoCount > 0) && (
        <div className="card p-4 mb-6 border border-[rgba(245,101,48,.35)] bg-[rgba(245,101,48,.08)]">
          <div className="mono text-[10px] tracking-[.18em] text-[var(--up-orange-soft)]">
            NEEDS YOU NOW
          </div>
          <div className="flex flex-wrap gap-6 mt-2.5">
            <button onClick={() => setTab('orders')} className="text-left">
              <div className="display text-2xl">{pendingCount}</div>
              <div className="mono text-[9px] tracking-[.14em] text-[#c3cad6]">PENDING</div>
            </button>
            <button onClick={() => setTab('stock')} className="text-left">
              <div className="display text-2xl">{lowStockCount}</div>
              <div className="mono text-[9px] tracking-[.14em] text-[#c3cad6]">LOW STOCK</div>
            </button>
            <button onClick={() => setTab('photos')} className="text-left">
              <div className="display text-2xl">{noPhotoCount}</div>
              <div className="mono text-[9px] tracking-[.14em] text-[#c3cad6]">NO PHOTO</div>
            </button>
          </div>
        </div>
      )}

      <div className="flex gap-3 mb-6 flex-wrap">
        {(['orders', 'stock', 'products', 'photos'] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-5 py-2 mono text-[11px] tracking-[.18em] ${
              tab === t ? 'btn' : 'btn-ghost'
            }`}
          >
            {t === 'stock' ? 'LOW STOCK' : t.toUpperCase()}
            {t === 'orders' && <span className="ml-2">{pendingCount}</span>}
            {t === 'stock' && <span className="ml-2">{lowStockCount}</span>}
            {t === 'photos' && <span className="ml-2">{noPhotoCount}</span>}
          </button>
        ))}
      </div>

      {tab === 'orders' && (
        <div className="space-y-3">
          {orders.length === 0 && <p className="text-[var(--up-steel)]">No orders yet.</p>}
          {orders.map((o) => (
            <div key={o.ref} className="card p-5">
              <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1">
                <span className="display text-2xl">{o.ref}</span>
                <span className="mono text-[11px] tracking-[.16em] text-[var(--up-orange)]">
                  {o.status.toUpperCase()}
                </span>
                <span className="flex-1" />
                <span className="display text-2xl tabular-nums">{fmt(o.totalBaisa)} OMR</span>
              </div>

              <p className="mt-2 text-[#c3cad6]">
                {o.name} · <a className="underline" href={`tel:${o.phone}`}>{o.phone}</a>
              </p>
              {o.note && <p className="mt-1 text-sm text-[var(--up-steel)]">“{o.note}”</p>}

              <ul className="mt-3 text-sm text-[#c3cad6]">
                {o.items.map((i, n) => (
                  <li key={n}>
                    {i.qty} × {i.name}{' '}
                    <span className="mono text-[var(--up-steel)]">{fmt(i.unitBaisa)}</span>
                  </li>
                ))}
              </ul>

              <div className="flex flex-wrap gap-2 mt-4">
                {['pending', 'paid', 'collected', 'cancelled'].map((s) => (
                  <button
                    key={s}
                    disabled={o.status === s}
                    onClick={() => setStatus(o.ref, s)}
                    className={`px-3 py-2 mono text-[10px] tracking-[.14em] ${
                      o.status === s ? 'btn' : 'btn-ghost'
                    }`}
                  >
                    {s.toUpperCase()}
                  </button>
                ))}
              </div>
              {o.status !== 'cancelled' && (
                <p className="mono text-[10px] text-[var(--up-steel)] mt-2">
                  CANCELLING RETURNS THESE ITEMS TO STOCK
                </p>
              )}
            </div>
          ))}
        </div>
      )}

      {tab === 'stock' && (
        <div>
          <p className="text-sm text-[var(--up-steel)] mb-4">
            Lowest stock first. Change a number here and it saves — no need to open the product.
          </p>
          <div className="space-y-2">
            {[...products]
              .filter((p) => p.active)
              .sort((a, b) => a.stock - b.stock)
              .map((p) => (
                <div key={p.id} className="card flex items-center gap-3 p-3">
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-bold truncate">{p.name}</div>
                    <div className="mono text-[10px] tracking-[.14em] text-[var(--up-steel)] mt-1">
                      {p.category}{p.size ? ` · EU ${p.size}` : ''}
                    </div>
                  </div>
                  <button
                    aria-label={`Decrease stock for ${p.name}`}
                    disabled={busy === p.id || p.stock <= 0}
                    className="btn-ghost w-8 h-8 leading-none flex-none"
                    onClick={() => bumpStock(p.id, p.stock - 1)}
                  >
                    −
                  </button>
                  <span
                    className={`display text-lg w-7 text-center tabular-nums flex-none ${
                      p.stock <= 1 ? 'text-[var(--up-orange)]' : ''
                    }`}
                  >
                    {p.stock}
                  </span>
                  <button
                    aria-label={`Increase stock for ${p.name}`}
                    disabled={busy === p.id}
                    className="btn-ghost w-8 h-8 leading-none flex-none"
                    onClick={() => bumpStock(p.id, p.stock + 1)}
                  >
                    +
                  </button>
                </div>
              ))}
          </div>
        </div>
      )}

      {tab === 'photos' && (
        <div>
          <div className="card p-5 mb-5">
            <h2 className="display text-xl">Add photos</h2>
            <p className="text-sm text-[var(--up-steel)] mt-2 leading-relaxed">
              Click any tile to attach a photo — it uploads and saves straight
              away, no need to open the product. Save the images from your
              supplier&apos;s site first, or shoot the item on your phone.
            </p>
            <p className="mono text-[11px] tracking-[.14em] text-[var(--up-orange)] mt-3">
              {products.filter((p) => !p.imageUrl).length} OF {products.length} STILL WITHOUT A PHOTO
            </p>
          </div>

          <div className="grid gap-4 grid-cols-2 sm:grid-cols-3 lg:grid-cols-4">
            {[...products]
              .sort((a, b) => Number(!!a.imageUrl) - Number(!!b.imageUrl))
              .map((p) => (
                <label
                  key={p.id}
                  className={`card p-3 cursor-pointer block ${busy === p.id ? 'opacity-50' : ''}`}
                >
                  <div className="w-full h-28 bg-[#0f1015] flex items-center justify-center overflow-hidden">
                    {p.imageUrl ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img src={p.imageUrl} alt="" className="w-full h-full object-cover" />
                    ) : (
                      <span className="mono text-[10px] tracking-[.14em] text-[var(--up-steel)]">
                        {busy === p.id ? 'UPLOADING…' : '+ ADD PHOTO'}
                      </span>
                    )}
                  </div>
                  <p className="text-xs mt-2 leading-tight line-clamp-2">{p.name}</p>
                  <input
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    className="hidden"
                    onChange={async (e) => {
                      const file = e.target.files?.[0]
                      e.target.value = ''
                      if (!file) return
                      setError(''); setBusy(p.id)
                      try {
                        const fd = new FormData(); fd.append('file', file)
                        const up = await fetch('/api/admin/upload', { method: 'POST', body: fd })
                        const upData = await up.json()
                        if (!up.ok) { setError(upData.error ?? 'Upload failed'); return }
                        // Send the whole product back, or the save would blank
                        // the fields this form is not showing.
                        const save = await fetch('/api/admin/products', {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({
                            id: p.id, slug: p.slug, name: p.name, category: p.category,
                            description: p.description, price: fmt(p.priceBaisa),
                            stock: p.stock, imageUrl: upData.url, active: p.active,
                          }),
                        })
                        if (!save.ok) {
                          const d = await save.json()
                          setError(d.error ?? 'Could not attach the photo'); return
                        }
                        await load()
                      } finally { setBusy(null) }
                    }}
                  />
                </label>
              ))}
          </div>
          {error && <p className="text-[var(--up-orange)] mt-4 font-semibold">{error}</p>}
        </div>
      )}

      {tab === 'products' && (
        <ProductsTab products={products} reload={load} />
      )}

    </div>
  )
}

function Stat({ k, v }: { k: string; v: string }) {
  return (
    <div>
      <div className="mono text-[10px] tracking-[.18em] text-[var(--up-steel)]">{k}</div>
      <div className="display text-xl tabular-nums">{v}</div>
    </div>
  )
}

