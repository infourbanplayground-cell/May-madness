'use client'

import { useState, useEffect, useCallback } from 'react'
import { CalendarDays, Users, Percent, Banknote, RefreshCw } from 'lucide-react'

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
      <div className="flex items-center justify-center h-64 text-gray-500 text-sm gap-2">
        <RefreshCw size={16} className="animate-spin" /> Loading dashboard…
      </div>
    )
  }

  if (!stats?.ok) {
    return (
      <div className="max-w-md mx-auto mt-12 p-5 bg-red-900/20 border border-red-800 rounded-2xl text-center">
        <p className="text-red-400 font-semibold mb-1">Could not load stats</p>
        <p className="text-red-300/70 text-sm mb-4">{stats?.error}</p>
        <button onClick={load} className="px-4 py-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-200 text-sm">
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

  const tiles = [
    { label: 'Bookings today', value: String(t.bookings), icon: CalendarDays, accent: '#6366f1' },
    { label: 'Occupancy', value: `${t.occupancy}%`, icon: Percent, accent: '#10b981' },
    { label: 'Players', value: String(t.players), icon: Users, accent: '#f59e0b' },
    { label: 'Revenue (OMR)', value: t.revenue.toFixed(2), icon: Banknote, accent: '#ec4899' },
  ]

  return (
    <div className="h-full overflow-auto p-6">
      <div className="max-w-5xl mx-auto space-y-6">
        {/* Header row */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-white">Today at Urban Playground</h1>
            <p className="text-sm text-gray-500">{t.date} · live from MatchPoint</p>
          </div>
          <button
            onClick={load}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300 text-sm transition-colors"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh
          </button>
        </div>

        {/* Stat tiles */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {tiles.map(({ label, value, icon: Icon, accent }) => (
            <div key={label} className="bg-gray-900 border border-gray-800 rounded-2xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <div
                  className="w-7 h-7 rounded-lg flex items-center justify-center"
                  style={{ backgroundColor: `${accent}1a` }}
                >
                  <Icon size={14} style={{ color: accent }} />
                </div>
                <span className="text-xs text-gray-400">{label}</span>
              </div>
              <p className="text-2xl font-bold text-white tabular-nums">{value}</p>
            </div>
          ))}
        </div>

        <div className="grid lg:grid-cols-5 gap-6">
          {/* 7-day outlook */}
          <div className="lg:col-span-2 bg-gray-900 border border-gray-800 rounded-2xl p-5">
            <h2 className="text-sm font-semibold text-white mb-1">Next 7 days</h2>
            <p className="text-xs text-gray-500 mb-4">Bookings per day</p>
            <div className="flex items-end gap-2 h-32">
              {week.map((w, i) => {
                const h = Math.max(4, Math.round((w.count / maxCount) * 100))
                return (
                  <div key={w.date} className="flex-1 flex flex-col items-center gap-1.5 group relative">
                    <div className="absolute -top-7 hidden group-hover:block bg-gray-800 border border-gray-700 text-gray-100 text-xs rounded-md px-2 py-0.5 whitespace-nowrap z-10">
                      {w.date}: {w.count}
                    </div>
                    {i === peakIdx && w.count > 0 && (
                      <span className="text-[10px] text-gray-300 font-semibold tabular-nums">{w.count}</span>
                    )}
                    <div
                      className="w-full max-w-[26px] rounded-t transition-colors bg-indigo-500 group-hover:bg-indigo-400"
                      style={{ height: `${h}%` }}
                    />
                    <span className={`text-[10px] ${i === 0 ? 'text-indigo-400 font-semibold' : 'text-gray-500'}`}>
                      {dayLabel(w.date, i)}
                    </span>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Today's schedule */}
          <div className="lg:col-span-3 bg-gray-900 border border-gray-800 rounded-2xl p-5">
            <h2 className="text-sm font-semibold text-white mb-1">Today&apos;s schedule</h2>
            <p className="text-xs text-gray-500 mb-4">{schedule.length} booking{schedule.length === 1 ? '' : 's'}</p>
            {schedule.length === 0 ? (
              <p className="text-sm text-gray-500 py-8 text-center">No bookings today yet</p>
            ) : (
              <div className="space-y-2 max-h-64 overflow-auto pr-1">
                {schedule.map((b) => (
                  <div
                    key={b.id}
                    className="flex items-center gap-3 bg-gray-800/50 rounded-xl px-3 py-2.5"
                  >
                    <span className="text-xs font-semibold text-gray-200 tabular-nums w-24 shrink-0">
                      {b.startTime}–{b.endTime}
                    </span>
                    <span className="text-xs text-gray-400 truncate flex-1">{b.playerName}</span>
                    <span className="text-[11px] text-gray-500 shrink-0">{b.resourceName}</span>
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
