import { NextResponse } from 'next/server'
import { fetchMpBookings, fetchMpSales } from '@/lib/matchpoint'
import { COURTS, TIME_SLOTS } from '@/lib/constants'

function ymd(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function timeToMinutes(t: string): number {
  const [h, m] = t.split(':').map(Number)
  return h * 60 + m
}

export async function GET() {
  const now = new Date()
  const today = ymd(now)
  const weekEnd = new Date(now)
  weekEnd.setDate(weekEnd.getDate() + 6)

  try {
    const [weekBookings, todaySales] = await Promise.all([
      fetchMpBookings(today, ymd(weekEnd)),
      fetchMpSales(today, today).catch(() => []),
    ])

    const active = weekBookings.filter((b) => b.Status !== 'CANCELED')
    const todayBookings = active.filter((b) => b.Date === today)

    // Occupancy: booked minutes / total court-minutes in operating hours
    const openMinutes = TIME_SLOTS.length * 30 * COURTS.length
    const bookedMinutes = todayBookings.reduce(
      (sum, b) => sum + Math.max(0, timeToMinutes(b.EndTime) - timeToMinutes(b.StartTime)),
      0
    )
    const occupancy = openMinutes > 0 ? Math.round((bookedMinutes / openMinutes) * 100) : 0

    // Unique players today
    const players = new Set<string>()
    for (const b of todayBookings) {
      for (const p of b.Participants ?? []) {
        if (p.Name) players.add(p.Name)
      }
    }

    // Revenue today from sales documents
    const revenue = todaySales
      .filter((s) => !s.IsCanceled)
      .reduce((sum, s) => sum + (Number(s.Total) || 0), 0)

    // Next 7 days booking counts
    const week: { date: string; count: number }[] = []
    for (let i = 0; i < 7; i++) {
      const d = new Date(now)
      d.setDate(d.getDate() + i)
      const ds = ymd(d)
      week.push({ date: ds, count: active.filter((b) => b.Date === ds).length })
    }

    // Today's schedule sorted by start time
    const schedule = todayBookings
      .map((b) => ({
        id: b.Id,
        startTime: b.StartTime,
        endTime: b.EndTime,
        resourceName: b.ResourceName,
        playerName: b.Participants?.[0]?.Name || b.Description || '—',
        players: (b.Participants ?? []).length,
        billed: b.Billed,
      }))
      .sort((a, b) => a.startTime.localeCompare(b.startTime))

    return NextResponse.json({
      ok: true,
      today: {
        date: today,
        bookings: todayBookings.length,
        occupancy,
        players: players.size,
        revenue,
      },
      week,
      schedule,
    })
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    return NextResponse.json({ ok: false, error: message }, { status: 502 })
  }
}
