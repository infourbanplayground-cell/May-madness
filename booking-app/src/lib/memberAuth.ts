import { createHmac, timingSafeEqual } from 'crypto'
import type { NextRequest } from 'next/server'

function getSecret(): string {
  const secret = process.env.SESSION_SECRET
  if (!secret) throw new Error('SESSION_SECRET env var is not set')
  return secret
}

export function signMemberId(id: string): string {
  const sig = createHmac('sha256', getSecret()).update(id).digest('hex')
  return `${id}.${sig}`
}

export function verifyMemberSession(cookieValue: string): string | null {
  const lastDot = cookieValue.lastIndexOf('.')
  if (lastDot === -1) return null
  const id = cookieValue.slice(0, lastDot)
  const sig = cookieValue.slice(lastDot + 1)
  const expected = createHmac('sha256', getSecret()).update(id).digest('hex')
  try {
    const sigBuf = Buffer.from(sig, 'hex')
    const expBuf = Buffer.from(expected, 'hex')
    if (sigBuf.length !== expBuf.length) return null
    if (!timingSafeEqual(sigBuf, expBuf)) return null
    return id
  } catch {
    return null
  }
}

export function getMemberFromRequest(req: NextRequest): string | null {
  const cookie = req.cookies.get('member_session')
  if (!cookie) return null
  return verifyMemberSession(cookie.value)
}

// For server components using next/headers
export async function getMemberFromCookies(): Promise<string | null> {
  const { cookies } = await import('next/headers')
  const cookieStore = await cookies()
  const cookie = cookieStore.get('member_session')
  if (!cookie) return null
  return verifyMemberSession(cookie.value)
}
