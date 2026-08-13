import Link from 'next/link'
import { initDB, listProducts, fmtOMR } from '@/lib/shop'

export const dynamic = 'force-dynamic'

export default async function Home() {
  await initDB()
  const products = await listProducts()

  const categories = [...new Set(products.map((p) => p.category))]

  return (
    <div>
      <section className="mb-10">
        <h1 className="display text-5xl sm:text-6xl leading-[0.95]">
          GEAR THAT
          <br />
          <span className="text-[var(--up-orange)]">SURVIVES</span> THE SEASON
        </h1>
        <p className="mt-4 max-w-xl text-[#c3cad6] font-semibold">
          Reserve online, pay and collect at the club. No delivery, no card
          details — your order is held under your name.
        </p>
      </section>

      {products.length === 0 ? (
        <div className="plate plate-br p-8">
          <p className="display text-2xl">NOTHING IN STOCK YET</p>
          <p className="mt-3 text-[#c3cad6]">
            Products added in the admin panel show up here straight away.
          </p>
        </div>
      ) : (
        categories.map((cat) => (
          <section key={cat} className="mb-12">
            <div className="flex items-center gap-4 mb-5">
              <h2 className="mono text-xs tracking-[.28em] text-[var(--up-orange)] whitespace-nowrap">
                {cat.toUpperCase()}
              </h2>
              <span className="flex-1 h-px bg-[var(--up-hair)]" />
            </div>

            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {products
                .filter((p) => p.category === cat)
                .map((p) => (
                  <Link
                    key={p.id}
                    href={`/product/${p.slug}`}
                    className="plate p-5 flex flex-col gap-3 hover:bg-[rgba(30,34,44,.95)] transition-colors"
                  >
                    {p.imageUrl ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={p.imageUrl}
                        alt={p.name}
                        className="w-full h-44 object-cover bg-black/40"
                      />
                    ) : (
                      <div className="w-full h-44 bg-black/40 flex items-center justify-center">
                        <span className="display text-4xl text-white/10">UP</span>
                      </div>
                    )}

                    <div className="flex-1">
                      <h3 className="display text-2xl leading-tight">{p.name}</h3>
                      {p.description && (
                        <p className="mt-1 text-sm text-[var(--up-steel)] line-clamp-2">
                          {p.description}
                        </p>
                      )}
                    </div>

                    <div className="flex items-baseline justify-between">
                      <span className="display text-2xl tabular-nums">
                        {fmtOMR(p.priceBaisa)}
                        <span className="text-[var(--up-orange)] text-base ml-1">OMR</span>
                      </span>
                      <span className="mono text-[11px] tracking-[.14em] text-[var(--up-steel)]">
                        {p.stock > 0 ? `${p.stock} IN STOCK` : 'SOLD OUT'}
                      </span>
                    </div>
                  </Link>
                ))}
            </div>
          </section>
        ))
      )}
    </div>
  )
}
