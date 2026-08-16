'use client'
import Link from 'next/link'
import { useMemo, useState } from 'react'
import { groupProducts, type GroupableProduct } from '@/lib/group'

const fmt = (b: number) => (b / 1000).toFixed(3)

export default function ShopBrowser({ products }: { products: GroupableProduct[] }) {
  const [cat, setCat] = useState('all')

  const groups = useMemo(() => groupProducts(products), [products])
  const categories = useMemo(
    () => [...new Set(groups.map((g) => g.category))].sort(),
    [groups],
  )
  const shown = useMemo(
    () => groups.filter((g) => cat === 'all' || g.category === cat).sort((a, b) => a.name.localeCompare(b.name)),
    [groups, cat],
  )

  if (groups.length === 0) {
    return (
      <div className="card p-10 text-center">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/up-logo.png" alt="" className="h-24 w-auto mx-auto opacity-40" />
        <p className="display text-2xl mt-6">The shelves are being stocked</p>
        <p className="mt-3 text-[var(--up-steel)] max-w-md mx-auto">
          Nothing is listed just yet. Come back shortly, or ask at the desk —
          we can usually find what you need.
        </p>
      </div>
    )
  }

  return (
    <div>
      <div
        className="sticky z-20 -mx-5 px-5 py-3 bg-[rgba(22,23,29,.96)] backdrop-blur border-b border-[var(--up-hair)] flex gap-2 overflow-x-auto"
        style={{ top: 72 }}
      >
        {['all', ...categories].map((c) => (
          <button
            key={c}
            onClick={() => setCat(c)}
            className={`shrink-0 px-4 py-2 rounded-full mono text-[10px] tracking-[.16em] whitespace-nowrap ${
              cat === c ? 'btn' : 'btn-ghost'
            }`}
          >
            {c === 'all' ? 'ALL' : c.toUpperCase()}
          </button>
        ))}
      </div>

      <div className="flex items-baseline justify-between mt-5 mb-3">
        <span className="mono text-[11px] tracking-[.18em] text-[var(--up-steel)]">
          {shown.length ? `${shown.length} PRODUCT${shown.length > 1 ? 'S' : ''}` : 'NOTHING IN STOCK'}
        </span>
      </div>

      {shown.length === 0 ? (
        <div className="card p-9 text-center border-dashed">
          <p className="display text-xl">NOTHING HERE YET</p>
          <p className="mt-2 text-sm text-[var(--up-steel)]">
            We restock this shelf most weeks. Ask at the desk and we&apos;ll order it in.
          </p>
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {shown.map((g) => {
            const rep = g.variants.find((v) => v.stock > 0) ?? g.variants[0]
            const sub =
              g.variants.length > 1
                ? `${g.variants.length} sizes · ${g.variants.map((v) => v.size).join(', ')}`
                : rep.size
                  ? `EU ${rep.size}`
                  : 'One size'
            const low = g.totalStock > 0 && g.totalStock <= 2
            const soldOut = g.totalStock === 0

            return (
              <Link key={g.key} href={`/product/${rep.slug}`} className="card flex gap-3 p-3">
                <div className="w-[78px] h-[78px] shrink-0 rounded-[8px] bg-[#0f1015] flex items-center justify-center overflow-hidden">
                  {g.imageUrl ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={g.imageUrl} alt="" className="w-full h-full object-cover" />
                  ) : (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src="/up-logo.png" alt="" className="h-8 w-auto opacity-25" />
                  )}
                </div>
                <div className="flex-1 min-w-0 flex flex-col gap-1">
                  <div className="mono text-[9px] tracking-[.18em] text-[var(--up-steel)]">
                    {g.category.toUpperCase()}
                  </div>
                  <div className="text-[14.5px] font-bold leading-tight">{g.name}</div>
                  <div className="text-[11.5px] text-[var(--up-steel)] leading-tight">{sub}</div>
                  <div className="flex items-baseline gap-2 mt-0.5">
                    <span className="display text-xl tabular-nums">{fmt(g.priceBaisa)}</span>
                    <span className="mono text-[9px] tracking-[.14em] text-[var(--up-steel)]">OMR</span>
                    <span
                      className={`mono text-[8px] tracking-[.12em] px-1.5 py-0.5 rounded-full ${
                        soldOut || low
                          ? 'bg-[rgba(245,101,48,.14)] text-[var(--up-orange-soft)]'
                          : 'bg-[var(--up-hair)] text-[var(--up-steel)]'
                      }`}
                    >
                      {soldOut ? 'SOLD OUT' : low ? `${g.totalStock} LEFT` : `${g.totalStock} IN STOCK`}
                    </span>
                  </div>
                </div>
              </Link>
            )
          })}
        </div>
      )}
    </div>
  )
}
