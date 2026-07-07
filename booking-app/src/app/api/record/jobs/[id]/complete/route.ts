import { NextRequest, NextResponse } from 'next/server'
import { Readable } from 'stream'
import { pipeline } from 'stream/promises'
import fs from 'fs'
import path from 'path'
import { getRecordingById, completeRecordingJob } from '@/lib/store'
import { checkAgentSecret } from '@/lib/agentAuth'

const RECORDINGS_DIR = process.env.RECORDINGS_DIR || '/opt/booking-app/recordings'

export async function POST(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const authError = checkAgentSecret(req)
  if (authError) return authError

  const { id } = await params
  const job = await getRecordingById(id)
  if (!job) return NextResponse.json({ error: 'not found' }, { status: 404 })

  const form = await req.formData()
  const file = form.get('file')
  if (!(file instanceof File)) {
    return NextResponse.json({ error: 'file field required' }, { status: 400 })
  }

  await fs.promises.mkdir(RECORDINGS_DIR, { recursive: true })
  const filePath = path.join(RECORDINGS_DIR, `${id}.mp4`)
  await pipeline(
    Readable.fromWeb(file.stream() as import('stream/web').ReadableStream<Uint8Array>),
    fs.createWriteStream(filePath)
  )

  const stat = await fs.promises.stat(filePath)
  const updated = await completeRecordingJob(id, filePath, stat.size)
  return NextResponse.json(updated)
}
