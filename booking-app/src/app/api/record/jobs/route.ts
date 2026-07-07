import { NextRequest, NextResponse } from 'next/server'
import { claimPendingRecordingJobs } from '@/lib/store'
import { checkAgentSecret } from '@/lib/agentAuth'

export async function GET(req: NextRequest) {
  const authError = checkAgentSecret(req)
  if (authError) return authError

  const jobs = await claimPendingRecordingJobs()
  return NextResponse.json(jobs)
}
