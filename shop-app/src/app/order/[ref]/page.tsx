import Link from 'next/link'
import { notFound } from 'next/navigation'
import { getOrderByRef, fmtOMR, initDB } from '@/lib/shop'

export const dynamic = 'force-dynamic'

// Payment routes are read from the environment, so the real account details
// live on the server and never in the repo.
const BANK = process.env.PAY_BANK ?? 'Bank Muscat'
const ACCOUNT = process.env.PAY_ACCOUNT ?? ''
const MOBILE = process.env.PAY_MOBILE ?? ''
const WHATSAPP = process.env.SHOP_WHATSAPP ?? ''

export default async function OrderPage({ params }: { params: Promise<{ ref: string }> }) {
  await initDB()
  const { ref } = await params
  const order = await getOrderByRef(ref.toUpperCase())
  if (!order) notFound()

  const statusLabel: Record<string, string> = {
    pending: 'RESERVED — AWAITING PAYMENT',
    paid: 'PAID — READY TO COLLECT',
    collected: 'COLLECTED',
    cancelled: 'CANCELLED',
  }

  return (
    <div>
      <div className="plate plate-br p-7">
        <span className="mono text-[11px] tracking-[.24em] text-[var(--up-orange)]">
          {statusLabel[order.status] ?? order.status.toUpperCase()}
        </span>
        <h1 className="display text-4xl sm:text-5xl mt-3">ORDER {order.ref}</h1>
        <p className="mt-3 text-[#c3cad6]">
          Thanks {order.name.split(' ')[0]} — we&apos;re holding this for you at the club.
          Quote <strong className="text-[var(--up-chalk)]">{order.ref}</strong> when you collect.
        </p>
      </div>

      <div className="plate p-6 mt-5">
        <h2 className="mono text-[11px] tracking-[.24em] text-[var(--up-orange)]">YOUR ORDER</h2>
        {order.items.map((i, idx) => (
          <div
            key={idx}
            className="flex items-center justify-between gap-4 py-3 border-b border-[var(--up-hair)] last:border-0"
          >
            <span className="display text-lg">
              {i.name}
              <span className="mono text-xs text-[var(--up-steel)] ml-3">×{i.qty}</span>
            </span>
            <span className="display text-lg tabular-nums">{fmtOMR(i.unitBaisa * i.qty)}</span>
          </div>
        ))}
        <div className="flex items-baseline justify-between pt-4">
          <span className="mono text-xs tracking-[.2em] text-[var(--up-steel)]">TOTAL</span>
          <span className="display text-3xl tabular-nums">
            {fmtOMR(order.totalBaisa)}
            <span className="text-[var(--up-orange)] text-xl ml-2">OMR</span>
          </span>
        </div>
      </div>

      {order.status === 'pending' && (
        <div className="plate p-6 mt-5">
          <h2 className="mono text-[11px] tracking-[.24em] text-[var(--up-orange)]">
            HOW TO PAY
          </h2>
          <p className="mt-3 text-[#c3cad6]">
            Pay at the club when you collect, or transfer ahead and we&apos;ll have it
            waiting. Put <strong className="text-[var(--up-chalk)]">{order.ref}</strong> in
            the transfer reference.
          </p>

          {(ACCOUNT || MOBILE) && (
            <div className="mt-5 space-y-3">
              {BANK && <Row k="BANK" v={BANK} />}
              {ACCOUNT && <Row k="ACCOUNT NAME" v={ACCOUNT} />}
              {MOBILE && <Row k="MOBILE TRANSFER" v={MOBILE} />}
            </div>
          )}

          {WHATSAPP && (
            <a
              href={`https://wa.me/${WHATSAPP.replace(/\D/g, '')}?text=${encodeURIComponent(
                `Hi, I've placed order ${order.ref} on the Urban Playground shop.`,
              )}`}
              className="btn inline-block px-6 py-3 mt-6"
            >
              SEND US A MESSAGE
            </a>
          )}
        </div>
      )}

      <p className="mt-8">
        <Link href="/" className="mono text-[11px] tracking-[.18em] text-[var(--up-steel)] hover:text-[var(--up-chalk)]">
          ← BACK TO SHOP
        </Link>
      </p>
    </div>
  )
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex items-baseline gap-5 border-b border-[var(--up-hair)] pb-3 last:border-0">
      <span className="mono text-[11px] tracking-[.16em] text-[var(--up-steel)] w-40 shrink-0">
        {k}
      </span>
      <span className="mono text-lg">{v}</span>
    </div>
  )
}
