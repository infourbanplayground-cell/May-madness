import { NextRequest, NextResponse } from 'next/server'
import { findClaimTarget, createAndSendCode, isRateLimited } from '@/lib/claims'

/**
 * Ask for a verification code. Always responds the same way whether or not the
 * identifier matches a customer, so this cannot be used to discover who is on
 * the club's books. The `masked` hint is only returned on a real match, which
 * is unavoidable if the user is to know where to look for the code.
 */
export async function POST(req: NextRequest) {
  const { identifier } = await req.json().catch(() => ({})) as { identifier?: string }

  if (!identifier?.trim()) {
    return NextResponse.json({ error: 'Enter your email or mobile number' }, { status: 400 })
  }

  const generic = { ok: true, sent: true as const }

  const target = await findClaimTarget(identifier)
  if (!target) {
    // Small delay so a miss isn't obviously faster than a hit.
    await new Promise((r) => setTimeout(r, 400))
    return NextResponse.json(generic)
  }

  if (await isRateLimited(target.customerCode)) {
    return NextResponse.json(
      { error: 'A code was just sent. Please wait a minute before trying again.' },
      { status: 429 }
    )
  }

  const res = await createAndSendCode(target)
  if (!res.ok) {
    console.error('claim code send failed:', res.error)
    return NextResponse.json(
      { error: 'Could not send the code right now. Please try again shortly.' },
      { status: 502 }
    )
  }

  return NextResponse.json({ ...generic, masked: target.masked })
}
