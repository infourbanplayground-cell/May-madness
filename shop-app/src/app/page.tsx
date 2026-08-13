import Link from 'next/link'
import { initDB, listProducts, fmtOMR } from '@/lib/shop'

export const dynamic = 'force-dynamic'

export default async function Home() {
  await initDB()
  const products = await listProducts()
  const categories = [...new Set(products.map((p) => p.category))]

  return (
    <div>
      <section className="mb-12">
        <span className="pill inline-block px-4 py-1.5 mono text-[11px] tracking-[.18em]">
          RESERVE ONLINE · COLLECT AT THE CLUB
        </span>
        <h1 className="display text-4xl sm:text-5xl leading-[1.02] mt-4">
          Everything you need
          <br />
          for your next game
        </h1>
        <p className="mt-4 max-w-xl text-[#cfd4dc] text-lg leading-relaxed">
          Rackets, balls, grips and kit — picked by the people you play with.
          Reserve it here and we&apos;ll have it waiting at the desk.{' '}
          <span className="text-[var(--up-chalk)] font-semibold">
            No card details, nothing charged online.
          </span>
        </p>
      </section>

      {products.length === 0 ? (
        <div className="card p-10 text-center">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/up-logo.png" alt="" className="h-24 w-auto mx-auto opacity-40" />
          <p className="display text-2xl mt-6">The shelves are being stocked</p>
          <p className="mt-3 text-[var(--up-steel)] max-w-md mx-auto">
            Nothing is listed just yet. Come back shortly, or ask at the desk —
            we can usually find what you need.
          </p>
        </div>
      ) : (
        categories.map((cat) => (
          <section key={cat} className="mb-14">
            <div className="flex items-center gap-4 mb-6">
              <h2 className="display text-2xl whitespace-nowrap">{cat}</h2>
              <span className="flex-1 h-px bg-[var(--up-hair)]" />
              <span className="mono text-[11px] tracking-[.14em] text-[var(--up-steel)]">
                {products.filter((p) => p.category === cat).length} ITEMS
              </span>
            </div>

            <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {products
                .filter((p) => p.category === cat)
                .map((p) => (
                  <Link key={p.id} href={`/product/${p.slug}`} className="card flex flex-col">
                    <div className="w-full h-48 bg-[#0f1015] flex items-center justify-center overflow-hidden">
                      {p.imageUrl ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img src={p.imageUrl} alt={p.name} className="w-full h-full object-cover" />
                      ) : (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img src="/up-logo.png" alt="" className="h-24 w-auto opacity-25" />
                      )}
                    </div>

                    <div className="p-5 flex flex-col flex-1 gap-3">
                      <div className="flex-1">
                        <h3 className="display text-xl leading-tight">{p.name}</h3>
                        {p.description && (
                          <p className="mt-1.5 text-sm text-[var(--up-steel)] line-clamp-2">
                            {p.description}
                          </p>
                        )}
                      </div>

                      <div className="flex items-baseline justify-between">
                        <span className="display text-2xl tabular-nums">
                          {fmtOMR(p.priceBaisa)}
                          <span className="text-[var(--up-orange)] text-sm ml-1.5">OMR</span>
                        </span>
                        <span
                          className={`mono text-[10px] tracking-[.12em] ${
                            p.stock > 0 ? 'text-[var(--up-steel)]' : 'text-[var(--up-orange)]'
                          }`}
                        >
                          {p.stock > 0 ? `${p.stock} LEFT` : 'SOLD OUT'}
                        </span>
                      </div>
                    </div>
                  </Link>
                ))}
            </div>
          </section>
        ))
      )}

      <section className="card p-7 mt-4">
        <h2 className="display text-2xl">How collecting works</h2>
        <div className="grid gap-6 sm:grid-cols-3 mt-5">
          {[
            ['Reserve it', 'Pick what you want and leave your name and number. Takes a minute.'],
            ['We hold it', 'Your order sits behind the desk under your reference — nobody else can take it.'],
            ['Pay when you collect', 'Cash, card at the club, or a bank transfer beforehand. Up to you.'],
          ].map(([h, b], i) => (
            <div key={h}>
              <span className="display text-3xl text-[var(--up-orange)]">{i + 1}</span>
              <h3 className="display text-lg mt-1">{h}</h3>
              <p className="text-sm text-[var(--up-steel)] mt-1 leading-relaxed">{b}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
