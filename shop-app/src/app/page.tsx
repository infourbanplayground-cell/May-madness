import { initDB, listProducts } from '@/lib/shop'
import ShopBrowser from '@/components/ShopBrowser'

export const dynamic = 'force-dynamic'

export default async function Home() {
  await initDB()
  const products = await listProducts()

  return (
    <div>
      <section className="mb-8">
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

      <ShopBrowser products={products} />

      <section className="card p-7 mt-10">
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
