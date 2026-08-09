import 'server-only'
import bcrypt from 'bcryptjs'
import { randomInt } from 'crypto'
import { pool } from './store'
import { sendMail, emailLayout } from './mailer'

export const CODE_TTL_MINUTES = 15
export const MAX_ATTEMPTS = 5
/** Cooldown between code requests for the same customer. */
export const RESEND_COOLDOWN_SECONDS = 60

export type ClaimChannel = 'email' | 'whatsapp'

export type ClaimTarget = {
  customerCode: string
  name: string
  /** Where the code will actually be sent — always the address on file. */
  destination: string
  channel: ClaimChannel
  /** Obscured for display, e.g. a••••@gmail.com */
  masked: string
}

function maskEmail(email: string): string {
  const [local, domain] = email.split('@')
  if (!domain) return '•••'
  const head = local.slice(0, 1)
  return `${head}${'•'.repeat(Math.max(3, local.length - 1))}@${domain}`
}

/**
 * Find the customer a login identifier belongs to. The identifier may be an
 * email or a mobile number, but the code is always delivered to the contact
 * details already on file — never to something the requester supplies.
 * Returns null if there's no match, or the record has no deliverable address.
 */
export async function findClaimTarget(identifier: string): Promise<ClaimTarget | null> {
  const id = identifier.trim()
  if (id.length < 4) return null

  // Compare digits only for phone, so +968 92777777 matches 92777777.
  const digits = id.replace(/\D/g, '')

  const { rows } = await pool.query(
    `SELECT code, name, email, mobile FROM mp_customers
      WHERE lower(email) = lower($1)
         OR ($2 <> '' AND regexp_replace(mobile, '\\D', '', 'g') = $2)
      LIMIT 1`,
    [id, digits]
  )
  if (!rows.length) return null

  const row = rows[0]
  const email = String(row.email ?? '').trim()
  if (!email.includes('@')) return null // no deliverable channel yet

  return {
    customerCode: row.code as string,
    name: row.name as string,
    destination: email,
    channel: 'email',
    masked: maskEmail(email),
  }
}

/** True if a code was requested for this customer within the cooldown. */
export async function isRateLimited(customerCode: string): Promise<boolean> {
  const { rows } = await pool.query(
    `SELECT 1 FROM customer_claims
      WHERE customer_code = $1
        AND created_at > now() - ($2 || ' seconds')::interval
      LIMIT 1`,
    [customerCode, RESEND_COOLDOWN_SECONDS]
  )
  return rows.length > 0
}

export async function createAndSendCode(target: ClaimTarget): Promise<{ ok: boolean; error?: string }> {
  const code = String(randomInt(0, 1_000_000)).padStart(6, '0')
  const codeHash = await bcrypt.hash(code, 10)

  // Invalidate any outstanding codes for this customer.
  await pool.query(
    `UPDATE customer_claims SET consumed_at = now()
      WHERE customer_code = $1 AND consumed_at IS NULL`,
    [target.customerCode]
  )

  await pool.query(
    `INSERT INTO customer_claims (customer_code, channel, destination, code_hash, expires_at)
     VALUES ($1, $2, $3, $4, now() + ($5 || ' minutes')::interval)`,
    [target.customerCode, target.channel, target.destination, codeHash, CODE_TTL_MINUTES]
  )

  const firstName = target.name.split(' ')[0]
  const res = await sendMail({
    to: target.destination,
    subject: `${code} is your Urban Playground code`,
    text:
      `Hi ${firstName},\n\n` +
      `Your Urban Playground verification code is ${code}\n\n` +
      `It expires in ${CODE_TTL_MINUTES} minutes. If you didn't request this, ignore this email.\n\n` +
      `Urban Playground, Muscat`,
    html: emailLayout(
      `<p style="margin:0 0 14px;">Hi ${firstName},</p>
       <p style="margin:0 0 18px;">Here is your verification code for setting up your Urban Playground booking account:</p>
       <div style="text-align:center;margin:0 0 18px;">
         <span style="display:inline-block;background:#f3f4f6;border-radius:12px;padding:14px 26px;font-size:30px;font-weight:700;letter-spacing:7px;color:#111827;">${code}</span>
       </div>
       <p style="margin:0 0 8px;color:#6b7280;font-size:13px;">This code expires in ${CODE_TTL_MINUTES} minutes.</p>
       <p style="margin:0;color:#6b7280;font-size:13px;">If you didn't ask for this, you can safely ignore this email.</p>`,
      `Your code is ${code}`
    ),
  })

  if (!res.ok) return { ok: false, error: res.error }
  return { ok: true }
}

export type VerifyResult =
  | { ok: true; customerCode: string; name: string; mobile: string }
  | { ok: false; error: string }

export async function verifyCode(identifier: string, code: string): Promise<VerifyResult> {
  const target = await findClaimTarget(identifier)
  if (!target) return { ok: false, error: 'Invalid or expired code' }

  const { rows } = await pool.query(
    `SELECT * FROM customer_claims
      WHERE customer_code = $1 AND consumed_at IS NULL
      ORDER BY created_at DESC LIMIT 1`,
    [target.customerCode]
  )
  if (!rows.length) return { ok: false, error: 'Invalid or expired code' }

  const claim = rows[0]
  if (new Date(claim.expires_at) < new Date()) {
    return { ok: false, error: 'That code has expired — request a new one' }
  }
  if (claim.attempts >= MAX_ATTEMPTS) {
    return { ok: false, error: 'Too many attempts — request a new code' }
  }

  const matches = await bcrypt.compare(code.trim(), claim.code_hash as string)
  if (!matches) {
    await pool.query('UPDATE customer_claims SET attempts = attempts + 1 WHERE id = $1', [claim.id])
    return { ok: false, error: 'Invalid or expired code' }
  }

  await pool.query('UPDATE customer_claims SET consumed_at = now() WHERE id = $1', [claim.id])

  const { rows: cust } = await pool.query(
    'SELECT name, mobile FROM mp_customers WHERE code = $1',
    [target.customerCode]
  )
  return {
    ok: true,
    customerCode: target.customerCode,
    name: (cust[0]?.name as string) ?? target.name,
    mobile: (cust[0]?.mobile as string) ?? '',
  }
}
