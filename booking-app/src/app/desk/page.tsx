import { timingSafeEqual } from 'crypto'
import DeskBoard from '@/components/DeskBoard'

export const metadata = {
  title: 'Front desk — Urban Playground',
  // Keep this page out of search results; the token is the only guard.
  robots: { index: false, follow: false },
}

function tokenOk(supplied?: string): boolean {
  const expected = process.env.DESK_TOKEN
  if (!expected || !supplied) return false
  const a = Buffer.from(supplied)
  const b = Buffer.from(expected)
  if (a.length !== b.length) return false
  return timingSafeEqual(a, b)
}

export default async function DeskPage({
  searchParams,
}: {
  searchParams: Promise<{ k?: string }>
}) {
  const { k } = await searchParams

  if (!tokenOk(k)) {
    return (
      <div className="min-h-screen bg-ink flex items-center justify-center px-6">
        <div className="text-center max-w-sm">
          <h1 className="h-display text-3xl mb-2">Link not valid</h1>
          <p className="text-warm text-sm">
            This front-desk link is missing or out of date. Ask the manager for the current one.
          </p>
        </div>
      </div>
    )
  }

  return <DeskBoard token={k!} />
}
