import { NextRequest, NextResponse } from 'next/server'
import fs from 'fs'
import { Readable } from 'stream'
import { getRecordingByToken } from '@/lib/store'

export async function GET(_req: NextRequest, { params }: { params: Promise<{ token: string }> }) {
  const { token } = await params
  const job = await getRecordingByToken(token)

  if (!job || job.status !== 'ready' || !job.expiresAt) {
    return NextResponse.json({ error: 'not found' }, { status: 404 })
  }
  if (new Date(job.expiresAt).getTime() < Date.now()) {
    return NextResponse.json({ error: 'link expired' }, { status: 410 })
  }

  if (!job.filePath || !fs.existsSync(job.filePath)) {
    return NextResponse.json({ error: 'file missing' }, { status: 404 })
  }

  const stat = fs.statSync(job.filePath)
  const stream = Readable.toWeb(
    fs.createReadStream(job.filePath)
  ) as unknown as ReadableStream<Uint8Array>

  return new NextResponse(stream, {
    headers: {
      'Content-Type': 'video/mp4',
      'Content-Length': String(stat.size),
      'Content-Disposition': `attachment; filename="court-recording-${job.id}.mp4"`,
    },
  })
}
