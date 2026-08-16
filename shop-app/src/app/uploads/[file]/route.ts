import { NextResponse } from 'next/server'
import { readFile } from 'fs/promises'
import path from 'path'

export const dynamic = 'force-dynamic'

const MIME: Record<string, string> = { jpg: 'image/jpeg', png: 'image/png', webp: 'image/webp' }

// Only names this app generated: a UUID plus a known extension. Anything else
// is rejected before it reaches the filesystem, so "..%2f..%2fetc%2fpasswd"
// never becomes a path.
const SAFE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.(jpg|png|webp)$/

export async function GET(_req: Request, { params }: { params: Promise<{ file: string }> }) {
  const { file } = await params
  if (!SAFE.test(file)) return new NextResponse('Not found', { status: 404 })

  const dir = process.env.UPLOAD_DIR ?? path.join(process.cwd(), 'data', 'uploads')
  try {
    const buf = await readFile(path.join(dir, file))
    const ext = file.split('.').pop() as string
    return new NextResponse(new Uint8Array(buf), {
      headers: {
        'Content-Type': MIME[ext],
        // Content is immutable — the filename is a fresh UUID per upload.
        'Cache-Control': 'public, max-age=31536000, immutable',
      },
    })
  } catch {
    return new NextResponse('Not found', { status: 404 })
  }
}
