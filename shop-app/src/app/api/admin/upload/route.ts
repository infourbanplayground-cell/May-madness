import { NextRequest, NextResponse } from 'next/server'
import { randomUUID } from 'crypto'
import { mkdir, writeFile } from 'fs/promises'
import path from 'path'
import { isAdmin } from '@/lib/adminAuth'

export const dynamic = 'force-dynamic'

const MAX_BYTES = 6 * 1024 * 1024

// Whitelist by sniffed content, not by the filename the browser sent. The
// stored name is a fresh UUID with an extension chosen from THIS map, so a
// file called "x.php" or "../../etc/passwd" cannot influence the path.
const TYPES: Record<string, string> = {
  'image/jpeg': 'jpg',
  'image/png': 'png',
  'image/webp': 'webp',
}

// Magic numbers, because a client can claim any Content-Type it likes.
function sniff(buf: Buffer): string | null {
  if (buf.length > 3 && buf[0] === 0xff && buf[1] === 0xd8 && buf[2] === 0xff) return 'image/jpeg'
  if (buf.length > 8 && buf.subarray(0, 8).equals(Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a])))
    return 'image/png'
  if (buf.length > 12 && buf.subarray(0, 4).toString() === 'RIFF' && buf.subarray(8, 12).toString() === 'WEBP')
    return 'image/webp'
  return null
}

export async function POST(req: NextRequest) {
  if (!(await isAdmin())) return NextResponse.json({ error: 'Unauthorised' }, { status: 401 })

  let form: FormData
  try {
    form = await req.formData()
  } catch {
    return NextResponse.json({ error: 'Malformed upload' }, { status: 400 })
  }

  const file = form.get('file')
  if (!(file instanceof File)) return NextResponse.json({ error: 'No file' }, { status: 400 })
  if (file.size === 0) return NextResponse.json({ error: 'That file is empty' }, { status: 400 })
  if (file.size > MAX_BYTES) {
    return NextResponse.json({ error: 'Image must be under 6MB' }, { status: 413 })
  }

  const buf = Buffer.from(await file.arrayBuffer())
  const kind = sniff(buf)
  if (!kind) return NextResponse.json({ error: 'Only JPEG, PNG or WebP images' }, { status: 415 })

  const name = `${randomUUID()}.${TYPES[kind]}`
  // NOT public/ — Next bakes that directory at build time, so anything written
  // there after a build 404s. This lives outside the build output and is
  // served by app/uploads/[file]/route.ts, which also means uploads survive a
  // redeploy instead of being overwritten by the release tarball.
  const dir = process.env.UPLOAD_DIR ?? path.join(process.cwd(), 'data', 'uploads')
  try {
    await mkdir(dir, { recursive: true })
    await writeFile(path.join(dir, name), buf)
  } catch (e) {
    console.error('upload failed', e)
    return NextResponse.json({ error: 'Could not save the image' }, { status: 500 })
  }

  return NextResponse.json({ url: `/uploads/${name}` })
}
