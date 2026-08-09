import { NextRequest, NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import bcrypt from 'bcryptjs'
import { verifyCode } from '@/lib/claims'
import { createMemberFromCustomer } from '@/lib/store'
import { signMemberId } from '@/lib/memberAuth'

export async function POST(req: NextRequest) {
  const { identifier, code, password } = await req.json().catch(() => ({})) as {
    identifier?: string; code?: string; password?: string
  }

  if (!identifier?.trim() || !code?.trim() || !password) {
    return NextResponse.json({ error: 'Email or mobile, code, and password are required' }, { status: 400 })
  }
  if (password.length < 6) {
    return NextResponse.json({ error: 'Password must be at least 6 characters' }, { status: 400 })
  }

  const result = await verifyCode(identifier, code)
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 400 })
  }

  const passwordHash = await bcrypt.hash(password, 12)
  const member = await createMemberFromCustomer(
    result.customerCode,
    result.name,
    result.mobile,
    passwordHash
  )

  const cookieStore = await cookies()
  cookieStore.set('member_session', signMemberId(member.id), {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    maxAge: 60 * 60 * 24 * 30,
    path: '/',
  })

  return NextResponse.json({
    member: { id: member.id, name: member.name, phone: member.phone },
  })
}
