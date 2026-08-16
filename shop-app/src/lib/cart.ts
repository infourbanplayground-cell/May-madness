'use client'

// The cart lives in localStorage only. It holds ids and quantities and
// deliberately NOT prices — the server re-prices every line at checkout, so a
// stale or edited cart can never change what an order costs.
export type CartLine = { productId: string; qty: number }

const KEY = 'up-shop-cart-v1'
const EVENT = 'up-cart-change'

export function readCart(): CartLine[] {
  if (typeof window === 'undefined') return []
  try {
    const raw = window.localStorage.getItem(KEY)
    if (!raw) return []
    const parsed: unknown = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    return parsed
      .filter(
        (l): l is CartLine =>
          !!l && typeof l === 'object' &&
          typeof (l as CartLine).productId === 'string' &&
          Number.isFinite((l as CartLine).qty),
      )
      .map((l) => ({ productId: l.productId, qty: Math.max(1, Math.floor(l.qty)) }))
  } catch {
    return []
  }
}

function write(lines: CartLine[]) {
  window.localStorage.setItem(KEY, JSON.stringify(lines))
  // Storage events only fire in OTHER tabs, so the header count in THIS tab
  // needs an explicit nudge.
  window.dispatchEvent(new CustomEvent(EVENT))
}

export function addToCart(productId: string, qty = 1) {
  const lines = readCart()
  const found = lines.find((l) => l.productId === productId)
  if (found) found.qty += qty
  else lines.push({ productId, qty })
  write(lines)
}

export function setQty(productId: string, qty: number) {
  let lines = readCart()
  if (qty <= 0) lines = lines.filter((l) => l.productId !== productId)
  else {
    const f = lines.find((l) => l.productId === productId)
    if (f) f.qty = qty
  }
  write(lines)
}

export function clearCart() {
  write([])
}

export function cartCount(): number {
  return readCart().reduce((n, l) => n + l.qty, 0)
}

export function onCartChange(fn: () => void): () => void {
  window.addEventListener(EVENT, fn)
  window.addEventListener('storage', fn)
  return () => {
    window.removeEventListener(EVENT, fn)
    window.removeEventListener('storage', fn)
  }
}
