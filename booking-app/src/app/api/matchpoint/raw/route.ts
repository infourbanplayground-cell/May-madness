import { NextRequest, NextResponse } from 'next/server'
import {
  fetchMpBookings,
  fetchMpCustomers,
  fetchMpMatches,
  fetchMpActivities,
  fetchMpSales,
} from '@/lib/matchpoint'

export async function GET(req: NextRequest) {
  const { searchParams } = req.nextUrl
  const endpoint = searchParams.get('endpoint') ?? 'bookings'
  const today = new Date()
  const ymd = (d: Date) =>
    `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  const dateFrom = searchParams.get('dateFrom') ?? ymd(new Date(today.getFullYear(), today.getMonth(), 1))
  const dateTo = searchParams.get('dateTo') ?? ymd(today)

  try {
    let data: unknown
    if (endpoint === 'bookings') data = await fetchMpBookings(dateFrom, dateTo)
    else if (endpoint === 'matches') data = await fetchMpMatches(dateFrom, dateTo)
    else if (endpoint === 'activities') data = await fetchMpActivities(dateFrom, dateTo)
    else if (endpoint === 'customers') data = await fetchMpCustomers()
    else if (endpoint === 'sales') data = await fetchMpSales(dateFrom, dateTo)
    else return NextResponse.json({ error: 'Unknown endpoint' }, { status: 400 })

    return NextResponse.json({ ok: true, endpoint, dateFrom, dateTo, data })
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    return NextResponse.json({ ok: false, error: message }, { status: 502 })
  }
}
