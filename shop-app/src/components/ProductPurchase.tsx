'use client'
import { useState } from 'react'
import { addToCart } from '@/lib/cart'

export type Variant = {
  id: string
  size: string | null
  priceBaisa: number
  stock: number
}

const fmt = (b: number) => (b / 1000).toFixed(3)

/**
 * Sizes are separate DB rows, so picking one just changes which row's id gets
 * added to the cart — price stays the same across a model's sizes, only stock
 * differs. Below `sm` the price + CTA live in a bar pinned to the viewport
 * bottom (always visible while scrolling the description); at `sm` and up
 * they sit inline, matching the rest of the site's product layout.
 */
export default function ProductPurchase({ variants }: { variants: Variant[] }) {
  const hasSizes = variants.length > 1 || variants[0]?.size != null
  const [selectedId, setSelectedId] = useState<string | null>(
    variants.length === 1 ? variants[0].id : null,
  )
  const [added, setAdded] = useState(false)

  const selected = variants.find((v) => v.id === selectedId) ?? null
  const totalStock = variants.reduce((n, v) => n + v.stock, 0)
  const needSize = variants.length > 1 && !selected
  const soldOut = !needSize && (selected ?? variants[0]).stock <= 0
  const price = (selected ?? variants[0]).priceBaisa

  function add() {
    if (!selected || selected.stock <= 0) return
    addToCart(selected.id, 1)
    setAdded(true)
    setTimeout(() => setAdded(false), 1600)
  }

  const label = needSize ? 'Pick a size' : soldOut ? 'Sold out' : added ? 'Added ✓' : 'Add to cart'
  const disabled = needSize || soldOut

  return (
    <div>
      {hasSizes && (
        <div className="mt-6">
          <div className="flex items-baseline justify-between">
            <span className="mono text-[11px] tracking-[.2em] text-[var(--up-steel)]">SIZE (EU)</span>
            <span className="mono text-[11px] tracking-[.14em] text-[#6d747f]">
              {variants.filter((v) => v.stock > 0).length} IN STOCK
            </span>
          </div>
          <div className="grid grid-cols-4 gap-2 mt-3">
            {variants.map((v) => {
              const on = v.id === selectedId
              const out = v.stock <= 0
              return (
                <button
                  key={v.id}
                  disabled={out}
                  onClick={() => setSelectedId(v.id)}
                  className={`flex flex-col items-center gap-1 py-2.5 px-1 rounded-[9px] border ${
                    out
                      ? 'opacity-35 cursor-not-allowed border-[var(--up-hair)]'
                      : on
                        ? 'border-[var(--up-orange)] bg-[var(--up-orange)] text-white'
                        : 'border-[var(--up-hair)] bg-[rgba(12,13,17,.4)] hover:border-[var(--up-orange)]'
                  }`}
                >
                  <span className="display text-base">{v.size}</span>
                  <span
                    className={`mono text-[7.5px] tracking-[.12em] ${
                      on ? 'text-white' : 'text-[var(--up-steel)]'
                    }`}
                  >
                    {out ? 'SOLD OUT' : v.stock <= 1 ? 'LAST' : `${v.stock} LEFT`}
                  </span>
                </button>
              )
            })}
          </div>
        </div>
      )}

      {!hasSizes && (
        <p className="mono text-xs tracking-[.14em] text-[var(--up-steel)] mt-2">
          {totalStock > 0 ? `${totalStock} IN STOCK` : 'SOLD OUT'}
        </p>
      )}

      {/* Desktop / tablet: inline CTA in the normal document flow. */}
      <div className="hidden sm:block mt-7">
        <button disabled={disabled} onClick={add} className="btn px-6 py-3 w-full sm:w-auto">
          {label}
        </button>
      </div>

      {/* Mobile: price + CTA pinned to the bottom of the viewport. */}
      <div className="sm:hidden fixed inset-x-0 bottom-0 z-30 px-4 pt-3 pb-6 bg-[rgba(16,17,22,.96)] backdrop-blur border-t border-[var(--up-hair)]">
        <div className="flex items-center gap-3">
          <div className="flex-1 min-w-0">
            <div className="mono text-[8.5px] tracking-[.18em] text-[var(--up-steel)]">TOTAL</div>
            <div className="display text-xl mt-0.5 tabular-nums">
              {fmt(price)} <span className="text-[var(--up-orange)] text-sm">OMR</span>
            </div>
          </div>
          <button disabled={disabled} onClick={add} className="btn flex-none px-5 py-3.5">
            {label.toUpperCase()}
          </button>
        </div>
      </div>
      {/* Spacer so the fixed bar never covers the last bit of content. */}
      <div className="sm:hidden h-24" />
    </div>
  )
}
