// Bulk-import the supplier invoice into shop_products.
//
//   node scripts/import-catalogue.mjs --markup 2.0            # dry run
//   node scripts/import-catalogue.mjs --markup 2.0 --commit   # write
//
// Everything lands HIDDEN (active=false). Nothing reaches the public shop
// until it is reviewed and switched on in the admin panel.
//
// Cost is taken from the LINE total divided by quantity, not the invoice's
// rounded per-unit column: 0.98 x 30 reads as 29.40 but the real line was
// 29.26, so the rounded column would overstate cost on every bulk item.
import { readFileSync } from 'fs'
import pg from 'pg'

const args = process.argv.slice(2)
const markup = Number(args[args.indexOf('--markup') + 1] ?? 2.0)
const commit = args.includes('--commit')
if (!Number.isFinite(markup) || markup <= 0) throw new Error('--markup must be a positive number')

// Retail rounds UP to a tidy shelf price, but the STEP has to scale with the
// price or the markup stops meaning anything: a 0.513 overgrip at 2.0x is
// 1.026, and forcing that to the nearest half rial would make it 1.500 — a
// 2.9x markup hiding inside a "2.0x" run. Sub-5 rial items step by 100 baisa.
const retailOf = (costBaisa) => {
  const raw = costBaisa * markup
  const step = raw < 5000 ? 100 : 500
  return Math.ceil(raw / step) * step
}

const slugify = (s) =>
  s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '')
   .replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 60)

const { items } = JSON.parse(readFileSync(new URL('./catalogue.json', import.meta.url)))

const rows = []
for (const it of items) {
  const lineBaisa = Math.round(it.lineOmr * 1000)
  const per = it.unitsPerPack ?? 1
  const units = it.qty * per                       // shelf units this line yields
  const costBaisa = Math.round(lineBaisa / units)  // cost per shelf unit
  const name = it.size ? `${it.name} (${it.size})` : it.name
  rows.push({
    slug: slugify(name),
    name,
    size: it.size || null,
    category: it.category,
    costBaisa,
    priceBaisa: retailOf(costBaisa),
    stock: units,
    lineBaisa,
  })
}

// Slugs are the natural key for re-running the import; a collision would
// silently merge two different SKUs, so fail loudly instead.
const seen = new Map()
for (const r of rows) {
  if (seen.has(r.slug)) throw new Error(`duplicate slug "${r.slug}" from "${r.name}" and "${seen.get(r.slug)}"`)
  seen.set(r.slug, r.name)
}

const f = (b) => (b / 1000).toFixed(3)
const totalCost = rows.reduce((n, r) => n + r.costBaisa * r.stock, 0)
const totalRetail = rows.reduce((n, r) => n + r.priceBaisa * r.stock, 0)

console.log(`${'ITEM'.padEnd(50)} ${'SIZE'.padEnd(8)} ${'COST'.padStart(9)} ${'RETAIL'.padStart(9)} ${'QTY'.padStart(4)}`)
for (const r of rows) {
  console.log(`${r.name.slice(0, 50).padEnd(50)} ${(r.size ?? '').padEnd(8)} ${f(r.costBaisa).padStart(9)} ${f(r.priceBaisa).padStart(9)} ${String(r.stock).padStart(4)}`)
}
console.log(`\n${rows.length} products, ${rows.reduce((n, r) => n + r.stock, 0)} units`)
console.log(`cost   ${f(totalCost)} OMR`)
console.log(`retail ${f(totalRetail)} OMR`)
console.log(`margin ${f(totalRetail - totalCost)} OMR  (${((1 - totalCost / totalRetail) * 100).toFixed(1)}%)`)

if (!commit) {
  console.log('\nDRY RUN — nothing written. Re-run with --commit.')
  process.exit(0)
}

const pool = new pg.Pool({ connectionString: process.env.DATABASE_URL })
const client = await pool.connect()
let inserted = 0, updated = 0
try {
  await client.query('BEGIN')
  for (const r of rows) {
    const { rowCount } = await client.query(
      `UPDATE shop_products
         SET name=$2, category=$3, price_baisa=$4, stock=$5, cost_baisa=$6, size=$7
       WHERE slug=$1`,
      [r.slug, r.name, r.category, r.priceBaisa, r.stock, r.costBaisa, r.size],
    )
    if (rowCount === 0) {
      await client.query(
        `INSERT INTO shop_products (slug,name,category,description,price_baisa,stock,active,cost_baisa,size)
         VALUES ($1,$2,$3,'',$4,$5,false,$6,$7)`,
        [r.slug, r.name, r.category, r.priceBaisa, r.stock, r.costBaisa, r.size],
      )
      inserted++
    } else updated++
  }
  await client.query('COMMIT')
} catch (e) {
  await client.query('ROLLBACK')
  throw e
} finally {
  client.release()
  await pool.end()
}
console.log(`\ninserted ${inserted}, updated ${updated} — all hidden until you publish them.`)
