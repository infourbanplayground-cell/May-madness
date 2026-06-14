import { NextRequest, NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import bcrypt from 'bcryptjs'
import { createMember, getMemberByPhone, initDB } from '@/lib/store'
import { signMemberId } from '@/lib/memberAuth'

export async function POST(req: NextRequest) {
  try {
    await initDB()
    const { name, phone, password } = await req.json()

    if (!name?.trim() || !phone?.trim() || !password) {
      return NextResponse.json({ error: 'Name, phone, and password are required' }, { status: 400 })
    }

    if (password.length < 6) {
      return NextResponse.json({ error: 'Password must be at least 6 characters' }, { status: 400 })
    }

    const existing = await getMemberByPhone(phone.trim())
    if (existing) {
      return NextResponse.json({ error: 'An account with this phone number already exists' }, { status: 409 })
    }

    const passwordHash = await bcrypt.hash(password, 12)
    const member = await createMember(name.trim(), phone.trim(), passwordHash)

    const cookieStore = await cookies()
    cookieStore.set('member_session', signMemberId(member.id), {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 60 * 60 * 24 * 30, // 30 days
      path: '/',
    })

    return NextResponse.json({ member: { id: member.id, name: member.name, phone: member.phone } }, { status: 201 })
  } catch (err) {
    console.error('Register error:', err)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
