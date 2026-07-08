'use client'

import { useState, useEffect, useCallback, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { COURTS, TIME_SLOTS } from '@/lib/constants'

// ─── Types ────────────────────────────────────────────────────────────────────

type SlotInfo = { startTime: string; endTime: string; available: boolean }
type Availability = Record<string, SlotInfo[]>
type Prices = Record<string, number>
type MemberInfo = { id: string; name: string; phone: string } | null

// ─── Helpers ──────────────────────────────────────────────────────────────────

function timeToMinutes(t: string) {
  const [h, m] = t.split(':').map(Number)
  return h * 60 + m
}

function addMinutesToTime(t: string, mins: number): string {
  const total = timeToMinutes(t) + mins
  const h = Math.floor(total / 60).toString().padStart(2, '0')
  const m = (total % 60).toString().padStart(2, '0')
  return `${h}:${m}`
}

function formatDateDisplay(dateStr: string): string {
  const [year, month, day] = dateStr.split('-').map(Number)
  const d = new Date(year, month - 1, day)
  return d.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })
}

function localDateStr(d: Date): string {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function getDateRange(days: number): string[] {
  const result: string[] = []
  for (let i = 0; i < days; i++) {
    const d = new Date()
    d.setDate(d.getDate() + i)
    result.push(localDateStr(d))
  }
  return result
}

const DURATIONS = [
  { value: 60, label: '60 min' },
  { value: 90, label: '90 min' },
  { value: 120, label: '2 hours' },
]

const SPORTS = ['All', ...Array.from(new Set(COURTS.map((c) => c.sport)))]

const SPORT_COLORS: Record<string, string> = {
  Padel: '#6366f1',
  Pickleball: '#f59e0b',
}

const TIME_GROUPS: { label: string; icon: string; from: number; to: number }[] = [
  { label: 'Morning', icon: '🌅', from: timeToMinutes('06:00'), to: timeToMinutes('12:00') },
  { label: 'Afternoon', icon: '☀️', from: timeToMinutes('12:00'), to: timeToMinutes('17:00') },
  { label: 'Evening', icon: '🌙', from: timeToMinutes('17:00'), to: timeToMinutes('24:00') },
]

// ─── Main page ────────────────────────────────────────────────────────────────

export default function BookPage() {
  const router = useRouter()
  const today = localDateStr(new Date())
  const dateRange = useMemo(() => getDateRange(31), [])

  const [selectedDate, setSelectedDate] = useState(today)
  const [sportFilter, setSportFilter] = useState('All')
  const [selectedCourtId, setSelectedCourtId] = useState<string | null>(null)
  const [selectedStartTime, setSelectedStartTime] = useState<string | null>(null)
  const [selectedDuration, setSelectedDuration] = useState<number>(60)
  const [availability, setAvailability] = useState<Availability>({})
  const [prices, setPrices] = useState<Prices>({})
  const [member, setMember] = useState<MemberInfo | undefined>(undefined)
  const [loadingAvail, setLoadingAvail] = useState(true)
  const [bookingState, setBookingState] = useState<'idle' | 'confirming' | 'booking' | 'success' | 'error'>('idle')
  const [bookingError, setBookingError] = useState('')

  useEffect(() => {
    fetch('/api/account/me')
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => setMember(data ? data.member : null))
      .catch(() => setMember(null))
  }, [])

  useEffect(() => {
    fetch('/api/courts/prices')
      .then((r) => r.json())
      .then(setPrices)
      .catch(() => {})
  }, [])

  const loadAvailability = useCallback(async () => {
    setLoadingAvail(true)
    setSelectedStartTime(null)
    setBookingState('idle')
    try {
      const res = await fetch(`/api/courts/availability?date=${selectedDate}`)
      setAvailability(await res.json())
    } catch {
      setAvailability({})
    } finally {
      setLoadingAvail(false)
    }
  }, [selectedDate])

  useEffect(() => { loadAvailability() }, [loadAvailability])

  useEffect(() => {
    setSelectedStartTime(null)
    setBookingState('idle')
  }, [selectedCourtId, selectedDuration])

  const visibleCourts = COURTS.filter((c) => sportFilter === 'All' || c.sport === sportFilter)

  // Past slots on today should not be bookable
  const nowMins = useMemo(() => {
    const n = new Date()
    return n.getHours() * 60 + n.getMinutes()
  }, [])

  function slotIsPast(startTime: string): boolean {
    return selectedDate === today && timeToMinutes(startTime) <= nowMins
  }

  function freeSlotCount(courtId: string): number {
    const slots = availability[courtId] ?? []
    return slots.filter((s) => s.available && !slotIsPast(s.startTime)).length
  }

  function getValidSlots(courtId: string): Array<{ startTime: string; available: boolean }> {
    const slots = availability[courtId] ?? []
    const closeMins = timeToMinutes(TIME_SLOTS[TIME_SLOTS.length - 1]) + 30

    return TIME_SLOTS.map((startTime) => {
      if (slotIsPast(startTime)) return { startTime, available: false }
      const endMins = timeToMinutes(startTime) + selectedDuration
      if (endMins > closeMins) return { startTime, available: false }

      const numChunks = selectedDuration / 30
      for (let i = 0; i < numChunks; i++) {
        const chunkStart = addMinutesToTime(startTime, i * 30)
        const slot = slots.find((s) => s.startTime === chunkStart)
        if (!slot || !slot.available) return { startTime, available: false }
      }
      return { startTime, available: true }
    })
  }

  function getValidDurationsForSlot(courtId: string, startTime: string): number[] {
    const slots = availability[courtId] ?? []
    const closeMins = timeToMinutes(TIME_SLOTS[TIME_SLOTS.length - 1]) + 30

    return DURATIONS.filter(({ value }) => {
      if (timeToMinutes(startTime) + value > closeMins) return false
      const numChunks = value / 30
      for (let i = 0; i < numChunks; i++) {
        const chunkStart = addMinutesToTime(startTime, i * 30)
        const slot = slots.find((s) => s.startTime === chunkStart)
        if (!slot || !slot.available) return false
      }
      return true
    }).map((d) => d.value)
  }

  const selectedCourt = COURTS.find((c) => c.id === selectedCourtId)
  const pricePerHour = selectedCourtId ? (prices[selectedCourtId] ?? 0) : 0
  const totalPrice = (pricePerHour * selectedDuration) / 60
  const endTime = selectedStartTime ? addMinutesToTime(selectedStartTime, selectedDuration) : null

  async function handleBook() {
    if (!selectedCourtId || !selectedStartTime) return

    if (!member) {
      router.push(`/account/login?next=${encodeURIComponent('/book')}`)
      return
    }

    if (bookingState === 'confirming') {
      setBookingState('booking')
      setBookingError('')
      try {
        const res = await fetch('/api/account/bookings', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            courtId: selectedCourtId,
            date: selectedDate,
            startTime: selectedStartTime,
            durationMinutes: selectedDuration,
          }),
        })
        if (res.ok) {
          setBookingState('success')
        } else {
          const data = await res.json()
          setBookingError(data.error || 'Booking failed. Please try again.')
          setBookingState('error')
        }
      } catch {
        setBookingError('Network error. Please try again.')
        setBookingState('error')
      }
      return
    }

    setBookingState('confirming')
  }

  const validSlots = selectedCourtId ? getValidSlots(selectedCourtId) : []
  const showBar = selectedCourtId && selectedStartTime && bookingState !== 'success'

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white/90 backdrop-blur border-b border-gray-200 sticky top-0 z-30">
        <div className="max-w-2xl mx-auto px-4 py-3.5 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-600 to-violet-600 flex items-center justify-center shadow-sm">
              <svg style={{ width: 18, height: 18 }} className="text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16" />
              </svg>
            </div>
            <div>
              <span className="font-bold text-gray-900 leading-none block">Urban Playground</span>
              <span className="text-[11px] text-gray-400 leading-none">Muscat, Oman</span>
            </div>
          </div>
          {member === undefined ? null : member ? (
            <Link href="/account" className="flex items-center gap-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-full pl-1.5 pr-3 py-1.5 transition-colors">
              <span className="w-6 h-6 rounded-full bg-indigo-600 text-white text-xs font-bold flex items-center justify-center">
                {member.name.charAt(0).toUpperCase()}
              </span>
              My bookings
            </Link>
          ) : (
            <Link href="/account/login" className="text-sm bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-4 py-2 rounded-full transition-colors">
              Sign in
            </Link>
          )}
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 pb-40">
        {/* Hero */}
        <div className="pt-7 pb-5">
          <h1 className="text-2xl font-bold text-gray-900">Book a court</h1>
          <p className="text-gray-500 text-sm mt-0.5">Padel &amp; pickleball · open 06:00 – 24:00</p>
        </div>

        {/* Date strip */}
        <section className="mb-6">
          <div className="flex gap-2 overflow-x-auto pb-2 -mx-4 px-4 snap-x">
            {dateRange.map((dateStr) => {
              const isSelected = selectedDate === dateStr
              const isToday = dateStr === today
              const [y, m, d] = dateStr.split('-').map(Number)
              const dt = new Date(y, m - 1, d)
              return (
                <button
                  key={dateStr}
                  onClick={() => setSelectedDate(dateStr)}
                  className={`flex flex-col items-center px-1 py-2.5 rounded-2xl min-w-[56px] snap-start transition-all ${
                    isSelected
                      ? 'bg-gray-900 text-white shadow-lg scale-105'
                      : 'bg-white text-gray-600 border border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <span className={`text-[10px] font-medium uppercase tracking-wide ${isSelected ? 'text-gray-300' : 'text-gray-400'}`}>
                    {isToday ? 'Today' : dt.toLocaleDateString('en-US', { weekday: 'short' })}
                  </span>
                  <span className="text-lg font-bold leading-tight">{dt.getDate()}</span>
                  <span className={`text-[10px] ${isSelected ? 'text-gray-300' : 'text-gray-400'}`}>
                    {dt.toLocaleDateString('en-US', { month: 'short' })}
                  </span>
                </button>
              )
            })}
          </div>
        </section>

        {/* Sport filter */}
        <section className="mb-4">
          <div className="flex gap-2">
            {SPORTS.map((sport) => (
              <button
                key={sport}
                onClick={() => {
                  setSportFilter(sport)
                  if (sport !== 'All' && selectedCourt && selectedCourt.sport !== sport) {
                    setSelectedCourtId(null)
                  }
                }}
                className={`px-4 py-2 rounded-full text-sm font-semibold transition-all ${
                  sportFilter === sport
                    ? 'bg-gray-900 text-white shadow-sm'
                    : 'bg-white text-gray-600 border border-gray-200 hover:border-gray-300'
                }`}
              >
                {sport}
              </button>
            ))}
          </div>
        </section>

        {/* Court cards */}
        <section className="mb-7">
          <div className="grid grid-cols-2 gap-3">
            {visibleCourts.map((court) => {
              const price = prices[court.id]
              const sportColor = SPORT_COLORS[court.sport] ?? '#6366f1'
              const isSelected = selectedCourtId === court.id
              const free = loadingAvail ? null : freeSlotCount(court.id)
              return (
                <button
                  key={court.id}
                  onClick={() => setSelectedCourtId(isSelected ? null : court.id)}
                  className={`relative rounded-2xl p-4 text-left transition-all border-2 ${
                    isSelected
                      ? 'border-gray-900 bg-white shadow-lg'
                      : 'border-transparent bg-white shadow-sm hover:shadow-md'
                  }`}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div
                      className="w-9 h-9 rounded-xl flex items-center justify-center"
                      style={{ backgroundColor: `${sportColor}14` }}
                    >
                      <svg style={{ width: 18, height: 18, color: sportColor }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <circle cx="12" cy="12" r="9" strokeWidth={2} />
                        <path strokeWidth={2} d="M12 3c2.5 2.4 4 5.5 4 9s-1.5 6.6-4 9c-2.5-2.4-4-5.5-4-9s1.5-6.6 4-9z" />
                      </svg>
                    </div>
                    {isSelected && (
                      <div className="w-5 h-5 rounded-full bg-gray-900 flex items-center justify-center">
                        <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                        </svg>
                      </div>
                    )}
                  </div>
                  <p className="font-bold text-gray-900 text-sm">{court.name}</p>
                  <p className="text-xs font-medium" style={{ color: sportColor }}>{court.sport}</p>
                  <div className="flex items-center justify-between mt-2">
                    {free !== null ? (
                      <span className={`text-[11px] font-medium ${free > 0 ? 'text-green-600' : 'text-red-500'}`}>
                        {free > 0 ? `${free} slots free` : 'Fully booked'}
                      </span>
                    ) : (
                      <span className="text-[11px] text-gray-300">Checking…</span>
                    )}
                    {price !== undefined && price > 0 && (
                      <span className="text-[11px] text-gray-500 font-medium">OMR {price.toFixed(2)}/hr</span>
                    )}
                  </div>
                </button>
              )
            })}
          </div>
        </section>

        {/* Time & duration */}
        {selectedCourtId && (
          <section className="mb-6">
            <div className="flex items-center justify-between mb-3">
              <h2 className="font-bold text-gray-900">Pick a time</h2>
              <span className="text-xs text-gray-400">{formatDateDisplay(selectedDate)}</span>
            </div>

            {/* Duration segmented control */}
            <div className="flex bg-gray-200/70 rounded-xl p-1 mb-5">
              {DURATIONS.map(({ value, label }) => (
                <button
                  key={value}
                  onClick={() => setSelectedDuration(value)}
                  className={`flex-1 py-2 rounded-lg text-sm font-semibold transition-all ${
                    selectedDuration === value
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>

            {loadingAvail ? (
              <div className="text-center py-10 text-gray-400 text-sm">Loading availability…</div>
            ) : (
              <div className="space-y-5">
                {TIME_GROUPS.map((group) => {
                  const groupSlots = validSlots.filter((s) => {
                    const mins = timeToMinutes(s.startTime)
                    return mins >= group.from && mins < group.to
                  })
                  const anyAvailable = groupSlots.some((s) => s.available)
                  if (!groupSlots.length) return null
                  return (
                    <div key={group.label}>
                      <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
                        {group.icon} {group.label}
                        {!anyAvailable && <span className="ml-2 normal-case font-normal text-gray-300">— full</span>}
                      </p>
                      <div className="grid grid-cols-4 gap-2">
                        {groupSlots.map(({ startTime, available }) => {
                          const isSelected = selectedStartTime === startTime
                          return (
                            <button
                              key={startTime}
                              disabled={!available}
                              onClick={() => {
                                setSelectedStartTime(isSelected ? null : startTime)
                                setBookingState('idle')
                                if (!isSelected) {
                                  const valid = getValidDurationsForSlot(selectedCourtId, startTime)
                                  if (valid.length > 0 && !valid.includes(selectedDuration)) {
                                    setSelectedDuration(valid[0])
                                  }
                                }
                              }}
                              className={`py-2.5 rounded-xl text-sm font-semibold transition-all tabular-nums ${
                                !available
                                  ? 'bg-gray-100 text-gray-300 cursor-not-allowed line-through decoration-gray-300'
                                  : isSelected
                                  ? 'bg-gray-900 text-white shadow-md scale-105'
                                  : 'bg-white text-gray-800 shadow-sm hover:shadow border border-gray-100'
                              }`}
                            >
                              {startTime}
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
        )}

        {!selectedCourtId && !loadingAvail && (
          <p className="text-center text-sm text-gray-400 py-6">Select a court to see available times</p>
        )}
      </main>

      {/* Sticky bottom summary bar */}
      {showBar && (
        <div className="fixed bottom-0 inset-x-0 z-40 bg-white border-t border-gray-200 shadow-[0_-8px_30px_rgba(0,0,0,0.08)]">
          <div className="max-w-2xl mx-auto px-4 py-4">
            {bookingState === 'error' && (
              <div className="mb-3 p-3 rounded-xl bg-red-50 border border-red-100 text-red-600 text-sm">
                {bookingError}
              </div>
            )}
            {bookingState === 'confirming' && member && (
              <div className="mb-3 p-3 rounded-xl bg-indigo-50 border border-indigo-100 text-sm text-indigo-800">
                Booking as <span className="font-semibold">{member.name}</span> ({member.phone}) — tap confirm to finish
              </div>
            )}
            <div className="flex items-center gap-4">
              <div className="min-w-0 flex-1">
                <p className="font-bold text-gray-900 text-sm truncate">
                  {selectedCourt?.name} · {selectedStartTime} – {endTime}
                </p>
                <p className="text-xs text-gray-500 truncate">
                  {formatDateDisplay(selectedDate)}
                  {totalPrice > 0 && <span className="font-semibold text-gray-800"> · OMR {totalPrice.toFixed(2)}</span>}
                </p>
              </div>
              {(bookingState === 'confirming' || bookingState === 'error') && (
                <button
                  onClick={() => { setBookingState('idle'); setBookingError('') }}
                  className="px-4 py-3 rounded-xl border border-gray-200 text-gray-500 font-medium text-sm hover:bg-gray-50 transition-colors shrink-0"
                >
                  Back
                </button>
              )}
              <button
                onClick={handleBook}
                disabled={bookingState === 'booking'}
                className={`px-6 py-3 rounded-xl font-bold text-sm transition-all shrink-0 ${
                  bookingState === 'confirming'
                    ? 'bg-green-600 hover:bg-green-700 text-white shadow-md'
                    : 'bg-gray-900 hover:bg-gray-800 text-white shadow-md'
                } disabled:opacity-60`}
              >
                {bookingState === 'booking'
                  ? 'Booking…'
                  : bookingState === 'confirming'
                  ? 'Confirm ✓'
                  : !member
                  ? 'Sign in to book'
                  : 'Book now'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Success overlay */}
      {bookingState === 'success' && selectedCourt && selectedStartTime && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center px-4">
          <div className="bg-white rounded-3xl w-full max-w-sm p-7 text-center shadow-2xl">
            <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-1">You&apos;re booked! 🎾</h3>
            <p className="text-gray-500 text-sm">{selectedCourt.name} · {formatDateDisplay(selectedDate)}</p>
            <p className="text-gray-900 font-semibold mt-1">{selectedStartTime} – {endTime}</p>
            {totalPrice > 0 && (
              <p className="text-indigo-600 font-bold mt-2">OMR {totalPrice.toFixed(2)}</p>
            )}
            <div className="flex gap-2 mt-6">
              <button
                onClick={() => {
                  setSelectedStartTime(null)
                  setBookingState('idle')
                  setSelectedCourtId(null)
                  loadAvailability()
                }}
                className="flex-1 py-3 rounded-xl border border-gray-200 text-gray-600 font-semibold text-sm hover:bg-gray-50 transition-colors"
              >
                Book another
              </button>
              <Link
                href="/account"
                className="flex-1 py-3 rounded-xl bg-gray-900 hover:bg-gray-800 text-white font-semibold text-sm text-center transition-colors"
              >
                My bookings
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
