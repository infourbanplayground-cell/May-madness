import Image from 'next/image'

/**
 * The full stacked lockup — racket emblem with URBAN / PLAYGROUND lettering.
 * The curved "PLAYGROUND" text stops being legible below about 90px tall, so
 * use <Emblem> plus a typographic wordmark for compact placements instead.
 */
export function Lockup({ height = 120, className = '' }: { height?: number; className?: string }) {
  // Source artwork is 327 x 507.
  const width = Math.round((height * 327) / 507)
  return (
    <Image
      src="/brand/up-logo.png"
      alt="Urban Playground"
      width={width}
      height={height}
      priority
      className={className}
    />
  )
}

/** The racket-and-ball mark on its own, for headers and tight spaces. */
export function Emblem({ size = 36, className = '' }: { size?: number; className?: string }) {
  return (
    <Image
      src="/brand/up-emblem.png"
      alt=""
      aria-hidden
      width={size}
      height={size}
      priority
      className={className}
    />
  )
}

/**
 * Header mark: emblem plus the name set in the display face. The emblem alone
 * is not yet recognisable enough to stand without the name.
 */
export function BrandMark({
  subtitle,
  size = 36,
}: {
  subtitle?: string
  size?: number
}) {
  return (
    <div className="flex items-center gap-2.5">
      <Emblem size={size} className="shrink-0" />
      <div className="leading-none">
        <p className="h-display text-[15px]">Urban Playground</p>
        {subtitle && <p className="label-mono text-faint mt-1.5">{subtitle}</p>}
      </div>
    </div>
  )
}
