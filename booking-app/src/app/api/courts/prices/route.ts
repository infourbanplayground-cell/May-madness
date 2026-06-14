import { NextResponse } from 'next/server'
import { getCourtPrices } from '@/lib/store'

export async function GET() {
  const prices = await getCourtPrices()
  return NextResponse.json(prices)
}
