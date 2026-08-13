'use client'
import { useEffect, useMemo, useRef, useState } from 'react'

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
  costBaisa: number | null
  size: string | null
}

const fmt = (b: number) => (b / 1000).toFixed(3)

const blank = {
  id: '', slug: '', name: '', category: 'Gear', description: '',
  price: '', stock: '0', imageUrl: '', active: true,
}
type FormState = typeof blank

/**
 * A 34-row catalogue made the old side-by-side form unusable: clicking Edit on
 * the last row sent you back to the top of the page to find the form. So the
 * editor is a modal, the list is a dense table, and the two fields that change
 * most (price, stock) are editable in the row without opening anything.
 */
export default function ProductsTab({
  products, reload,
}: { products: Product[]; reload: () => Promise<void> }) {
  const [q, setQ] = useState('')
  const [cat, setCat] = useState('')
  const [vis, setVis] = useState<'all' | 'live' | 'hidden'>('all')
  const [sel, setSel] = useState<Set<string>>(new Set())
  const [editing, setEditing] = useState<FormState | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const categories = useMemo(
    () => [...new Set(products.map((p) => p.category))].sort(), [products],
  )

  const shown = useMemo(() => {
    const needle = q.trim().toLowerCase()
    return products.filter((p) => {
      if (cat && p.category !== cat) return false
      if (vis === 'live' && !p.active) return false
      if (vis === 'hidden' && p.active) return false
      if (!needle) return true
      return `${p.name} ${p.category} ${p.size ?? ''}`.toLowerCase().includes(needle)
    })
  }, [products, q, cat, vis])

  // Selecting rows then filtering could otherwise act on invisible rows.
  const shownIds = useMemo(() => new Set(shown.map((p) => p.id)), [shown])
  const selected = useMemo(() => [...sel].filter((id) => shownIds.has(id)), [sel, shownIds])

  async function patch(ids: string[], body: Record<string, unknown>) {
    setError(''); setBusy(true)
    try {
      const res = await fetch('/api/admin/products', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ids, ...body }),
      })
      if (!res.ok) { setError((await res.json()).error ?? 'Could not save'); return false }
      await reload()
      return true
    } finally { setBusy(false) }
  }

  async function save(f: FormState) {
    setError('')
    const res = await fetch('/api/admin/products', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(f),
    })
    if (!res.ok) { setError((await res.json()).error ?? 'Could not save'); return }
    setEditing(null)
    await reload()
  }

  return (
    <div>
      {/* toolbar */}
      <div className="card p-4 mb-4 flex flex-wrap items-center gap-3"
        style={{ position: 'sticky', top: 72, zIndex: 30 }}>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search products…"
          className="px-3 py-2 flex-1 min-w-[180px]"
          aria-label="Search products"
        />
        <select value={cat} onChange={(e) => setCat(e.target.value)} className="px-3 py-2" aria-label="Category">
          <option value="">All categories</option>
          {categories.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
        <select
          value={vis}
          onChange={(e) => setVis(e.target.value as typeof vis)}
          className="px-3 py-2"
          aria-label="Visibility"
        >
          <option value="all">All</option>
          <option value="live">Live</option>
          <option value="hidden">Hidden</option>
        </select>
        <button className="btn px-5 py-2" onClick={() => setEditing({ ...blank })}>
          + New product
        </button>
      </div>

      {/* bulk bar — publishing 30 imported items one at a time is the pain
          this exists to remove */}
      {selected.length > 0 && (
        <div className="card p-3 mb-4 flex flex-wrap items-center gap-3"
          style={{ position: 'sticky', top: 150, zIndex: 29 }}>
          <span className="mono text-[11px] tracking-[.16em] text-[var(--up-orange)]">
            {selected.length} SELECTED
          </span>
          <button disabled={busy} className="btn-ghost px-4 py-2 text-sm"
            onClick={() => patch(selected, { active: true })}>Publish</button>
          <button disabled={busy} className="btn-ghost px-4 py-2 text-sm"
            onClick={() => patch(selected, { active: false })}>Hide</button>
          <button className="btn-ghost px-4 py-2 text-sm" onClick={() => setSel(new Set())}>
            Clear
          </button>
        </div>
      )}

      {error && <p className="text-[var(--up-orange)] font-semibold mb-3">{error}</p>}

      <div className="card" style={{ overflow: 'visible' }}>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left border-b border-[var(--up-hair)] [&>th]:sticky [&>th]:z-20 [&>th]:bg-[var(--up-panel)] mono text-[10px] tracking-[.14em] text-[var(--up-steel)]"
              style={{ }}>
              <th className="p-3 w-8" style={{ top: 150 }}>
                <input
                  type="checkbox"
                  aria-label="Select all shown"
                  checked={shown.length > 0 && selected.length === shown.length}
                  onChange={(e) =>
                    setSel(e.target.checked ? new Set(shown.map((p) => p.id)) : new Set())
                  }
                />
              </th>
              <th className="p-3" style={{ top: 150 }}>PRODUCT</th>
              <th className="p-3 w-28" style={{ top: 150 }}>PRICE</th>
              <th className="p-3 w-20" style={{ top: 150 }}>STOCK</th>
              <th className="p-3 w-24 hidden sm:table-cell" style={{ top: 150 }}>MARGIN</th>
              <th className="p-3 w-20" style={{ top: 150 }}>LIVE</th>
              <th className="p-3 w-24" style={{ top: 150 }}></th>
            </tr>
          </thead>
          <tbody>
            {shown.length === 0 && (
              <tr><td colSpan={7} className="p-8 text-center text-[var(--up-steel)]">
                Nothing matches that.
              </td></tr>
            )}
            {shown.map((p) => (
              <Row
                key={p.id}
                p={p}
                checked={sel.has(p.id)}
                onCheck={(on) => setSel((s) => {
                  const n = new Set(s); on ? n.add(p.id) : n.delete(p.id); return n
                })}
                onPatch={(body) => patch([p.id], body)}
                onEdit={() => setEditing({
                  id: p.id, slug: p.slug, name: p.name, category: p.category,
                  description: p.description, price: fmt(p.priceBaisa),
                  stock: String(p.stock), imageUrl: p.imageUrl ?? '', active: p.active,
                })}
                onDelete={async () => {
                  if (!confirm(`Delete ${p.name}? Past orders keep their line items.`)) return
                  await fetch(`/api/admin/products?id=${p.id}`, { method: 'DELETE' })
                  await reload()
                }}
              />
            ))}
          </tbody>
        </table>
      </div>

      <p className="mono text-[11px] tracking-[.14em] text-[var(--up-steel)] mt-3">
        SHOWING {shown.length} OF {products.length}
      </p>

      {editing && (
        <EditModal
          form={editing}
          onChange={setEditing}
          onClose={() => { setEditing(null); setError('') }}
          onSave={save}
          error={error}
        />
      )}
    </div>
  )
}

