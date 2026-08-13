'use client'
import Link from 'next/link'
import { useEffect, useState } from 'react'
import { cartCount, onCartChange } from '@/lib/cart'

export default function CartButton() {
  // Starts at null rather than 0 so the server render and the first client
  // render agree; localStorage is only read after mount.
  const [n, setN] = useState<number | null>(null)

  useEffect(() => {
    const sync = () => setN(cartCount())
    sync()
    return onCartChange(sync)
  }, [])

  return (
    <Link href="/cart" className="btn-ghost px-4 py-2 flex items-center gap-3">
      <span className="mono text-[11px] tracking-[.18em]">CART</span>
      <span className="display text-lg text-[var(--up-orange)] tabular-nums">{n ?? 0}</span>
    </Link>
  )
}
