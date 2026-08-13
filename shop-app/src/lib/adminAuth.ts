import { createHmac, timingSafeEqual } from 'crypto'

// Same shape as booking-app/src/lib/memberAuth.ts: an HMAC-signed cookie value
// rather than a bare flag, so a user cannot grant themselves admin by editing
// a cookie in devtools.
function secret(): string {
  const s = process.env.SESSION_SECRET
  if (!s) throw new Error('SESSION_SECRET env var is not set')
  return s
}

export const ADMIN_COOKIE = 'shop_admin'

export function signAdmin(): string {
  const issued = String(Date.now())
  const sig = createHmac('sha256', secret()).update(issued).digest('hex')
  return `${issued}.${sig}`
}

export function verifyAdmin(value: string | undefined): boolean {
  if (!value) return false
  const dot = value.lastIndexOf('.')
  if (dot === -1) return false
  const issued = value.slice(0, dot)
  const sig = value.slice(dot + 1)
  const expected = createHmac('sha256', secret()).update(issued).digest('hex')
  try {
    const a = Buffer.from(sig, 'hex')
    const b = Buffer.from(expected, 'hex')
    if (a.length !== b.length) return false
    if (!timingSafeEqual(a, b)) return false
  } catch {
    return false
  }
  // 30 days, so a stolen cookie is not valid forever.
  return Date.now() - Number(issued) < 30 * 24 * 60 * 60 * 1000
}

export function checkPassword(supplied: string): boolean {
  const real = process.env.ADMIN_PASSWORD
  if (!real) return false
  const a = Buffer.from(supplied)
  const b = Buffer.from(real)
  if (a.length !== b.length) return false
  return timingSafeEqual(a, b)
}

export async function isAdmin(): Promise<boolean> {
  const { cookies } = await import('next/headers')
  const jar = await cookies()
  return verifyAdmin(jar.get(ADMIN_COOKIE)?.value)
}
