'use client'

import { useState, useEffect, useCallback } from 'react'
import { CalendarDays, Users, Percent, Banknote, RefreshCw } from 'lucide-react'
import { formatTime } from '@/lib/time'

type Stats = {
  ok: boolean
  error?: string
  today?: {
    date: string
    bookings: number
    occupancy: number
    players: number
    revenue: number
  }
  week?: { date: string; count: number }[]
  schedule?: {
    id: number
    startTime: string
    endTime: string
    resourceName: string
    playerName: string
    players: number
    billed: boolean
  }[]
}

const DAY_SHORT = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

// MatchPoint names courts "Court 3 “MONDO”" etc, so match on the number.
const COURT_ACCENTS = ['#FF8A3D', '#FFC24B', '#33A1FF', '#8DF3E8']
function courtAccent(resourceName: string): string {
  const m = (resourceName ?? '').match(/\d+/)
  const idx = m ? parseInt(m[0], 10) - 1 : 0
  return COURT_ACCENTS[idx] ?? COURT_ACCENTS[0]
}

function dayLabel(dateStr: string, i: number): string {
  if (i === 0) return 'Today'
  const [y, m, d] = dateStr.split('-').map(Number)
  return DAY_SHORT[new Date(y, m - 1, d).getDay()]
}

export default function AdminDashboard() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch('/api/matchpoint/stats')
      setStats(await res.json())
    } catch {
      setStats({ ok: false, error: 'Network error' })
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  if (loading && !stats) {
    return (
      <div className="flex items-center justify-center h-64 text-faint text-sm gap-2">
        <RefreshCw size={16} className="animate-spin" /> Loading dashboard…
      </div>
    )
  }

  if (!stats?.ok) {
    return (
      <div className="max-w-md mx-auto mt-12 p-5 bg-red-900/20 border border-red-800 rounded-2xl text-center">
        <p className="text-red-400 font-semibold mb-1">Could not load stats</p>
        <p className="text-red-300/70 text-sm mb-4">{stats?.error}</p>
        <button onClick={load} className="px-4 py-2 rounded-lg bg-surface-2 hover:bg-surface-3 text-cream text-sm">
          Retry
        </button>
      </div>
    )
  }

  const t = stats.today!
  const week = stats.week ?? []
  const schedule = stats.schedule ?? []
  const maxCount = Math.max(1, ...week.map((w) => w.count))
  const peakIdx = week.findIndex((w) => w.count === maxCount)

  // JULY HEAT accents — ember, azure, lime, gold
  const tiles = [
    { label: 'Bookings today', value: String(t.bookings), icon: CalendarDays, accent: '#FF8A3D' },
    { label: 'Occupancy', value: `${t.occupancy}%`, icon: Percent, accent: '#33A1FF' },
    { label: 'Players', value: String(t.players), icon: Users, accent: '#E4FF3B' },
    { label: 'Revenue (OMR)', value: t.revenue.toFixed(2), icon: Banknote, accent: '#FFC24B' },
  ]

  return (
    <div className="h-full overflow-auto p-6">
      <div className="max-w-5xl mx-auto space-y-6">
        {/* Header row */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="h-display text-3xl">Today at Urban Playground</h1>
            <p className="label-mono text-faint mt-1.5">{t.date} · live from MatchPoint</p>
          </div>
          <button
            onClick={load}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-2 hover:bg-surface-3 text-cream/90 text-sm transition-colors"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh
          </button>
        </div>

        {/* Stat tiles */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {tiles.map(({ label, value, icon: Icon, accent }) => (
            <div key={label} className="bg-surface border border-hair rounded-2xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <div
                  className="w-7 h-7 rounded-lg flex items-center justify-center"
                  style={{ backgroundColor: `${accent}1a` }}
                >
                  <Icon size={14} style={{ color: accent }} />
                </div>
                <span className="label-mono text-faint">{label}</span>
              </div>
              <p className="h-display text-4xl mt-1 tabular-nums">{value}</p>
            </div>
          ))}
        </div>

        <div className="grid lg:grid-cols-5 gap-6">
          {/* 7-day outlook */}
          <div className="lg:col-span-2 bg-surface border border-hair rounded-2xl p-5">
            <h2 className="h-display text-xl">Next 7 days</h2>
            <p className="label-mono text-faint mt-1 mb-4">Bookings per day</p>
            <div className="flex items-end gap-2 h-32">
              {week.map((w, i) => {
                const h = Math.max(4, Math.round((w.count / maxCount) * 100))
                return (
                  <div key={w.date} className="flex-1 flex flex-col items-center gap-1.5 group relative h-full">
                    <div className="absolute -top-7 hidden group-hover:block bg-surface-2 border border-hair text-cream text-xs rounded-md px-2 py-0.5 whitespace-nowrap z-10">
                      {w.date}: {w.count}
                    </div>
                    {i === peakIdx && w.count > 0 && (
                      <span className="text-[10px] text-cream/90 font-semibold tabular-nums">{w.count}</span>
                    )}
                    {/* Track gives the bar a resolved height to size against —
                        a percentage against an auto-height parent collapses to 0. */}
                    <div className="w-full flex-1 flex items-end justify-center min-h-0">
                      <div
                        className="w-full max-w-[26px] rounded-t transition-colors bg-ember group-hover:bg-gold"
                        style={{ height: `${h}%` }}
                      />
                    </div>
                    <span className={`text-[10px] shrink-0 ${i === 0 ? 'text-ember font-semibold' : 'text-faint'}`}>
                      {dayLabel(w.date, i)}
                    </span>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Today's schedule */}
          <div className="lg:col-span-3 bg-surface border border-hair rounded-2xl p-5">
            <h2 className="h-display text-xl">Today&apos;s schedule</h2>
            <p className="label-mono text-faint mt-1 mb-4">{schedule.length} booking{schedule.length === 1 ? '' : 's'}</p>
            {schedule.length === 0 ? (
              <p className="text-sm text-faint py-8 text-center">No bookings today yet</p>
            ) : (
              <div className="space-y-2 max-h-64 overflow-auto pr-1">
                {schedule.map((b) => (
                  <div
                    key={b.id}
                    className="flex items-center gap-3 bg-surface-2/50 rounded-xl px-3 py-2.5 border-l-2"
                    style={{ borderLeftColor: courtAccent(b.resourceName) }}
                  >
                    <span className="font-mono text-xs font-bold text-gold tabular-nums w-36 shrink-0">
                      {formatTime(b.startTime)} – {formatTime(b.endTime)}
                    </span>
                    <span className="text-xs text-cream/90 truncate flex-1">{b.playerName}</span>
                    <span
                      className="font-mono text-[11px] shrink-0"
                      style={{ color: courtAccent(b.resourceName) }}
                    >
                      {b.resourceName}
                    </span>
                    {b.billed && (
                      <span className="text-[10px] bg-green-900/50 text-green-400 px-1.5 py-0.5 rounded-full shrink-0">
                        paid
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
