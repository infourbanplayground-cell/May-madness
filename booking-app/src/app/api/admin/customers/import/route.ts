import { NextResponse } from 'next/server'
import { fetchAllMpCustomers } from '@/lib/matchpoint'
import { upsertCustomers, getCustomerCount, StoredCustomer } from '@/lib/store'

export const maxDuration = 60

export async function POST() {
  try {
    const mp = await fetchAllMpCustomers()

    // 22 records in this club have a blank Name but a real phone/email. Derive
    // something searchable rather than dropping the customer entirely.
    function displayName(c: (typeof mp)[number]): string {
      const given = String(c.Name ?? '').trim()
      if (given) return given
      const email = (c.Email ?? '').trim()
      if (email.includes('@')) return email.split('@')[0]
      const mobile = (c.Mobile ?? '').trim()
      if (mobile) return mobile
      return `Customer ${c.Code}`
    }

    let unnamed = 0
    const customers: StoredCustomer[] = mp
      .filter((c) => c.Code)
      .map((c) => {
        if (!String(c.Name ?? '').trim()) unnamed++
        return {
        code: String(c.Code),
        name: displayName(c),
        email: (c.Email ?? '').trim(),
        mobile: (c.Mobile ?? '').trim(),
        memberCode: (c.MemberCode ?? '').trim(),
        entryDate: c.EntryDate ? String(c.EntryDate).slice(0, 10) : null,
        status: (c.Status ?? '').trim(),
        type: (c.Type ?? '').trim(),
        groups: Array.isArray(c.Groups) ? c.Groups.map(String) : [],
        }
      })

    const inserted = await upsertCustomers(customers)
    const { total, lastImport } = await getCustomerCount()

    return NextResponse.json({
      ok: true,
      fetched: mp.length,
      imported: customers.length,
      newRecords: inserted,
      updated: customers.length - inserted,
      unnamed,
      total,
      lastImport,
    })
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    return NextResponse.json({ ok: false, error: message }, { status: 502 })
  }
}

export async function GET() {
  const { total, lastImport } = await getCustomerCount()
  return NextResponse.json({ ok: true, total, lastImport })
}
