'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { formatTime } from '@/lib/time'
import { Emblem } from '@/components/Brand'

type DeskBooking = {
  id: string
  startTime: string
  endTime: string
  courtName: string
  courtColor: string
  sport: string
  playerName: string
  playerPhone: string
  notes: string
  source: string
}

const localDateStr = (d: Date) =>
  `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`

const toMins = (t: string) => {
  const [h, m] = t.split(':').map(Number)
  return h * 60 + m
}

function dayLabel(dateStr: string, today: string) {
  const [y, m, d] = dateStr.split('-').map(Number)
  const dt = new Date(y, m - 1, d)
  const t = new Date(today.split('-').map(Number)[0], today.split('-').map(Number)[1] - 1, today.split('-').map(Number)[2])
  const diff = Math.round((dt.getTime() - t.getTime()) / 86400000)
  if (diff === 0) return 'Today'
  if (diff === 1) return 'Tomorrow'
  if (diff === -1) return 'Yesterday'
  return dt.toLocaleDateString('en-GB', { weekday: 'long' })
}

function fullDate(dateStr: string) {
  const [y, m, d] = dateStr.split('-').map(Number)
  return new Date(y, m - 1, d).toLocaleDateString('en-GB', {
    weekday: 'short', day: 'numeric', month: 'long',
  })
}

