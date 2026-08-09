import 'server-only'
import nodemailer from 'nodemailer'

/**
 * Relays through the local Postfix instance, which is already configured with
 * SPF, DKIM (opendkim) and DMARC for urbanpadel.om. No external provider or
 * credentials involved.
 */
const transporter = nodemailer.createTransport({
  host: process.env.SMTP_HOST ?? '127.0.0.1',
  port: Number(process.env.SMTP_PORT ?? 25),
  secure: false,
  tls: { rejectUnauthorized: false },
})

export const MAIL_FROM = process.env.MAIL_FROM ?? 'Urban Playground <bookings@urbanpadel.om>'

export type SendResult = { ok: true; messageId: string } | { ok: false; error: string }

export async function sendMail(opts: {
  to: string
  subject: string
  html: string
  text: string
  headers?: Record<string, string>
}): Promise<SendResult> {
  try {
    const info = await transporter.sendMail({
      from: MAIL_FROM,
      to: opts.to,
      subject: opts.subject,
      text: opts.text,
      html: opts.html,
      headers: opts.headers,
    })
    return { ok: true, messageId: info.messageId }
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) }
  }
}

/** Shared shell so every message looks like it came from the same place. */
export function emailLayout(bodyHtml: string, preheader = ''): string {
  return `<!doctype html>
<html><body style="margin:0;padding:0;background:#f5f5f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
${preheader ? `<div style="display:none;max-height:0;overflow:hidden;opacity:0;">${preheader}</div>` : ''}
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f5f5f5;padding:24px 12px;">
  <tr><td align="center">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:520px;background:#ffffff;border-radius:16px;overflow:hidden;">
      <tr><td style="background:#4f46e5;padding:20px 28px;">
        <span style="color:#ffffff;font-size:17px;font-weight:700;">Urban Playground</span>
      </td></tr>
      <tr><td style="padding:28px;color:#1f2937;font-size:15px;line-height:1.6;">
        ${bodyHtml}
      </td></tr>
      <tr><td style="padding:18px 28px;background:#fafafa;color:#9ca3af;font-size:12px;line-height:1.5;">
        Urban Playground · Muscat, Oman<br>
        <a href="https://bookings.urbanpadel.om/book" style="color:#6b7280;">bookings.urbanpadel.om</a>
      </td></tr>
    </table>
  </td></tr>
</table>
</body></html>`
}
