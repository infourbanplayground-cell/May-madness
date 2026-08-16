'use client'

import { useState, useEffect, useCallback, useMemo } from 'react'
import Link from 'next/link'
import { COURTS, TIME_SLOTS } from '@/lib/constants'
import { BrandMark, Emblem } from '@/components/Brand'

// ─── Types ────────────────────────────────────────────────────────────────────

type SlotInfo = { startTime: string; endTime: string; available: boolean }
type Availability = Record<string, SlotInfo[]>
type Prices = Record<string, number>
type MemberInfo = { id: string; name: string; phone: string } | null

type Confirmed = {
  id: string
  courtId: string
  date: string
  startTime: string
  endTime: string
  playerName: string
  playerPhone: string
  priceTotal: number
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

const timeToMinutes = (t: string) => {
  const [h, m] = t.split(':').map(Number)
  return h * 60 + m
}

const addMinutes = (t: string, mins: number) => {
  const total = timeToMinutes(t) + mins
  return `${String(Math.floor(total / 60)).padStart(2, '0')}:${String(total % 60).padStart(2, '0')}`
}

const localDateStr = (d: Date) =>
  `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`

function formatDateLong(dateStr: string) {
  const [y, m, d] = dateStr.split('-').map(Number)
  return new Date(y, m - 1, d).toLocaleDateString('en-GB', {
    weekday: 'long', day: 'numeric', month: 'long',
  })
}

const DURATIONS = [60, 90, 120]

const TIME_GROUPS = [
  { label: 'Morning',   from: timeToMinutes('06:00'), to: timeToMinutes('12:00') },
  { label: 'Afternoon', from: timeToMinutes('12:00'), to: timeToMinutes('17:00') },
  { label: 'Evening',   from: timeToMinutes('17:00'), to: timeToMinutes('24:00') },
]

const COURT_ACCENT: Record<string, string> = {
  'court-1': '#FF8A3D',
  'court-2': '#FFC24B',
  'court-3': '#33A1FF',
  'court-4': '#8DF3E8',
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function BookPage() {
  const today = localDateStr(new Date())
  const dateRange = useMemo(
    () => Array.from({ length: 31 }, (_, i) => {
      const d = new Date()
      d.setDate(d.getDate() + i)
      return localDateStr(d)
    }),
    []
  )

  const [date, setDate] = useState(today)
  const [duration, setDuration] = useState(90)
  const [startTime, setStartTime] = useState<string | null>(null)
  const [courtId, setCourtId] = useState<string | null>(null)

  const [availability, setAvailability] = useState<Availability>({})
  const [prices, setPrices] = useState<Prices>({})
  const [member, setMember] = useState<MemberInfo | undefined>(undefined)
  const [loading, setLoading] = useState(true)

  const [sheetOpen, setSheetOpen] = useState(false)
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [confirmed, setConfirmed] = useState<Confirmed | null>(null)

  useEffect(() => {
    fetch('/api/account/me')
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        setMember(d ? d.member : null)
        if (d?.member) { setName(d.member.name); setPhone(d.member.phone) }
      })
      .catch(() => setMember(null))
  }, [])

  useEffect(() => {
    fetch('/api/courts/prices').then((r) => r.json()).then(setPrices).catch(() => {})
  }, [])

  const loadAvailability = useCallback(async () => {
    setLoading(true)
    setStartTime(null)
    setCourtId(null)
    try {
      const res = await fetch(`/api/courts/availability?date=${date}`)
      setAvailability(await res.json())
    } catch {
      setAvailability({})
    } finally {
      setLoading(false)
    }
  }, [date])

  useEffect(() => { loadAvailability() }, [loadAvailability])

  // Changing duration invalidates the chosen time and court.
  useEffect(() => { setStartTime(null); setCourtId(null) }, [duration])

  const nowMins = useMemo(() => {
    const n = new Date()
    return n.getHours() * 60 + n.getMinutes()
  }, [])

  const isPast = useCallback(
    (t: string) => date === today && timeToMinutes(t) <= nowMins,
    [date, today, nowMins]
  )

  /** Courts with every 30-min chunk free for `duration` starting at `t`. */
  const freeCourtsAt = useCallback(
    (t: string): string[] => {
      const closing = timeToMinutes(TIME_SLOTS[TIME_SLOTS.length - 1]) + 30
      if (timeToMinutes(t) + duration > closing) return []
      const chunks = duration / 30
      return COURTS.filter((court) => {
        const slots = availability[court.id] ?? []
        for (let i = 0; i < chunks; i++) {
          const s = slots.find((x) => x.startTime === addMinutes(t, i * 30))
          if (!s || !s.available) return false
        }
        return true
      }).map((c) => c.id)
    },
    [availability, duration]
  )

  // Precompute free courts for every slot once per availability/duration change.
  const slotMap = useMemo(() => {
    const map = new Map<string, string[]>()
    for (const t of TIME_SLOTS) map.set(t, isPast(t) ? [] : freeCourtsAt(t))
    return map
  }, [freeCourtsAt, isPast])

  const availableCourts = startTime ? (slotMap.get(startTime) ?? []) : []
  const selectedCourt = COURTS.find((c) => c.id === courtId)
  const endTime = startTime ? addMinutes(startTime, duration) : null
  const price = courtId ? ((prices[courtId] ?? 0) * duration) / 60 : 0

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    if (!courtId || !startTime) return
    setSubmitting(true)
    setError('')
    try {
      const res = await fetch('/api/bookings/public', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          courtId, date, startTime, durationMinutes: duration,
          playerName: name.trim(), playerPhone: phone.trim(),
        }),
      })
      const data = await res.json()
      if (!res.ok) {
        setError(data.error || 'Something went wrong. Please try again.')
        return
      }
      setConfirmed({ ...data.booking, priceTotal: data.booking.priceTotal ?? 0 })
      setSheetOpen(false)
    } catch {
      setError('Network problem. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  function reset() {
    setConfirmed(null)
    setStartTime(null)
    setCourtId(null)
    setError('')
    loadAvailability()
  }

  return (
    <div className="min-h-screen heat-bg pb-40">
      {/* Header */}
      <header className="sticky top-0 z-30 backdrop-blur bg-ink/85 border-b border-hair">
        <div className="max-w-lg mx-auto px-4 py-3 flex items-center justify-between">
          <BrandMark subtitle="Muscat, Oman" size={38} />
          {member === undefined ? null : member ? (
            <Link href="/account" className="label-mono text-ember hover:text-gold transition-colors">
              My bookings
            </Link>
          ) : (
            <Link href="/account/login" className="label-mono text-faint hover:text-cream transition-colors">
              Sign in
            </Link>
          )}
        </div>
      </header>

      <main className="max-w-lg mx-auto px-4">
        <div className="pt-7 pb-6">
          <h1 className="h-display text-4xl">Book a court</h1>
          <p className="text-warm text-sm mt-2">Padel &amp; pickleball · open 06:00 – 24:00</p>
          <p className="text-faint text-xs mt-1">No account needed — just your name and mobile.</p>
        </div>

        {/* 1 — Day */}
        <section className="mb-7">
          <p className="label-mono text-faint mb-3">
            <span className="text-ember">1</span> Pick a day
          </p>
          <div className="flex gap-2 overflow-x-auto pb-2 -mx-4 px-4">
            {dateRange.map((d) => {
              const sel = d === date
              const [y, mo, da] = d.split('-').map(Number)
              const dt = new Date(y, mo - 1, da)
              return (
                <button
                  key={d}
                  onClick={() => setDate(d)}
                  className={`shrink-0 w-[62px] py-2.5 rounded-2xl border transition-all ${
                    sel
                      ? 'border-ember bg-ember/15 text-cream'
                      : 'border-hair bg-surface/60 text-warm hover:border-warm/40'
                  }`}
                >
                  <span className="label-mono block text-[9px] text-faint">
                    {d === today ? 'Today' : dt.toLocaleDateString('en-GB', { weekday: 'short' })}
                  </span>
                  <span className="h-display block text-2xl mt-1">{dt.getDate()}</span>
                  <span className="label-mono block text-[9px] text-faint mt-0.5">
                    {dt.toLocaleDateString('en-GB', { month: 'short' })}
                  </span>
                </button>
              )
            })}
          </div>
        </section>

        {/* 2 — Duration */}
        <section className="mb-7">
          <p className="label-mono text-faint mb-3">
            <span className="text-ember">2</span> How long
          </p>
          <div className="grid grid-cols-3 gap-2">
            {DURATIONS.map((d) => (
              <button
                key={d}
                onClick={() => setDuration(d)}
                className={`py-3 rounded-2xl border font-semibold text-sm transition-all ${
                  duration === d
                    ? 'border-ember bg-ember/15 text-cream'
                    : 'border-hair bg-surface/60 text-warm hover:border-warm/40'
                }`}
              >
                {d} min
              </button>
            ))}
          </div>
        </section>

        {/* 3 — Time */}
        <section className="mb-7">
          <p className="label-mono text-faint mb-3">
            <span className="text-ember">3</span> Pick a start time
          </p>

          {loading ? (
            <p className="text-faint text-sm py-8 text-center">Checking availability…</p>
          ) : (
            <div className="space-y-5">
              {TIME_GROUPS.map((g) => {
                const slots = TIME_SLOTS.filter((t) => {
                  const m = timeToMinutes(t)
                  return m >= g.from && m < g.to
                })
                if (!slots.length) return null
                const anyFree = slots.some((t) => (slotMap.get(t) ?? []).length > 0)
                // Distinguish "already gone" from "taken" — telling someone
                // 06:00 is fully booked at 8pm is just wrong.
                const allPast = slots.every((t) => isPast(t))
                const suffix = anyFree ? null : allPast ? 'earlier today' : 'fully booked'
                return (
                  <div key={g.label}>
                    <p className="label-mono text-faint mb-2">
                      {g.label}
                      {suffix && (
                        <span className="text-faint/60 normal-case tracking-normal"> — {suffix}</span>
                      )}
                    </p>
                    <div className="grid grid-cols-4 gap-2">
                      {slots.map((t) => {
                        const free = (slotMap.get(t) ?? []).length
                        const sel = startTime === t
                        return (
                          <button
                            key={t}
                            disabled={free === 0}
                            onClick={() => { setStartTime(sel ? null : t); setCourtId(null) }}
                            className={`relative py-2.5 rounded-xl font-mono text-sm font-bold transition-all ${
                              free === 0
                                ? 'text-faint/40 line-through cursor-not-allowed bg-surface/30'
                                : sel
                                ? 'bg-ember text-ink'
                                : 'bg-surface text-cream border border-hair hover:border-ember/60'
                            }`}
                          >
                            {t}
                            {free > 0 && !sel && (
                              <span className="absolute top-1 right-1.5 text-[9px] text-faint font-sans">
                                {free}
                              </span>
                            )}
                          </button>
                        )
                      })}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </section>

        {/* 4 — Court, only once a time is chosen */}
        {startTime && (
          <section className="mb-8">
            <p className="label-mono text-faint mb-3">
              <span className="text-ember">4</span> Which court
            </p>
            <div className="grid grid-cols-2 gap-2.5">
              {availableCourts.map((id) => {
                const court = COURTS.find((c) => c.id === id)!
                const accent = COURT_ACCENT[id] ?? '#FF8A3D'
                const sel = courtId === id
                const rate = prices[id]
                return (
                  <button
                    key={id}
                    onClick={() => setCourtId(sel ? null : id)}
                    className={`rounded-2xl border p-4 text-left transition-all ${
                      sel ? 'border-ember bg-ember/10' : 'border-hair bg-surface/60 hover:border-warm/40'
                    }`}
                  >
                    <span
                      className="block w-8 h-1 rounded-full mb-3"
                      style={{ backgroundColor: accent }}
                    />
                    <p className="h-display text-lg">{court.name}</p>
                    <p className="label-mono mt-1" style={{ color: accent }}>{court.sport}</p>
                    {rate !== undefined && rate > 0 && (
                      <p className="text-faint text-xs mt-2 font-mono">
                        OMR {((rate * duration) / 60).toFixed(2)}
                      </p>
                    )}
                  </button>
                )
              })}
            </div>
          </section>
        )}
      </main>

      {/* Sticky summary */}
      {courtId && startTime && !confirmed && (
        <div className="fixed bottom-0 inset-x-0 z-40 border-t border-hair bg-ink/95 backdrop-blur">
          <div className="max-w-lg mx-auto px-4 py-4 flex items-center gap-4">
            <div className="min-w-0 flex-1">
              <p className="h-display text-lg truncate">
                {selectedCourt?.name} · {startTime}–{endTime}
              </p>
              <p className="label-mono text-faint mt-1 truncate">
                {formatDateLong(date)}
                {price > 0 && <span className="text-gold"> · OMR {price.toFixed(2)}</span>}
              </p>
            </div>
            <button
              onClick={() => { setSheetOpen(true); setError('') }}
              className="shrink-0 px-6 py-3 rounded-xl bg-gradient-to-r from-ember to-ember-deep text-ink font-bold text-sm hover:brightness-110 transition-all"
            >
              Book
            </button>
          </div>
        </div>
      )}

      {/* Details sheet — name and mobile only */}
      {sheetOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-end sm:items-center justify-center">
          <div className="w-full sm:max-w-sm bg-surface border-t sm:border border-hair sm:rounded-3xl rounded-t-3xl p-6">
            <div className="flex items-start justify-between mb-5">
              <div>
                <h2 className="h-display text-2xl">Almost there</h2>
                <p className="label-mono text-faint mt-1.5">
                  {selectedCourt?.name} · {startTime}–{endTime}
                </p>
              </div>
              <button
                onClick={() => setSheetOpen(false)}
                className="text-faint hover:text-cream text-xl leading-none"
                aria-label="Close"
              >
                ×
              </button>
            </div>

            {error && (
              <div className="mb-4 p-3 rounded-xl bg-flare/15 border border-flare/40 text-[#ff9a96] text-sm">
                {error}
              </div>
            )}

            <form onSubmit={submit} className="space-y-3">
              <div>
                <label className="label-mono text-faint block mb-1.5">Your name</label>
                <input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  autoFocus
                  placeholder="Full name"
                  className="w-full bg-ink border border-hair rounded-xl px-4 py-3 text-cream placeholder-faint/60 focus:outline-none focus:border-ember text-sm"
                />
              </div>
              <div>
                <label className="label-mono text-faint block mb-1.5">Mobile</label>
                <input
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  required
                  inputMode="tel"
                  placeholder="9123 4567"
                  className="w-full bg-ink border border-hair rounded-xl px-4 py-3 text-cream placeholder-faint/60 focus:outline-none focus:border-ember text-sm font-mono"
                />
              </div>
              <button
                type="submit"
                disabled={submitting}
                className="w-full py-3.5 rounded-xl bg-gradient-to-r from-ember to-ember-deep text-ink font-bold text-sm disabled:opacity-60 hover:brightness-110 transition-all"
              >
                {submitting ? 'Booking…' : `Confirm${price > 0 ? ` · OMR ${price.toFixed(2)}` : ''}`}
              </button>
              <p className="text-faint text-[11px] text-center pt-1">
                Pay at the club. Free cancellation up to 2 hours before.
              </p>
            </form>
          </div>
        </div>
      )}

      {/* Confirmation — account setup offered only now */}
      {confirmed && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center px-4">
          <div className="w-full max-w-sm bg-surface border border-hair rounded-3xl p-7 text-center">
            <div className="flex justify-center mb-4">
              <Emblem size={64} />
            </div>
            <h2 className="h-display text-3xl mb-2">You&apos;re booked</h2>
            <p className="text-warm text-sm">
              {COURTS.find((c) => c.id === confirmed.courtId)?.name} · {formatDateLong(confirmed.date)}
            </p>
            <p className="font-mono text-cream text-lg mt-1">
              {confirmed.startTime}–{confirmed.endTime}
            </p>
            {confirmed.priceTotal > 0 && (
              <p className="text-gold font-bold mt-2 font-mono">OMR {confirmed.priceTotal.toFixed(2)}</p>
            )}

            {!member && (
              <div className="mt-6 p-4 rounded-2xl bg-ink border border-hair text-left">
                <p className="h-display text-base mb-1">Want to skip this next time?</p>
                <p className="text-faint text-xs mb-3">
                  Set up an account to see your bookings and rebook in one tap.
                </p>
                <Link
                  href="/account/claim"
                  className="block w-full py-2.5 rounded-xl bg-ember/15 border border-ember/40 text-ember font-bold text-sm text-center hover:bg-ember/25 transition-colors"
                >
                  Set up my account
                </Link>
              </div>
            )}

            <button
              onClick={reset}
              className="w-full mt-3 py-3 rounded-xl border border-hair text-warm font-semibold text-sm hover:text-cream hover:border-warm/40 transition-colors"
            >
              Book another court
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
