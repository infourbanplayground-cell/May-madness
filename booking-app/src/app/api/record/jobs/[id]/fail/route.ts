import { NextRequest, NextResponse } from 'next/server'
import { failRecordingJob } from '@/lib/store'
import { checkAgentSecret } from '@/lib/agentAuth'

export async function POST(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const authError = checkAgentSecret(req)
  if (authError) return authError

  const { id } = await params
  const body = await req.json().catch(() => ({}))
  await failRecordingJob(id, String(body.error ?? 'unknown error'))
  return NextResponse.json({ ok: true })
}
