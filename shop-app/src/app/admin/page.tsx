'use client'
import { useCallback, useEffect, useState } from 'react'

type Product = {
  id: string
  slug: string
  name: string
  category: string
  description: string
  priceBaisa: number
  stock: number
  imageUrl: string | null
  active: boolean
  costBaisa: number | null
  size: string | null
}
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
const blank = {
  id: '', slug: '', name: '', category: 'Gear', description: '',
  price: '', stock: '0', imageUrl: '', active: true,
}

export default function Admin() {
  const [authed, setAuthed] = useState<boolean | null>(null)
  const [password, setPassword] = useState('')
  const [loginError, setLoginError] = useState('')
  const [tab, setTab] = useState<'orders' | 'products'>('orders')
  const [products, setProducts] = useState<Product[]>([])
  const [orders, setOrders] = useState<Order[]>([])
  const [form, setForm] = useState({ ...blank })
  const [error, setError] = useState('')
  const [uploading, setUploading] = useState(false)

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

  async function saveProduct(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    const res = await fetch('/api/admin/products', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form),
    })
    const data = await res.json()
    if (!res.ok) { setError(data.error ?? 'Could not save'); return }
    setForm({ ...blank })
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

      <div className="flex gap-3 mb-6">
        {(['orders', 'products'] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-5 py-2 mono text-[11px] tracking-[.18em] ${
              tab === t ? 'btn' : 'btn-ghost'
            }`}
          >
            {t.toUpperCase()}
            {t === 'orders' && (
              <span className="ml-2">
                {orders.filter((o) => o.status === 'pending').length}
              </span>
            )}
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

      {tab === 'products' && (
        <div className="grid gap-6 lg:grid-cols-2">
          <form onSubmit={saveProduct} className="card p-6 h-fit">
            <h2 className="display text-2xl">{form.id ? 'EDIT PRODUCT' : 'NEW PRODUCT'}</h2>

            <Field label="NAME">
              <input required value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="w-full px-3 py-2" />
            </Field>
            <Field label="CATEGORY">
              <input value={form.category}
                onChange={(e) => setForm({ ...form, category: e.target.value })}
                className="w-full px-3 py-2" />
            </Field>
            <div className="grid grid-cols-2 gap-3">
              <Field label="PRICE (OMR)">
                <input required inputMode="decimal" value={form.price}
                  onChange={(e) => setForm({ ...form, price: e.target.value })}
                  placeholder="12.500" className="w-full px-3 py-2" />
              </Field>
              <Field label="STOCK">
                <input required inputMode="numeric" value={form.stock}
                  onChange={(e) => setForm({ ...form, stock: e.target.value })}
                  className="w-full px-3 py-2" />
              </Field>
            </div>
            <Field label="PHOTO">
              <div className="flex items-start gap-3">
                {form.imageUrl && (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={form.imageUrl} alt="" className="w-20 h-20 object-cover shrink-0" />
                )}
                <div className="flex-1 min-w-0">
                  <input
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    className="w-full px-3 py-2 text-sm"
                    onChange={async (e) => {
                      const f = e.target.files?.[0]
                      if (!f) return
                      setError(''); setUploading(true)
                      const fd = new FormData(); fd.append('file', f)
                      const res = await fetch('/api/admin/upload', { method: 'POST', body: fd })
                      const data = await res.json()
                      setUploading(false)
                      // Reset so re-picking the same file still fires onChange.
                      e.target.value = ''
                      if (!res.ok) { setError(data.error ?? 'Upload failed'); return }
                      setForm((f0) => ({ ...f0, imageUrl: data.url }))
                    }}
                  />
                  <p className="mono text-[10px] text-[var(--up-steel)] mt-1">
                    {uploading ? 'UPLOADING…' : 'JPEG, PNG OR WEBP · UP TO 6MB · OR PASTE A URL BELOW'}
                  </p>
                  <input value={form.imageUrl}
                    onChange={(e) => setForm({ ...form, imageUrl: e.target.value })}
                    placeholder="/uploads/… or https://…" className="w-full px-3 py-2 mt-2 text-sm" />
                </div>
              </div>
            </Field>
            <Field label="DESCRIPTION">
              <textarea rows={3} value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                className="w-full px-3 py-2" />
            </Field>

            <label className="flex items-center gap-3 mt-4 cursor-pointer">
              <input type="checkbox" checked={form.active}
                onChange={(e) => setForm({ ...form, active: e.target.checked })} />
              <span className="mono text-[11px] tracking-[.16em] text-[var(--up-steel)]">
                VISIBLE IN THE SHOP
              </span>
            </label>

            {error && <p className="text-[var(--up-orange)] mt-3 font-semibold">{error}</p>}

            <div className="flex gap-3 mt-5">
              <button className="btn px-6 py-3 flex-1">
                {form.id ? 'SAVE CHANGES' : 'ADD PRODUCT'}
              </button>
              {form.id && (
                <button type="button" className="btn-ghost px-5 py-3"
                  onClick={() => { setForm({ ...blank }); setError('') }}>
                  CANCEL
                </button>
              )}
            </div>
          </form>

          <div className="space-y-3">
            {products.some((p) => p.costBaisa != null) && (() => {
              const withCost = products.filter((p) => p.costBaisa != null)
              const cost = withCost.reduce((n, p) => n + (p.costBaisa ?? 0) * p.stock, 0)
              const retail = withCost.reduce((n, p) => n + p.priceBaisa * p.stock, 0)
              const units = withCost.reduce((n, p) => n + p.stock, 0)
              return (
                <div className="card p-4 flex flex-wrap gap-x-8 gap-y-2">
                  <Stat k="UNITS" v={String(units)} />
                  <Stat k="COST" v={fmt(cost)} />
                  <Stat k="RETAIL" v={fmt(retail)} />
                  <Stat
                    k="MARGIN"
                    v={`${fmt(retail - cost)}  (${retail ? (((retail - cost) / retail) * 100).toFixed(1) : '0'}%)`}
                  />
                </div>
              )
            })()}
            {products.map((p) => (
              <div key={p.id} className="card p-4 flex items-center gap-4">
                <div className="flex-1 min-w-0">
                  <p className="display text-xl truncate">
                    {p.name}
                    {!p.active && (
                      <span className="mono text-[10px] text-[var(--up-steel)] ml-2">HIDDEN</span>
                    )}
                  </p>
                  <p className="mono text-xs text-[var(--up-steel)]">
                    {fmt(p.priceBaisa)} OMR · {p.stock} in stock · {p.category}
                  </p>
                  {p.costBaisa != null && (
                    <p className="mono text-xs text-[var(--up-steel)] mt-0.5">
                      cost {fmt(p.costBaisa)} ·{' '}
                      <span className="text-[var(--up-orange)]">
                        {p.priceBaisa
                          ? `${(((p.priceBaisa - p.costBaisa) / p.priceBaisa) * 100).toFixed(0)}% margin`
                          : 'no price set'}
                      </span>
                    </p>
                  )}
                </div>
                <button className="btn-ghost px-3 py-2 mono text-[10px] tracking-[.14em]"
                  onClick={() => setForm({
                    id: p.id, slug: p.slug, name: p.name, category: p.category,
                    description: p.description, price: fmt(p.priceBaisa),
                    stock: String(p.stock), imageUrl: p.imageUrl ?? '', active: p.active,
                  })}>
                  EDIT
                </button>
                <button className="btn-ghost px-3 py-2 mono text-[10px] tracking-[.14em]"
                  onClick={async () => {
                    if (!confirm(`Delete ${p.name}? Past orders keep their line items.`)) return
                    await fetch(`/api/admin/products?id=${p.id}`, { method: 'DELETE' })
                    load()
                  }}>
                  DELETE
                </button>
              </div>
            ))}
          </div>
        </div>
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

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block mt-4">
      <span className="mono text-[11px] tracking-[.16em] text-[var(--up-steel)]">{label}</span>
      <div className="mt-2">{children}</div>
    </label>
  )
}
