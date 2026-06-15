'use client'

import { useState, useEffect, useCallback } from 'react'
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

function formatDateShort(dateStr: string): string {
  const [year, month, day] = dateStr.split('-').map(Number)
  const d = new Date(year, month - 1, day)
  return d.toLocaleDateString('en-US', { weekday: 'short', day: 'numeric' })
}

function localDateStr(d: Date): string {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function getTodayStr(): string {
  return localDateStr(new Date())
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
  { value: 60, label: '1h' },
  { value: 90, label: '1.5h' },
  { value: 120, label: '2h' },
]

const SPORT_COLORS: Record<string, string> = {
  Padel: '#6366f1',
  Pickleball: '#f59e0b',
}

// ─── Main page ────────────────────────────────────────────────────────────────

export default function BookPage() {
  const router = useRouter()
  const today = getTodayStr()
  const dateRange = getDateRange(31)

  const [selectedDate, setSelectedDate] = useState(today)
  const [selectedCourtId, setSelectedCourtId] = useState<string | null>(null)
  const [selectedStartTime, setSelectedStartTime] = useState<string | null>(null)
  const [selectedDuration, setSelectedDuration] = useState<number>(60)
  const [availability, setAvailability] = useState<Availability>({})
  const [prices, setPrices] = useState<Prices>({})
  const [member, setMember] = useState<MemberInfo>(undefined as unknown as MemberInfo)
  const [loadingAvail, setLoadingAvail] = useState(false)
  const [bookingState, setBookingState] = useState<'idle' | 'confirming' | 'booking' | 'success' | 'error'>('idle')
  const [bookingError, setBookingError] = useState('')

  // Load member session
  useEffect(() => {
    fetch('/api/account/me')
      .then((r) => r.ok ? r.json() : null)
      .then((data) => setMember(data ? data.member : null))
      .catch(() => setMember(null))
  }, [])

  // Load prices once
  useEffect(() => {
    fetch('/api/courts/prices')
      .then((r) => r.json())
      .then(setPrices)
      .catch(() => {})
  }, [])

  // Load availability when date changes
  const loadAvailability = useCallback(async () => {
    setLoadingAvail(true)
    setSelectedStartTime(null)
    setBookingState('idle')
    try {
      const res = await fetch(`/api/courts/availability?date=${selectedDate}`)
      const data = await res.json()
      setAvailability(data)
    } catch {
      setAvailability({})
    } finally {
      setLoadingAvail(false)
    }
  }, [selectedDate])

  useEffect(() => { loadAvailability() }, [loadAvailability])

  // When court or duration changes, reset time selection
  useEffect(() => {
    setSelectedStartTime(null)
    setBookingState('idle')
  }, [selectedCourtId, selectedDuration])

  // Compute which start times are valid for the selected duration on selected court
  function getValidSlots(courtId: string): Array<{ startTime: string; available: boolean }> {
    const slots = availability[courtId] ?? []
    const lastSlot = TIME_SLOTS[TIME_SLOTS.length - 1]
    const lastSlotEnd = addMinutesToTime(lastSlot, 30)

    return TIME_SLOTS.map((startTime) => {
      const endTime = addMinutesToTime(startTime, selectedDuration)

      // Check end time doesn't exceed closing time
      if (timeToMinutes(endTime) > timeToMinutes(lastSlotEnd)) {
        return { startTime, available: false }
      }

      // Check all 30-min chunks in the duration are available
      const numChunks = selectedDuration / 30
      let allFree = true
      for (let i = 0; i < numChunks; i++) {
        const chunkStart = addMinutesToTime(startTime, i * 30)
        const slot = slots.find((s) => s.startTime === chunkStart)
        if (!slot || !slot.available) {
          allFree = false
          break
        }
      }

      return { startTime, available: allFree }
    })
  }

  // Which durations are valid for a given start time on selected court
  function getValidDurationsForSlot(courtId: string, startTime: string): number[] {
    const slots = availability[courtId] ?? []
    const lastSlot = TIME_SLOTS[TIME_SLOTS.length - 1]
    const lastSlotEnd = addMinutesToTime(lastSlot, 30)

    return DURATIONS.filter(({ value }) => {
      const endTime = addMinutesToTime(startTime, value)
      if (timeToMinutes(endTime) > timeToMinutes(lastSlotEnd)) return false
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
      const next = encodeURIComponent('/book')
      router.push(`/account/login?next=${next}`)
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

  function resetBooking() {
    setSelectedStartTime(null)
    setBookingState('idle')
    setBookingError('')
    loadAvailability()
  }

  const validSlots = selectedCourtId ? getValidSlots(selectedCourtId) : []

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-20">
        <div className="max-w-2xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-indigo-600 flex items-center justify-center shadow-sm">
              <svg className="w-4.5 h-4.5 text-white" style={{ width: 18, height: 18 }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16" />
              </svg>
            </div>
            <span className="font-bold text-gray-900">Urban Padel</span>
          </div>
          <div className="flex items-center gap-3">
            {member === undefined ? null : member ? (
              <Link href="/account" className="text-sm text-indigo-600 font-medium hover:text-indigo-700">
                My bookings
              </Link>
            ) : (
              <Link href="/account/login" className="text-sm text-indigo-600 font-medium hover:text-indigo-700">
                Sign in
              </Link>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 pb-16">
        {/* Hero */}
        <div className="py-8 text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Book a court</h1>
          <p className="text-gray-500">Choose your court, date, and time</p>
        </div>

        {/* Step 1: Court selection */}
        <section className="mb-8">
          <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
            Step 1 — Select court
          </h2>
          <div className="grid grid-cols-2 gap-3">
            {COURTS.map((court) => {
              const price = prices[court.id]
              const sportColor = SPORT_COLORS[court.sport] ?? '#6366f1'
              const isSelected = selectedCourtId === court.id
              return (
                <button
                  key={court.id}
                  onClick={() => setSelectedCourtId(isSelected ? null : court.id)}
                  className={`relative rounded-2xl border-2 p-4 text-left transition-all ${
                    isSelected
                      ? 'border-indigo-500 bg-indigo-50 shadow-md'
                      : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm'
                  }`}
                >
                  <div
                    className="w-8 h-8 rounded-lg flex items-center justify-center mb-3"
                    style={{ backgroundColor: `${sportColor}15` }}
                  >
                    <div className="w-4 h-4 rounded-full" style={{ backgroundColor: sportColor }} />
                  </div>
                  <p className="font-semibold text-gray-900 text-sm">{court.name}</p>
                  <p className="text-xs font-medium mt-0.5" style={{ color: sportColor }}>
                    {court.sport}
                  </p>
                  {price !== undefined && price > 0 ? (
                    <p className="text-xs text-gray-500 mt-1.5">OMR {price.toFixed(2)}/hr</p>
                  ) : price === 0 ? (
                    <p className="text-xs text-gray-400 mt-1.5">Free</p>
                  ) : null}
                  {isSelected && (
                    <div className="absolute top-3 right-3 w-5 h-5 rounded-full bg-indigo-600 flex items-center justify-center">
                      <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                  )}
                </button>
              )
            })}
          </div>
        </section>

        {/* Step 2: Date picker */}
        <section className="mb-8">
          <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
            Step 2 — Select date
          </h2>
          <div className="flex gap-2 overflow-x-auto pb-2 -mx-4 px-4">
            {dateRange.map((dateStr) => {
              const isSelected = selectedDate === dateStr
              const isToday = dateStr === today
              const [year, month, day] = dateStr.split('-').map(Number)
              const d = new Date(year, month - 1, day)
              const dayName = d.toLocaleDateString('en-US', { weekday: 'short' })
              const dayNum = d.getDate()
              return (
                <button
                  key={dateStr}
                  onClick={() => setSelectedDate(dateStr)}
                  className={`flex flex-col items-center px-3 py-2.5 rounded-xl min-w-[52px] transition-all ${
                    isSelected
                      ? 'bg-indigo-600 text-white shadow-md'
                      : isToday
                      ? 'bg-indigo-50 text-indigo-700 border border-indigo-200'
                      : 'bg-white text-gray-600 border border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <span className="text-xs font-medium">{isToday ? 'Today' : dayName}</span>
                  <span className="text-lg font-bold leading-tight">{dayNum}</span>
                </button>
              )
            })}
          </div>
          <p className="text-sm text-gray-600 mt-3 font-medium">{formatDateDisplay(selectedDate)}</p>
        </section>

        {/* Step 3: Time + duration (only when court selected) */}
        {selectedCourtId && (
          <section className="mb-8">
            <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
              Step 3 — Choose time &amp; duration
            </h2>

            {/* Duration picker */}
            <div className="mb-4">
              <p className="text-sm font-medium text-gray-700 mb-2">Duration</p>
              <div className="flex gap-2">
                {DURATIONS.map(({ value, label }) => (
                  <button
                    key={value}
                    onClick={() => setSelectedDuration(value)}
                    className={`flex-1 py-2.5 rounded-xl text-sm font-semibold transition-all border ${
                      selectedDuration === value
                        ? 'bg-indigo-600 text-white border-indigo-600 shadow-sm'
                        : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>

            {/* Time grid */}
            {loadingAvail ? (
              <div className="text-center py-8 text-gray-400 text-sm">Loading availability…</div>
            ) : (
              <>
                <p className="text-sm font-medium text-gray-700 mb-2">Available times</p>
                <div className="grid grid-cols-4 gap-2">
                  {validSlots.map(({ startTime, available }) => {
                    const isSelected = selectedStartTime === startTime
                    return (
                      <button
                        key={startTime}
                        disabled={!available}
                        onClick={() => {
                          setSelectedStartTime(isSelected ? null : startTime)
                          setBookingState('idle')
                          // Auto-adjust duration if needed
                          if (!isSelected) {
                            const validDurations = getValidDurationsForSlot(selectedCourtId, startTime)
                            if (validDurations.length > 0 && !validDurations.includes(selectedDuration)) {
                              setSelectedDuration(validDurations[0])
                            }
                          }
                        }}
                        className={`py-2.5 rounded-xl text-sm font-medium transition-all border ${
                          !available
                            ? 'bg-gray-100 text-gray-300 border-gray-100 cursor-not-allowed'
                            : isSelected
                            ? 'bg-green-500 text-white border-green-500 shadow-sm'
                            : 'bg-green-50 text-green-700 border-green-200 hover:bg-green-100 hover:border-green-300'
                        }`}
                      >
                        {startTime}
                      </button>
                    )
                  })}
                </div>

                <div className="flex items-center gap-4 mt-3">
                  <div className="flex items-center gap-1.5 text-xs text-gray-500">
                    <div className="w-3 h-3 rounded-sm bg-green-100 border border-green-300" />
                    Available
                  </div>
                  <div className="flex items-center gap-1.5 text-xs text-gray-500">
                    <div className="w-3 h-3 rounded-sm bg-gray-100 border border-gray-200" />
                    Taken
                  </div>
                </div>
              </>
            )}
          </section>
        )}

        {/* Booking summary + CTA */}
        {selectedCourtId && selectedStartTime && bookingState !== 'success' && (
          <section className="bg-white rounded-2xl border-2 border-indigo-100 shadow-md p-5 mb-6">
            <h3 className="font-semibold text-gray-900 mb-4">Booking summary</h3>
            <div className="space-y-2 text-sm mb-4">
              <div className="flex justify-between">
                <span className="text-gray-500">Court</span>
                <span className="font-medium text-gray-900">{selectedCourt?.name} · {selectedCourt?.sport}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Date</span>
                <span className="font-medium text-gray-900">{formatDateDisplay(selectedDate)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Time</span>
                <span className="font-medium text-gray-900">{selectedStartTime} – {endTime}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Duration</span>
                <span className="font-medium text-gray-900">
                  {selectedDuration >= 60
                    ? `${selectedDuration / 60}${selectedDuration % 60 ? '.5' : ''}h`
                    : `${selectedDuration}min`}
                </span>
              </div>
              {totalPrice > 0 && (
                <div className="flex justify-between pt-2 border-t border-gray-100 mt-2">
                  <span className="font-semibold text-gray-700">Total</span>
                  <span className="font-bold text-indigo-600 text-base">OMR {totalPrice.toFixed(2)}</span>
                </div>
              )}
            </div>

            {bookingState === 'error' && (
              <div className="mb-4 p-3 rounded-xl bg-red-50 border border-red-100 text-red-600 text-sm">
                {bookingError}
              </div>
            )}

            {bookingState === 'confirming' && member && (
              <div className="mb-4 p-3 rounded-xl bg-indigo-50 border border-indigo-100 text-sm text-indigo-800">
                Booking as <span className="font-semibold">{member.name}</span> ({member.phone})
              </div>
            )}

            <div className="flex gap-2">
              {(bookingState === 'confirming' || bookingState === 'error') && (
                <button
                  onClick={resetBooking}
                  className="flex-1 py-3 rounded-xl border border-gray-200 text-gray-600 font-medium text-sm hover:bg-gray-50 transition-colors"
                >
                  Back
                </button>
              )}
              <button
                onClick={handleBook}
                disabled={bookingState === 'booking'}
                className="flex-1 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60 disabled:cursor-not-allowed text-white font-semibold text-sm transition-colors shadow-sm"
              >
                {bookingState === 'booking'
                  ? 'Booking…'
                  : bookingState === 'confirming'
                  ? 'Confirm booking'
                  : !member
                  ? 'Sign in to book'
                  : 'Book now'}
              </button>
            </div>
          </section>
        )}

        {/* Success state */}
        {bookingState === 'success' && selectedCourt && selectedStartTime && (
          <section className="bg-white rounded-2xl border-2 border-green-200 shadow-md p-6 mb-6 text-center">
            <div className="w-14 h-14 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-4">
              <svg className="w-7 h-7 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-1">You&apos;re booked!</h3>
            <p className="text-gray-500 text-sm mb-1">{selectedCourt.name} · {formatDateDisplay(selectedDate)}</p>
            <p className="text-gray-500 text-sm mb-4">{selectedStartTime} – {endTime}</p>
            {totalPrice > 0 && (
              <p className="text-indigo-600 font-bold mb-4">OMR {totalPrice.toFixed(2)}</p>
            )}
            <div className="flex gap-2">
              <button
                onClick={() => {
                  setSelectedStartTime(null)
                  setBookingState('idle')
                  setSelectedCourtId(null)
                  loadAvailability()
                }}
                className="flex-1 py-2.5 rounded-xl border border-gray-200 text-gray-600 font-medium text-sm hover:bg-gray-50 transition-colors"
              >
                Book another
              </button>
              <Link
                href="/account"
                className="flex-1 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm text-center transition-colors"
              >
                My bookings
              </Link>
            </div>
          </section>
        )}
      </main>
    </div>
  )
}
