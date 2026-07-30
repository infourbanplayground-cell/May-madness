import { NextResponse } from 'next/server'
import { getPendingMatchpointEntry } from '@/lib/store'
import { COURTS } from '@/lib/constants'

const COURT_NAME = new Map(COURTS.map((c) => [c.id, c.name]))

/** RFC 4180: wrap in quotes and double any embedded quote. */
function csvCell(value: unknown): string {
  const s = value === null || value === undefined ? '' : String(value)
  return `"${s.replace(/"/g, '""')}"`
}

/** "2026-06-15 13:11" in Oman local time, rather than a raw Date toString. */
function formatTimestamp(value: string): string {
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return value
  const p = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}

export async function GET() {
  const pending = await getPendingMatchpointEntry()

  const header = [
    'Date', 'Start', 'End', 'Court', 'Player', 'Phone',
    'Duration (min)', 'Price (OMR)', 'Booked via', 'Booked at', 'Notes',
  ]

  const rows = pending.map((b) => [
    b.date,
    b.startTime,
    b.endTime,
    COURT_NAME.get(b.courtId) ?? b.courtId,
    b.playerName,
    b.playerPhone,
    b.durationMinutes ?? '',
    b.priceTotal != null ? b.priceTotal.toFixed(2) : '',
    b.bookingSource === 'member' ? 'Member (online)' : 'Front desk',
    formatTimestamp(b.createdAt),
    b.notes,
  ])

  // BOM so Excel opens UTF-8 names correctly.
  const csv = '﻿' + [header, ...rows].map((r) => r.map(csvCell).join(',')).join('\r\n')

  const today = new Date()
  const stamp = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`

  return new NextResponse(csv, {
    headers: {
      'Content-Type': 'text/csv; charset=utf-8',
      'Content-Disposition': `attachment; filename="matchpoint-to-enter-${stamp}.csv"`,
      'Cache-Control': 'no-store',
    },
  })
}