function Row({
  p, checked, onCheck, onPatch, onEdit, onDelete,
}: {
  p: Product
  checked: boolean
  onCheck: (on: boolean) => void
  onPatch: (body: Record<string, unknown>) => Promise<boolean | undefined>
  onEdit: () => void
  onDelete: () => void
}) {
  // Inline fields keep their own draft so typing is not fought by a reload,
  // and only commit on blur or Enter.
  const [price, setPrice] = useState(fmt(p.priceBaisa))
  const [stock, setStock] = useState(String(p.stock))
  useEffect(() => { setPrice(fmt(p.priceBaisa)) }, [p.priceBaisa])
  useEffect(() => { setStock(String(p.stock)) }, [p.stock])

  const margin = p.costBaisa != null && p.priceBaisa > 0
    ? Math.round(((p.priceBaisa - p.costBaisa) / p.priceBaisa) * 100) : null

  return (
    <tr className="border-b border-[var(--up-hair)] last:border-0 hover:bg-[var(--up-panel-hi)]">
      <td className="p-3">
        <input type="checkbox" checked={checked} aria-label={`Select ${p.name}`}
          onChange={(e) => onCheck(e.target.checked)} />
      </td>
      <td className="p-3">
        <div className="flex items-center gap-3">
          {p.imageUrl
            // eslint-disable-next-line @next/next/no-img-element
            ? <img src={p.imageUrl} alt="" className="w-10 h-10 object-cover shrink-0" />
            : <div className="w-10 h-10 bg-black/40 shrink-0" />}
          <div className="min-w-0">
            <div className="truncate">{p.name}</div>
            <div className="mono text-[10px] text-[var(--up-steel)]">
              {p.category}{p.costBaisa != null && ` · cost ${fmt(p.costBaisa)}`}
            </div>
          </div>
        </div>
      </td>
      <td className="p-3">
        <input
          value={price} inputMode="decimal" aria-label={`Price for ${p.name}`}
          className="w-24 px-2 py-1 text-sm"
          onChange={(e) => setPrice(e.target.value)}
          onBlur={() => price !== fmt(p.priceBaisa) && onPatch({ price })}
          onKeyDown={(e) => e.key === 'Enter' && (e.target as HTMLInputElement).blur()}
        />
      </td>
      <td className="p-3">
        <input
          value={stock} inputMode="numeric" aria-label={`Stock for ${p.name}`}
          className="w-16 px-2 py-1 text-sm"
          onChange={(e) => setStock(e.target.value)}
          onBlur={() => stock !== String(p.stock) && onPatch({ stock })}
          onKeyDown={(e) => e.key === 'Enter' && (e.target as HTMLInputElement).blur()}
        />
      </td>
      <td className="p-3 hidden sm:table-cell mono text-xs">
        {margin == null ? <span className="text-[var(--up-steel)]">—</span>
          : <span className={margin < 20 ? 'text-[var(--up-orange)]' : ''}>{margin}%</span>}
      </td>
      <td className="p-3">
        <button
          onClick={() => onPatch({ active: !p.active })}
          aria-pressed={p.active}
          className={`px-3 py-1 mono text-[10px] tracking-[.12em] ${p.active ? 'btn' : 'btn-ghost'}`}
        >
          {p.active ? 'LIVE' : 'HIDDEN'}
        </button>
      </td>
      <td className="p-3 text-right whitespace-nowrap">
        <button className="btn-ghost px-3 py-1 text-xs" onClick={onEdit}>Edit</button>
        <button className="btn-ghost px-2 py-1 text-xs ml-1" onClick={onDelete} aria-label={`Delete ${p.name}`}>×</button>
      </td>
    </tr>
  )
}