export default function DeskBoard({ token }: { token: string }) {
  const today = localDateStr(new Date())
  const [date, setDate] = useState(today)
  const [rows, setRows] = useState<DeskBooking[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null)
  const [nowMins, setNowMins] = useState(() => {
    const n = new Date()
    return n.getHours() * 60 + n.getMinutes()
  })
  const firstLoad = useRef(true)

  const load = useCallback(async () => {
    try {
      const res = await fetch(`/api/desk?k=${encodeURIComponent(token)}&date=${date}`, {
        cache: 'no-store',
      })
      const json = await res.json()
      if (!res.ok || !json.ok) {
        setError(json.error ?? 'Could not load bookings')
        return
      }
      setRows(json.bookings)
      setError(null)
      setUpdatedAt(new Date())
    } catch {
      setError('No connection — showing the last update')
    } finally {
      firstLoad.current = false
    }
  }, [token, date])

  useEffect(() => { load() }, [load])

  // Refresh every 60s, and keep the "on now" highlight moving.
  useEffect(() => {
    const t = setInterval(() => {
      load()
      const n = new Date()
      setNowMins(n.getHours() * 60 + n.getMinutes())
    }, 60000)
    return () => clearInterval(t)
  }, [load])

  function shiftDay(delta: number) {
    const [y, m, d] = date.split('-').map(Number)
    const dt = new Date(y, m - 1, d)
    dt.setDate(dt.getDate() + delta)
    setDate(localDateStr(dt))
    setRows(null)
  }

  const isToday = date === today
  const onNow = (b: DeskBooking) =>
    isToday && toMins(b.startTime) <= nowMins && toMins(b.endTime) > nowMins
  const finished = (b: DeskBooking) => isToday && toMins(b.endTime) <= nowMins

  return (
    <div className="min-h-screen bg-ink text-cream">
      {/* Header */}
      <header className="sticky top-0 z-20 bg-ink/95 backdrop-blur border-b border-hair">
        <div className="max-w-3xl mx-auto px-4 py-3 flex items-center gap-3">
          <Emblem size={34} />
          <div className="min-w-0 flex-1">
            <h1 className="h-display text-xl leading-none">Today&apos;s bookings</h1>
            <p className="label-mono text-faint mt-1.5">
              {updatedAt
                ? `Updated ${updatedAt.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}`
                : 'Loading…'}
            </p>
          </div>
          <button
            onClick={load}
            className="shrink-0 px-3 py-2 rounded-xl bg-surface-2 hover:bg-surface-3 text-cream text-sm font-semibold transition-colors"
          >
            Refresh
          </button>
        </div>

        {/* Day nav */}
        <div className="max-w-3xl mx-auto px-4 pb-3 flex items-center gap-2">
          <button
            onClick={() => shiftDay(-1)}
            className="px-3 py-2 rounded-xl bg-surface border border-hair text-warm hover:text-cream text-sm"
            aria-label="Previous day"
          >
            ←
          </button>
          <div className="flex-1 text-center">
            <p className="h-display text-lg leading-none">{dayLabel(date, today)}</p>
            <p className="label-mono text-faint mt-1">{fullDate(date)}</p>
          </div>
          <button
            onClick={() => shiftDay(1)}
            className="px-3 py-2 rounded-xl bg-surface border border-hair text-warm hover:text-cream text-sm"
            aria-label="Next day"
          >
            →
          </button>
          {!isToday && (
            <button
              onClick={() => { setDate(today); setRows(null) }}
              className="px-3 py-2 rounded-xl bg-ember text-ink text-sm font-bold"
            >
              Today
            </button>
          )}
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-5">
        {error && (
          <div className="mb-4 p-3 rounded-xl bg-flare/15 border border-flare/40 text-[#ff9a96] text-sm">
            {error}
          </div>
        )}

        {rows === null && !error && (
          <p className="text-center text-faint py-16">Loading bookings…</p>
        )}

        {rows && rows.length === 0 && (
          <div className="text-center py-16">
            <p className="h-display text-2xl text-warm">No bookings</p>
            <p className="text-faint text-sm mt-2">Nothing booked for this day yet.</p>
          </div>
        )}

        {rows && rows.length > 0 && (
          <>
            <p className="label-mono text-faint mb-3">
              {rows.length} booking{rows.length === 1 ? '' : 's'}
            </p>
            <div className="space-y-2.5">
              {rows.map((b) => {
                const live = onNow(b)
                const done = finished(b)
                return (
                  <div
                    key={b.id}
                    className={`rounded-2xl border p-4 transition-colors ${
                      live
                        ? 'border-ember bg-ember/10'
                        : done
                        ? 'border-hair-soft bg-surface/40 opacity-55'
                        : 'border-hair bg-surface'
                    }`}
                  >
                    <div className="flex items-start gap-4">
                      {/* Time */}
                      <div className="shrink-0 w-28">
                        <p className="h-display text-2xl leading-none">
                          {formatTime(b.startTime).replace(' ', '')}
                        </p>
                        <p className="label-mono text-faint mt-1.5">
                          to {formatTime(b.endTime).replace(' ', '')}
                        </p>
                      </div>

                      {/* Player */}
                      <div className="min-w-0 flex-1">
                        <p className="text-lg font-bold truncate">{b.playerName}</p>
                        <div className="flex items-center gap-2 mt-1 flex-wrap">
                          <span
                            className="label-mono px-2 py-1 rounded-full"
                            style={{ backgroundColor: `${b.courtColor}22`, color: b.courtColor }}
                          >
                            {b.courtName}
                          </span>
                          {live && (
                            <span className="label-mono px-2 py-1 rounded-full bg-ember text-ink">
                              On now
                            </span>
                          )}
                          {b.source !== 'matchpoint' && (
                            <span className="label-mono px-2 py-1 rounded-full bg-lime/15 text-lime">
                              App
                            </span>
                          )}
                        </div>
                        {b.notes && (
                          <p className="text-xs text-faint mt-2 line-clamp-2">{b.notes}</p>
                        )}
                      </div>

                      {/* Phone */}
                      {b.playerPhone && (
                        <a
                          href={`tel:${b.playerPhone}`}
                          className="shrink-0 text-right font-mono text-sm text-gold hover:text-ember transition-colors"
                        >
                          {b.playerPhone}
                        </a>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </>
        )}

        <p className="text-center text-faint text-xs mt-8">
          Refreshes automatically every minute · Urban Playground
        </p>
      </main>
    </div>
  )
}
