import { NextRequest, NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import bcrypt from 'bcryptjs'
import { getMemberByPhone } from '@/lib/store'
import { signMemberId } from '@/lib/memberAuth'

export async function POST(req: NextRequest) {
  try {
    const { phone, password } = await req.json()

    if (!phone?.trim() || !password) {
      return NextResponse.json({ error: 'Phone and password are required' }, { status: 400 })
    }

    const member = await getMemberByPhone(phone.trim())
    if (!member) {
      return NextResponse.json({ error: 'Invalid phone number or password' }, { status: 401 })
    }

    const valid = await bcrypt.compare(password, member.passwordHash)
    if (!valid) {
      return NextResponse.json({ error: 'Invalid phone number or password' }, { status: 401 })
    }

    const cookieStore = await cookies()
    cookieStore.set('member_session', signMemberId(member.id), {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 60 * 60 * 24 * 30, // 30 days
      path: '/',
    })

    return NextResponse.json({ member: { id: member.id, name: member.name, phone: member.phone } })
  } catch (err) {
    console.error('Login error:', err)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