function EditModal({
  form, onChange, onClose, onSave, error,
}: {
  form: FormState
  onChange: (f: FormState) => void
  onClose: () => void
  onSave: (f: FormState) => void
  error: string
}) {
  const first = useRef<HTMLInputElement>(null)
  const [uploading, setUploading] = useState(false)

  useEffect(() => {
    first.current?.focus()
    const esc = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', esc)
    // Stop the page behind the dialog scrolling under it.
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      window.removeEventListener('keydown', esc)
      document.body.style.overflow = prev
    }
  }, [onClose])

  return (
    <div
      className="fixed inset-0 z-50 flex items-start sm:items-center justify-center p-4 overflow-y-auto"
      style={{ background: 'rgba(6,7,11,.72)' }}
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <form
        role="dialog" aria-modal="true" aria-label={form.id ? 'Edit product' : 'New product'}
        onSubmit={(e) => { e.preventDefault(); onSave(form) }}
        className="card p-6 w-full max-w-lg my-8"
      >
        <h2 className="display text-2xl">{form.id ? 'Edit product' : 'New product'}</h2>

        <F label="NAME">
          <input ref={first} required value={form.name}
            onChange={(e) => onChange({ ...form, name: e.target.value })}
            className="w-full px-3 py-2" />
        </F>
        <div className="grid grid-cols-2 gap-3">
          <F label="CATEGORY">
            <input value={form.category}
              onChange={(e) => onChange({ ...form, category: e.target.value })}
              className="w-full px-3 py-2" />
          </F>
          <F label="PRICE (OMR)">
            <input required inputMode="decimal" value={form.price}
              onChange={(e) => onChange({ ...form, price: e.target.value })}
              placeholder="12.500" className="w-full px-3 py-2" />
          </F>
        </div>
        <F label="STOCK">
          <input required inputMode="numeric" value={form.stock}
            onChange={(e) => onChange({ ...form, stock: e.target.value })}
            className="w-full px-3 py-2" />
        </F>
        <F label="PHOTO">
          <div className="flex items-start gap-3">
            {form.imageUrl && (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={form.imageUrl} alt="" className="w-16 h-16 object-cover shrink-0" />
            )}
            <div className="flex-1 min-w-0">
              <input type="file" accept="image/jpeg,image/png,image/webp"
                className="w-full px-3 py-2 text-sm"
                onChange={async (e) => {
                  const f = e.target.files?.[0]; e.target.value = ''
                  if (!f) return
                  setUploading(true)
                  const fd = new FormData(); fd.append('file', f)
                  const res = await fetch('/api/admin/upload', { method: 'POST', body: fd })
                  const d = await res.json()
                  setUploading(false)
                  if (res.ok) onChange({ ...form, imageUrl: d.url })
                }} />
              <input value={form.imageUrl}
                onChange={(e) => onChange({ ...form, imageUrl: e.target.value })}
                placeholder="/uploads/… or https://…" className="w-full px-3 py-2 mt-2 text-sm" />
              {uploading && (
                <p className="mono text-[10px] text-[var(--up-steel)] mt-1">UPLOADING…</p>
              )}
            </div>
          </div>
        </F>
        <F label="DESCRIPTION">
          <textarea rows={3} value={form.description}
            onChange={(e) => onChange({ ...form, description: e.target.value })}
            className="w-full px-3 py-2" />
        </F>

        <label className="flex items-center gap-3 mt-4 cursor-pointer">
          <input type="checkbox" checked={form.active}
            onChange={(e) => onChange({ ...form, active: e.target.checked })} />
          <span className="mono text-[11px] tracking-[.16em] text-[var(--up-steel)]">
            VISIBLE IN THE SHOP
          </span>
        </label>

        {error && <p className="text-[var(--up-orange)] mt-3 font-semibold">{error}</p>}

        <div className="flex gap-3 mt-6">
          <button className="btn px-6 py-3 flex-1">
            {form.id ? 'Save changes' : 'Add product'}
          </button>
          <button type="button" className="btn-ghost px-5 py-3" onClick={onClose}>Cancel</button>
        </div>
      </form>
    </div>
  )
}

function F({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block mt-4">
      <span className="mono text-[11px] tracking-[.16em] text-[var(--up-steel)]">{label}</span>
      <div className="mt-2">{children}</div>
    </label>
  )
}
