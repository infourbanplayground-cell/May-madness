'use client'

import { useState, useEffect, useCallback } from 'react'
import { format, addDays, subDays, parseISO } from 'date-fns'
import { ChevronLeft, ChevronRight, Plus, X, FileText, RefreshCw, DollarSign } from 'lucide-react'
import { Court, Booking } from '@/lib/types'
import { TIME_SLOTS } from '@/lib/constants'
import CustomerSearch from '@/components/CustomerSearch'

const COURTS: Court[] = [
  { id: 'court-1', name: 'Court 1', sport: 'Padel', color: '#6366f1' },
  { id: 'court-2', name: 'Court 2', sport: 'Padel', color: '#10b981' },
  { id: 'court-3', name: 'Court 3', sport: 'Pickleball', color: '#f59e0b' },
  { id: 'court-4', name: 'Court 4', sport: 'Pickleball', color: '#ef4444' },
]

const DAY_NAMES = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

function timeToMinutes(t: string) {
  const [h, m] = t.split(':').map(Number)
  return h * 60 + m
}

function addMinutes(t: string, mins: number) {
  const total = timeToMinutes(t) + mins
  const h = Math.floor(total / 60).toString().padStart(2, '0')
  const m = (total % 60).toString().padStart(2, '0')
  return `${h}:${m}`
}

type SlotSelection = { courtId: string; startTime: string } | null

