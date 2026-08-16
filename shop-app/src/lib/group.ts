// Shoes (and anything else sized) are stored one row per size — that's what
// stock and checkout need to stay correct. Browsing them as 16 near-identical
// rows is the actual bug this file fixes: group same-model rows back into one
// card, and let the product page split them out again as a size picker.

export type GroupableProduct = {
  id: string
  slug: string
  name: string
  category: string
  priceBaisa: number
  stock: number
  imageUrl: string | null
  size: string | null
}

export type ProductGroup<T extends GroupableProduct = GroupableProduct> = {
  key: string
  name: string
  category: string
  priceBaisa: number
  imageUrl: string | null
  totalStock: number
  variants: T[]
}

// "New Balance 796V3 Gris Blanco (42.5)" + size "42.5" -> "New Balance 796V3 Gris Blanco"
function modelName(p: GroupableProduct): string {
  if (!p.size) return p.name.trim()
  const suffix = `(${p.size})`
  const idx = p.name.lastIndexOf(suffix)
  if (idx === -1) return p.name.trim()
  return (p.name.slice(0, idx) + p.name.slice(idx + suffix.length)).replace(/\s+/g, ' ').trim()
}

function sizeSort(a: string | null, b: string | null): number {
  if (a === b) return 0
  if (a == null) return -1
  if (b == null) return 1
  const na = parseFloat(a)
  const nb = parseFloat(b)
  if (!Number.isNaN(na) && !Number.isNaN(nb) && na !== nb) return na - nb
  return a.localeCompare(b)
}

export function groupProducts<T extends GroupableProduct>(products: T[]): ProductGroup<T>[] {
  const map = new Map<string, T[]>()
  for (const p of products) {
    const key = `${p.category}::${modelName(p)}`
    const arr = map.get(key)
    if (arr) arr.push(p)
    else map.set(key, [p])
  }
  return [...map.entries()].map(([key, variants]) => {
    variants.sort((a, b) => sizeSort(a.size, b.size))
    const totalStock = variants.reduce((n, v) => n + v.stock, 0)
    const rep = variants.find((v) => v.stock > 0) ?? variants[0]
    return {
      key,
      name: modelName(rep),
      category: rep.category,
      priceBaisa: rep.priceBaisa,
      imageUrl: rep.imageUrl,
      totalStock,
      variants,
    }
  })
}
