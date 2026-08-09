import { NextRequest, NextResponse } from 'next/server'
import { searchCustomers } from '@/lib/store'

export async function GET(req: NextRequest) {
  const q = req.nextUrl.searchParams.get('q') ?? ''
  const results = await searchCustomers(q)
  return NextResponse.json({ ok: true, results })
}
