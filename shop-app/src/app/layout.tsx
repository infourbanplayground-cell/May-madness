import type { Metadata } from 'next'
import Link from 'next/link'
import './globals.css'
import CartButton from '@/components/CartButton'

export const metadata: Metadata = {
  title: 'Urban Playground Shop',
  description: 'Padel gear, reserved online and collected at the club.',
  openGraph: {
    title: 'Urban Playground Shop',
    description: 'Padel gear, reserved online and collected at the club.',
    url: 'https://shop.urbanpadel.om',
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link
          href="https://fonts.googleapis.com/css2?family=Anton&family=Archivo:wght@400;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <header className="border-b border-[var(--up-hair)] sticky top-0 z-40 backdrop-blur bg-[rgba(8,9,12,.82)]">
          <div className="mx-auto max-w-5xl px-5 h-16 flex items-center justify-between gap-4">
            <Link href="/" className="flex items-baseline gap-3">
              <span className="display text-2xl">URBAN PLAYGROUND</span>
              <span className="mono text-[11px] tracking-[.22em] text-[var(--up-steel)] hidden sm:inline">
                SHOP
              </span>
            </Link>
            <CartButton />
          </div>
        </header>

        <main className="mx-auto max-w-5xl px-5 py-8">{children}</main>

        <footer className="mt-16 border-t border-[var(--up-hair)]">
          <div className="mx-auto max-w-5xl px-5 py-8 flex flex-wrap items-baseline justify-between gap-3">
            <span className="display text-xl">
              URBANPADEL<span className="text-[var(--up-orange)]">.</span>OM
            </span>
            <span className="mono text-[11px] tracking-[.2em] text-[var(--up-steel)]">
              URBAN PLAYGROUND · OMAN
            </span>
          </div>
        </footer>
      </body>
    </html>
  )
}
