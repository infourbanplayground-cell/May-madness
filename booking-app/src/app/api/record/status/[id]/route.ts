import { NextRequest, NextResponse } from 'next/server'
import { getRecordingById } from '@/lib/store'

export async function GET(_req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const job = await getRecordingById(id)
  if (!job) return NextResponse.json({ error: 'not found' }, { status: 404 })
  return NextResponse.json(job)
}
