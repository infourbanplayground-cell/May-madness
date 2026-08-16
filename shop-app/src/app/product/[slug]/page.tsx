import Link from 'next/link'
import { notFound } from 'next/navigation'
import { getProduct, listProducts, initDB } from '@/lib/shop'
import { groupProducts } from '@/lib/group'
import ProductPurchase from '@/components/ProductPurchase'

export const dynamic = 'force-dynamic'

export default async function ProductPage({ params }: { params: Promise<{ slug: string }> }) {
  await initDB()
  const { slug } = await params
  const p = await getProduct(slug)
  if (!p || !p.active) notFound()

  // Re-derive the model group from the live catalogue rather than trusting
  // the URL alone, so sibling sizes always match what's actually in stock.
  const all = await listProducts()
  const group = groupProducts(all).find((g) => g.variants.some((v) => v.slug === slug))
  const variants = group?.variants ?? [p]

  return (
    <div>
      <Link href="/" className="mono text-[11px] tracking-[.18em] text-[var(--up-steel)] hover:text-[var(--up-chalk)]">
        ← BACK TO SHOP
      </Link>

      <div className="mt-6 grid gap-8 md:grid-cols-2">
        {p.imageUrl ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={p.imageUrl} alt={p.name} className="w-full object-cover bg-black/40" />
        ) : (
          <div className="w-full aspect-square bg-black/40 flex items-center justify-center">
            <span className="display text-7xl text-white/10">UP</span>
          </div>
        )}

        <div>
          <span className="mono text-[11px] tracking-[.24em] text-[var(--up-orange)]">
            {p.category.toUpperCase()}
          </span>
          <h1 className="display text-4xl sm:text-5xl mt-2 leading-[0.95]">{group?.name ?? p.name}</h1>

          <p className="display text-4xl mt-5 tabular-nums">
            {(p.priceBaisa / 1000).toFixed(3)}
            <span className="text-[var(--up-orange)] text-2xl ml-2">OMR</span>
          </p>

          {p.description && (
            <p className="mt-5 text-[#c3cad6] leading-relaxed whitespace-pre-line">
              {p.description}
            </p>
          )}

          <ProductPurchase
            variants={variants.map((v) => ({
              id: v.id,
              size: v.size,
              priceBaisa: v.priceBaisa,
              stock: v.stock,
            }))}
          />

          <div className="card p-5 mt-2 sm:mt-8">
            <p className="mono text-[11px] tracking-[.2em] text-[var(--up-orange)]">
              HOW IT WORKS
            </p>
            <p className="mt-3 text-sm text-[#c3cad6] leading-relaxed">
              Reserve it here and we hold it under your name. Pay by bank
              transfer or at the club when you collect. Nothing is charged
              online and we never ask for card details.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
