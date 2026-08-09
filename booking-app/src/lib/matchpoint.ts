import 'server-only'

const BASE_URL = 'https://urbanplayground.matchpoint.com.es/api/query'
const API_KEY = process.env.MATCHPOINT_API_KEY ?? ''

type MpEnvelope = {
  Ok: boolean
  Error: string | null
  Data: unknown[]
  Offset: number
  Limit: number
  HasMore: boolean
}

async function mpFetch(path: string): Promise<unknown[]> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'X-Api-Token': API_KEY },
    cache: 'no-store',
  })
  if (!res.ok) {
    throw new Error(`MatchPoint ${path} → ${res.status} ${res.statusText}`)
  }
  const json = await res.json() as MpEnvelope
  if (!json.Ok) {
    throw new Error(json.Error ?? 'MatchPoint API error')
  }
  return json.Data ?? []
}

export type MpBooking = {
  Id: number
  Venue: string
  Date: string
  StartTime: string
  EndTime: string
  ResourceName: string
  Description: string
  Locator: string
  Status: string
  Type: string
  Billed: boolean
  AccessCode: string
  Lighting: Record<string, unknown>
  Participants: MpParticipant[]
  Payments: MpPayment[]
}

export type MpParticipant = {
  Name: string
  Email: string
  Phone: string
  TotalAmount: number
  OwesMoney: boolean
  Paid: boolean
  Team?: string
  Position?: string
  Level?: string
  Gender?: string
}

export type MpPayment = {
  Date: string
  PayMethod: string
  Amount: number
}

export type MpMatch = {
  Id: number
  Venue: string
  Date: string
  StartTime: string
  EndTime: string
  Sport: string
  ResourceName: string
  CurrentPlayers: number
  MaxPlayers: number
  Status: string
  Competitive: boolean
  MinLevel: string
  MaxLevel: string
  Participants: MpParticipant[]
  Payments: MpPayment[]
}

export type MpActivity = {
  Id: number
  Venue: string
  Name: string
  Group: string
  Date: string
  StartTime: string
  EndTime: string
  ResourceName: string
  CurrentUsers: number
  MaxUsers: number
  Status: string
  Description: string
  Participants: MpParticipant[]
}

export type MpCustomer = {
  Code: string
  Name: string
  Email: string
  Mobile: string
  MemberCode: string
  EntryDate: string
  Status: string
  Type: string
  Groups: string[]
}

export type MpSale = {
  Id: number
  Date: string
  DocNumber: string
  Type: string
  IsCanceled: boolean
  CancelDate: string
  CustomerName: string
  CustomerCode: string
  CustomerIdent: string
  IssuerName: string
  IssuerVat: string
  Description: string
  Amount: number
  Vat: number
  Total: number
  Paid: boolean
  PayDate: string
  Lines: unknown[]
  Payments: MpPayment[]
}

export async function fetchMpBookings(dateFrom: string, dateTo: string): Promise<MpBooking[]> {
  return mpFetch(`/bookings?dateFrom=${dateFrom}&dateTo=${dateTo}`) as Promise<MpBooking[]>
}

export async function fetchMpMatches(dateFrom: string, dateTo: string): Promise<MpMatch[]> {
  return mpFetch(`/matches?dateFrom=${dateFrom}&dateTo=${dateTo}`) as Promise<MpMatch[]>
}

export async function fetchMpActivities(dateFrom: string, dateTo: string): Promise<MpActivity[]> {
  return mpFetch(`/activities?dateFrom=${dateFrom}&dateTo=${dateTo}`) as Promise<MpActivity[]>
}

export async function fetchMpCustomers(): Promise<MpCustomer[]> {
  return mpFetch('/customers') as Promise<MpCustomer[]>
}

/**
 * Every customer, following pagination. MatchPoint caps limit at 1000 and the
 * club has more than that, so a single call silently truncates.
 * maxPages guards against a HasMore that never goes false.
 */
export async function fetchAllMpCustomers(maxPages = 25): Promise<MpCustomer[]> {
  const all: MpCustomer[] = []
  let offset = 0
  const limit = 1000
  for (let page = 0; page < maxPages; page++) {
    const res = await fetch(`${BASE_URL}/customers?offset=${offset}&limit=${limit}`, {
      headers: { 'X-Api-Token': API_KEY },
      cache: 'no-store',
    })
    if (!res.ok) throw new Error(`MatchPoint /customers → ${res.status} ${res.statusText}`)
    const json = await res.json() as MpEnvelope
    if (!json.Ok) throw new Error(json.Error ?? 'MatchPoint API error')
    all.push(...((json.Data ?? []) as MpCustomer[]))
    if (!json.HasMore) break
    offset += limit
  }
  return all
}

export async function fetchMpSales(dateFrom: string, dateTo: string): Promise<MpSale[]> {
  return mpFetch(`/sales?dateFrom=${dateFrom}&dateTo=${dateTo}`) as Promise<MpSale[]>
}
