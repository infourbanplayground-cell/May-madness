import type { Metadata } from 'next'
import Link from 'next/link'
import './globals.css'
import CartButton from '@/components/CartButton'

export const metadata: Metadata = {
  title: 'Urban Playground Shop',
  description: 'Padel gear, reserved online and collected at the club in Muscat.',
  openGraph: {
    title: 'Urban Playground Shop',
    description: 'Padel gear, reserved online and collected at the club in Muscat.',
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
        <header className="border-b border-[var(--up-hair)] sticky top-0 z-40 backdrop-blur bg-[rgba(22,23,29,.86)]">
          <div className="mx-auto max-w-5xl px-5 h-[72px] flex items-center justify-between gap-4">
            <Link href="/" className="flex items-center gap-3 group">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src="/up-logo.png"
                alt="Urban Playground"
                className="h-11 w-auto transition-transform duration-200 group-hover:scale-105"
              />
              <span className="leading-tight">
                <span className="display text-xl block">URBAN PLAYGROUND</span>
                <span className="mono text-[10px] tracking-[.24em] text-[var(--up-steel)]">
                  SHOP · MUSCAT
                </span>
              </span>
            </Link>
            <CartButton />
          </div>
        </header>

        <main className="mx-auto max-w-5xl px-5 py-8">{children}</main>

        <footer className="mt-20 border-t border-[var(--up-hair)]">
          <div className="mx-auto max-w-5xl px-5 py-10 flex flex-wrap items-center gap-6">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/up-logo.png" alt="" className="h-16 w-auto opacity-80" />
            <div className="flex-1 min-w-[200px]">
              <p className="display text-xl">
                URBANPADEL<span className="text-[var(--up-orange)]">.</span>OM
              </p>
              <p className="text-sm text-[var(--up-steel)] mt-1">
                Come and play. We&apos;re at Urban Playground, Muscat — courts,
                leagues and the gear to go with them.
              </p>
            </div>
            <Link href="/admin" className="mono text-[10px] tracking-[.2em] text-[var(--up-steel)] hover:text-[var(--up-chalk)]">
              STAFF
            </Link>
          </div>
        </footer>
      </body>
    </html>
  )
}
