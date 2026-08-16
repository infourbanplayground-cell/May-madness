import { NextRequest, NextResponse } from 'next/server'
import { ADMIN_COOKIE, checkPassword, signAdmin } from '@/lib/adminAuth'

export const dynamic = 'force-dynamic'

export async function POST(req: NextRequest) {
  const { password } = (await req.json().catch(() => ({}))) as { password?: string }
  if (typeof password !== 'string' || !checkPassword(password)) {
    // Deliberately vague, and slowed slightly so this endpoint is a poor
    // oracle for guessing.
    await new Promise((r) => setTimeout(r, 400))
    return NextResponse.json({ error: 'Wrong password' }, { status: 401 })
  }
  const res = NextResponse.json({ ok: true })
  res.cookies.set(ADMIN_COOKIE, signAdmin(), {
    httpOnly: true,
    sameSite: 'lax',
    secure: true,
    path: '/',
    maxAge: 30 * 24 * 60 * 60,
  })
  return res
}

export async function DELETE() {
  const res = NextResponse.json({ ok: true })
  res.cookies.delete(ADMIN_COOKIE)
  return res
}