export default function BookingCalendar() {
  const [activeTab, setActiveTab] = useState<'calendar' | 'pricing'>('calendar')
  const [selectedDate, setSelectedDate] = useState(new Date())
  const [bookings, setBookings] = useState<Booking[]>([])
  const [slotSelection, setSlotSelection] = useState<SlotSelection>(null)
  const [showModal, setShowModal] = useState(false)
  const [detailBooking, setDetailBooking] = useState<Booking | null>(null)
  const [loading, setLoading] = useState(false)

  const dateStr = format(selectedDate, 'yyyy-MM-dd')

  const fetchBookings = useCallback(async () => {
    const res = await fetch(`/api/bookings?date=${dateStr}`)
    const data = await res.json()
    setBookings(data)
  }, [dateStr])

  useEffect(() => { fetchBookings() }, [fetchBookings])

  function getBookingForSlot(courtId: string, time: string): Booking | null {
    return bookings.find((b) => {
      if (b.courtId !== courtId) return false
      const start = timeToMinutes(b.startTime)
      const end = timeToMinutes(b.endTime)
      const slot = timeToMinutes(time)
      return slot >= start && slot < end
    }) ?? null
  }

  function isSlotStart(booking: Booking, time: string) {
    return booking.startTime === time
  }

  function slotSpan(booking: Booking) {
    return (timeToMinutes(booking.endTime) - timeToMinutes(booking.startTime)) / 30
  }

  async function handleCancel(id: string) {
    await fetch(`/api/bookings/${id}`, { method: 'DELETE' })
    setDetailBooking(null)
    fetchBookings()
  }

  return (
    <div className="flex flex-col h-full">
      {/* Tab bar */}
      <div className="flex border-b border-hair px-6 pt-3 gap-4">
        <button
          onClick={() => setActiveTab('calendar')}
          className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'calendar'
              ? 'border-ember text-cream'
              : 'border-transparent text-warm hover:text-cream/90'
          }`}
        >
          Calendar
        </button>
        <button
          onClick={() => setActiveTab('pricing')}
          className={`pb-3 text-sm font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
            activeTab === 'pricing'
              ? 'border-ember text-cream'
              : 'border-transparent text-warm hover:text-cream/90'
          }`}
        >
          <DollarSign size={14} />
          Pricing
        </button>
      </div>

      {/* Pricing tab */}
      {activeTab === 'pricing' && <PricingPanel />}

      {/* Calendar tab */}
      {activeTab === 'calendar' && <>

      {/* Date navigation */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-hair">
        <button
          onClick={() => setSelectedDate((d) => subDays(d, 1))}
          className="p-2 rounded-lg hover:bg-surface-2 text-warm hover:text-cream transition-colors"
        >
          <ChevronLeft size={20} />
        </button>

        <div className="text-center">
          <div className="text-xl font-bold text-cream">
            {format(selectedDate, 'EEEE, MMMM d')}
          </div>
          <div className="text-sm text-warm">{format(selectedDate, 'yyyy')}</div>
        </div>

        <button
          onClick={() => setSelectedDate((d) => addDays(d, 1))}
          className="p-2 rounded-lg hover:bg-surface-2 text-warm hover:text-cream transition-colors"
        >
          <ChevronRight size={20} />
        </button>
      </div>

      {/* Week strip */}
      <div className="flex px-6 py-3 gap-2 border-b border-hair overflow-x-auto">
        {Array.from({ length: 7 }, (_, i) => {
          const d = addDays(subDays(selectedDate, 3), i)
          const isToday = format(d, 'yyyy-MM-dd') === format(new Date(), 'yyyy-MM-dd')
          const isSelected = format(d, 'yyyy-MM-dd') === dateStr
          return (
            <button
              key={i}
              onClick={() => setSelectedDate(d)}
              className={`flex flex-col items-center px-3 py-2 rounded-xl min-w-[52px] transition-colors ${
                isSelected
                  ? 'bg-ember text-cream'
                  : isToday
                  ? 'bg-surface-2 text-ember'
                  : 'text-warm hover:bg-surface-2 hover:text-cream'
              }`}
            >
              <span className="text-xs font-medium">{DAY_NAMES[d.getDay()]}</span>
              <span className="text-lg font-bold">{format(d, 'd')}</span>
            </button>
          )
        })}
      </div>

      {/* Calendar grid */}
      <div className="flex-1 overflow-auto">
        <div className="min-w-[600px]">
          {/* Court headers */}
          <div className="flex sticky top-0 z-10 bg-ink border-b border-hair">
            <div className="w-16 shrink-0" />
            {COURTS.map((court) => (
              <div
                key={court.id}
                className="flex-1 text-center py-3 border-l border-hair"
              >
                <div className="text-sm font-bold text-cream">{court.name}</div>
                <div
                  className="text-xs font-medium mt-0.5"
                  style={{ color: court.color }}
                >
                  {court.sport}
                </div>
              </div>
            ))}
          </div>

          {/* Time rows */}
          {TIME_SLOTS.map((time) => (
            <div key={time} className="flex border-b border-hair-soft h-12">
              <div className="w-16 shrink-0 flex items-center justify-center">
                <span className="text-xs text-faint">{time}</span>
              </div>

              {COURTS.map((court) => {
                const booking = getBookingForSlot(court.id, time)
                const isStart = booking && isSlotStart(booking, time)

                return (
                  <div
                    key={court.id}
                    className="flex-1 border-l border-hair-soft relative"
                  >
                    {isStart && booking ? (
                      <button
                        onClick={() => setDetailBooking(booking)}
                        className="absolute inset-x-1 top-0.5 rounded-md text-cream text-xs font-semibold px-2 py-1 text-left overflow-hidden z-10 hover:brightness-110 transition-all"
                        style={{
                          backgroundColor: court.color,
                          height: `${slotSpan(booking) * 48 - 4}px`,
                        }}
                      >
                        <div className="truncate">{booking.playerName}</div>
                        <div className="opacity-80 text-[10px]">
                          {booking.startTime} – {booking.endTime}
                        </div>
                        {booking.isRecurring && (
                          <RefreshCw size={10} className="absolute top-1 right-1 opacity-70" />
                        )}
                      </button>
                    ) : !booking ? (
                      <button
                        onClick={() => {
                          setSlotSelection({ courtId: court.id, startTime: time })
                          setShowModal(true)
                        }}
                        className="absolute inset-0 hover:bg-surface-2/60 transition-colors group"
                      >
                        <Plus
                          size={14}
                          className="absolute inset-0 m-auto text-faint/70 opacity-0 group-hover:opacity-100 transition-opacity"
                        />
                      </button>
                    ) : null}
                  </div>
                )
              })}
            </div>
          ))}
        </div>
      </div>

      {/* Add booking modal */}
      {showModal && slotSelection && (
        <BookingModal
          courtId={slotSelection.courtId}
          date={dateStr}
          startTime={slotSelection.startTime}
          onClose={() => { setShowModal(false); setSlotSelection(null) }}
          onSaved={() => { setShowModal(false); setSlotSelection(null); fetchBookings() }}
        />
      )}

      {/* Booking detail drawer */}
      {detailBooking && (
        <BookingDetail
          booking={detailBooking}
          court={COURTS.find((c) => c.id === detailBooking.courtId)!}
          onClose={() => setDetailBooking(null)}
          onCancel={handleCancel}
        />
      )}

      </> /* end calendar tab */}
    </div>
  )
}

// ─── Pricing Panel ────────────────────────────────────────────────────────────

function PricingPanel() {
  const [prices, setPrices] = useState<Record<string, string>>({})
  const [saving, setSaving] = useState<string | null>(null)
  const [saved, setSaved] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch('/api/courts/prices')
      .then((r) => r.json())
      .then((data: Record<string, number>) => {
        const strPrices: Record<string, string> = {}
        for (const court of COURTS) {
          strPrices[court.id] = data[court.id] !== undefined ? String(data[court.id]) : '0'
        }
        setPrices(strPrices)
      })
      .catch(() => {
        const strPrices: Record<string, string> = {}
        for (const court of COURTS) strPrices[court.id] = '0'
        setPrices(strPrices)
      })
  }, [])

  async function handleSave(courtId: string) {
    const price = parseFloat(prices[courtId] ?? '0')
    if (isNaN(price) || price < 0) {
      setError('Price must be a non-negative number')
      return
    }
    setSaving(courtId)
    setError(null)
    try {
      const res = await fetch('/api/admin/prices', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ courtId, pricePerHour: price }),
      })
      if (!res.ok) {
        const d = await res.json()
        setError(d.error || 'Failed to save')
      } else {
        setSaved(courtId)
        setTimeout(() => setSaved(null), 2000)
      }
    } catch {
      setError('Network error')
    } finally {
      setSaving(null)
    }
  }

  return (
    <div className="flex-1 overflow-auto p-6">
      <div className="max-w-md">
        <h2 className="text-lg font-bold text-cream mb-1">Court Pricing</h2>
        <p className="text-sm text-warm mb-6">Set per-hour rates shown to members on the booking page.</p>

        {error && (
          <div className="mb-4 p-3 rounded-xl bg-red-900/30 border border-red-800 text-red-400 text-sm">
            {error}
          </div>
        )}

        <div className="space-y-3">
          {COURTS.map((court) => (
            <div key={court.id} className="bg-surface rounded-xl border border-hair p-4">
              <div className="flex items-center gap-3 mb-3">
                <div
                  className="w-3 h-3 rounded-full shrink-0"
                  style={{ backgroundColor: court.color }}
                />
                <div>
                  <p className="font-medium text-cream text-sm">{court.name}</p>
                  <p className="text-xs text-warm">{court.sport}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-1.5 flex-1 bg-surface-2 rounded-lg border border-hair px-3 py-2 focus-within:ring-2 focus-within:ring-indigo-500">
                  <span className="text-warm text-sm">OMR</span>
                  <input
                    type="number"
                    min="0"
                    step="0.25"
                    value={prices[court.id] ?? ''}
                    onChange={(e) => setPrices((p) => ({ ...p, [court.id]: e.target.value }))}
                    placeholder="0.00"
                    className="flex-1 bg-transparent text-cream text-sm focus:outline-none"
                  />
                  <span className="text-warm text-xs">/hr</span>
                </div>
                <button
                  onClick={() => handleSave(court.id)}
                  disabled={saving === court.id}
                  className="px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50 bg-ember hover:bg-ember-deep text-ink"
                >
                  {saving === court.id ? 'Saving…' : saved === court.id ? 'Saved!' : 'Save'}
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// ─── Booking Modal ────────────────────────────────────────────────────────────

type ModalProps = {
  courtId: string
  date: string
  startTime: string
  onClose: () => void
  onSaved: () => void
}

function BookingModal({ courtId, date, startTime, onClose, onSaved }: ModalProps) {
  const court = COURTS.find((c) => c.id === courtId)!
  const [playerName, setPlayerName] = useState('')
  const [playerPhone, setPlayerPhone] = useState('')
  const [notes, setNotes] = useState('')
  const [duration, setDuration] = useState(60)
  const [isRecurring, setIsRecurring] = useState(false)
  const [recurringDays, setRecurringDays] = useState<number[]>([])
  const [recurringUntil, setRecurringUntil] = useState('')
  const [saving, setSaving] = useState(false)

  const endTime = addMinutes(startTime, duration)

  function toggleDay(day: number) {
    setRecurringDays((prev) =>
      prev.includes(day) ? prev.filter((d) => d !== day) : [...prev, day]
    )
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault()
    if (!playerName.trim()) return
    setSaving(true)

    await fetch('/api/bookings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        courtId,
        date,
        startTime,
        endTime,
        playerName,
        playerPhone,
        notes,
        isRecurring,
        recurringDays: isRecurring ? recurringDays : undefined,
        recurringUntil: isRecurring ? recurringUntil : undefined,
      }),
    })

    onSaved()
  }

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 px-4">
      <div className="bg-surface rounded-2xl w-full max-w-md border border-hair shadow-2xl">
        <div className="flex items-center justify-between px-6 py-4 border-b border-hair">
          <div>
            <h2 className="font-bold text-cream">New Booking</h2>
            <p className="text-sm text-warm">
              <span style={{ color: court.color }}>{court.name}</span> · {date} · {startTime} – {endTime}
            </p>
          </div>
          <button onClick={onClose} className="text-warm hover:text-cream">
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSave} className="p-6 space-y-4">
          <div>
            <label className="block text-xs font-medium text-warm mb-1">Duration</label>
            <div className="flex gap-2">
              {[30, 60, 90, 120].map((d) => (
                <button
                  key={d}
                  type="button"
                  onClick={() => setDuration(d)}
                  className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${
                    duration === d
                      ? 'bg-ember text-cream'
                      : 'bg-surface-2 text-cream/90 hover:bg-surface-2'
                  }`}
                >
                  {d}m
                </button>
              ))}
            </div>
          </div>

          <CustomerSearch
            name={playerName}
            phone={playerPhone}
            onChange={({ name, phone }) => { setPlayerName(name); setPlayerPhone(phone) }}
          />

          <div>
            <label className="flex items-center gap-2 text-xs font-medium text-warm mb-1">
              <FileText size={14} /> Notes
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Equipment, special requests…"
              rows={2}
              className="w-full bg-surface-2 border border-hair rounded-lg px-4 py-2.5 text-cream placeholder-faint/60 focus:outline-none focus:ring-2 focus:ring-ember resize-none"
            />
          </div>

          <div>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={isRecurring}
                onChange={(e) => setIsRecurring(e.target.checked)}
                className="rounded accent-indigo-600"
              />
              <span className="text-sm text-cream/90 flex items-center gap-1.5">
                <RefreshCw size={14} /> Recurring booking
              </span>
            </label>
          </div>

          {isRecurring && (
            <div className="bg-surface-2 rounded-xl p-4 space-y-3">
              <div>
                <label className="block text-xs font-medium text-warm mb-2">Repeat on</label>
                <div className="flex gap-1.5">
                  {DAY_NAMES.map((day, i) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() => toggleDay(i)}
                      className={`w-9 h-9 rounded-lg text-xs font-semibold transition-colors ${
                        recurringDays.includes(i)
                          ? 'bg-ember text-cream'
                          : 'bg-gray-700 text-warm hover:bg-gray-600'
                      }`}
                    >
                      {day}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-warm mb-1">Repeat until</label>
                <input
                  type="date"
                  value={recurringUntil}
                  onChange={(e) => setRecurringUntil(e.target.value)}
                  min={date}
                  required={isRecurring}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-cream focus:outline-none focus:ring-2 focus:ring-ember"
                />
              </div>
            </div>
          )}

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2.5 rounded-lg bg-surface-2 text-cream/90 hover:bg-surface-2 font-medium transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex-1 py-2.5 rounded-lg bg-ember hover:bg-ember-deep disabled:opacity-50 text-ink font-semibold transition-colors"
            >
              {saving ? 'Saving…' : 'Book'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ─── Booking Detail ───────────────────────────────────────────────────────────

type DetailProps = {
  booking: Booking
  court: Court
  onClose: () => void
  onCancel: (id: string) => void
}

function BookingDetail({ booking, court, onClose, onCancel }: DetailProps) {
  const [confirming, setConfirming] = useState(false)

  return (
    <div className="fixed inset-0 bg-black/70 flex items-end sm:items-center justify-center z-50 px-4 pb-4 sm:pb-0">
      <div className="bg-surface rounded-2xl w-full max-w-sm border border-hair shadow-2xl">
        <div
          className="h-2 rounded-t-2xl"
          style={{ backgroundColor: court.color }}
        />
        <div className="px-6 py-4">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h2 className="font-bold text-cream text-lg">{booking.playerName}</h2>
              <p className="text-sm" style={{ color: court.color }}>
                {court.name} · {court.sport}
              </p>
            </div>
            <button onClick={onClose} className="text-warm hover:text-cream mt-0.5">
              <X size={20} />
            </button>
          </div>

          <div className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-warm">Date</span>
              <span className="text-cream">{booking.date}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-warm">Time</span>
              <span className="text-cream">{booking.startTime} – {booking.endTime}</span>
            </div>
            {booking.playerPhone && (
              <div className="flex justify-between">
                <span className="text-warm">Phone</span>
                <span className="text-cream">{booking.playerPhone}</span>
              </div>
            )}
            {booking.notes && (
              <div className="flex justify-between">
                <span className="text-warm">Notes</span>
                <span className="text-cream text-right max-w-[60%]">{booking.notes}</span>
              </div>
            )}
            {booking.isRecurring && (
              <div className="flex justify-between">
                <span className="text-warm">Recurring</span>
                <span className="text-ember flex items-center gap-1">
                  <RefreshCw size={12} /> Yes
                </span>
              </div>
            )}
          </div>

          <div className="mt-6">
            {!confirming ? (
              <button
                onClick={() => setConfirming(true)}
                className="w-full py-2.5 rounded-lg bg-red-900/40 hover:bg-red-900/60 text-red-400 font-medium transition-colors"
              >
                Cancel booking
              </button>
            ) : (
              <div className="space-y-2">
                <p className="text-center text-sm text-warm">Are you sure?</p>
                <div className="flex gap-2">
                  <button
                    onClick={() => setConfirming(false)}
                    className="flex-1 py-2.5 rounded-lg bg-surface-2 text-cream/90 hover:bg-surface-2 font-medium transition-colors"
                  >
                    Keep
                  </button>
                  <button
                    onClick={() => onCancel(booking.id)}
                    className="flex-1 py-2.5 rounded-lg bg-red-600 hover:bg-red-500 text-cream font-semibold transition-colors"
                  >
                    Yes, cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
