import 'server-only'
import { NextRequest, NextResponse } from 'next/server'

// Shared-secret auth for the local recording agent (not a browser session).
// Returns a 401 response if the secret is missing/wrong, otherwise null.
export function checkAgentSecret(req: NextRequest): NextResponse | null {
  const expected = process.env.RECORDING_AGENT_SECRET
  if (!expected) {
    return NextResponse.json({ error: 'RECORDING_AGENT_SECRET not configured' }, { status: 500 })
  }
  const provided = req.headers.get('x-agent-secret')
  if (provided !== expected) {
    return NextResponse.json({ error: 'unauthorized' }, { status: 401 })
  }
  return null
}
