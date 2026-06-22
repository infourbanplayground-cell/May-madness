import 'server-only'

const BASE_URL = 'https://urbanplayground.matchpoint.com.es/api/query'
const API_KEY = process.env.MATCHPOINT_API_KEY ?? ''

async function mpFetch(path: string): Promise<unknown> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { Authorization: `Bearer ${API_KEY}` },
    cache: 'no-store',
  })
  if (!res.ok) {
    throw new Error(`MatchPoint ${path} → ${res.status} ${res.statusText}`)
  }
  return res.json()
}

export type MpBooking = {
  id: string | number
  courtName?: string
  courtId?: string | number
  date?: string
  startDate?: string
  start?: string
  end?: string
  startTime?: string
  endTime?: string
  customerName?: string
  customerPhone?: string
  notes?: string
  status?: string
  [key: string]: unknown
}

export type MpCustomer = {
  id: string | number
  name?: string
  firstName?: string
  lastName?: string
  phone?: string
  email?: string
  [key: string]: unknown
}

export type MpMatch = {
  id: string | number
  [key: string]: unknown
}

export type MpActivity = {
  id: string | number
  [key: string]: unknown
}

export type MpSale = {
  id: string | number
  [key: string]: unknown
}

export async function fetchMpBookings(dateFrom: string, dateTo: string): Promise<MpBooking[]> {
  const data = await mpFetch(`/bookings?dateFrom=${dateFrom}&dateTo=${dateTo}`)
  return (Array.isArray(data) ? data : (data as { data?: unknown[] }).data ?? []) as MpBooking[]
}

export async function fetchMpMatches(dateFrom: string, dateTo: string): Promise<MpMatch[]> {
  const data = await mpFetch(`/matches?dateFrom=${dateFrom}&dateTo=${dateTo}`)
  return (Array.isArray(data) ? data : (data as { data?: unknown[] }).data ?? []) as MpMatch[]
}

export async function fetchMpActivities(dateFrom: string, dateTo: string): Promise<MpActivity[]> {
  const data = await mpFetch(`/activities?dateFrom=${dateFrom}&dateTo=${dateTo}`)
  return (Array.isArray(data) ? data : (data as { data?: unknown[] }).data ?? []) as MpActivity[]
}

export async function fetchMpCustomers(): Promise<MpCustomer[]> {
  const data = await mpFetch('/customers')
  return (Array.isArray(data) ? data : (data as { data?: unknown[] }).data ?? []) as MpCustomer[]
}

export async function fetchMpSales(dateFrom: string, dateTo: string): Promise<MpSale[]> {
  const data = await mpFetch(`/sales?dateFrom=${dateFrom}&dateTo=${dateTo}`)
  return (Array.isArray(data) ? data : (data as { data?: unknown[] }).data ?? []) as MpSale[]
}
