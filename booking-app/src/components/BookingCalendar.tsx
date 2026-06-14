'use client'

import { useState, useEffect, useCallback } from 'react'
import { format, addDays, subDays, parseISO } from 'date-fns'
import { ChevronLeft, ChevronRight, Plus, X, Phone, User, FileText, RefreshCw } from 'lucide-react'
import { Court, Booking } from '@/lib/types'
import { TIME_SLOTS } from '@/lib/store'

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
      {/* Date navigation */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
        <button
          onClick={() => setSelectedDate((d) => subDays(d, 1))}
          className="p-2 rounded-lg hover:bg-gray-800 text-gray-400 hover:text-white transition-colors"
        >
          <ChevronLeft size={20} />
        </button>

        <div className="text-center">
          <div className="text-xl font-bold text-white">
            {format(selectedDate, 'EEEE, MMMM d')}
          </div>
          <div className="text-sm text-gray-400">{format(selectedDate, 'yyyy')}</div>
        </div>

        <button
          onClick={() => setSelectedDate((d) => addDays(d, 1))}
          className="p-2 rounded-lg hover:bg-gray-800 text-gray-400 hover:text-white transition-colors"
        >
          <ChevronRight size={20} />
        </button>
      </div>

      {/* Week strip */}
      <div className="flex px-6 py-3 gap-2 border-b border-gray-800 overflow-x-auto">
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
                  ? 'bg-indigo-600 text-white'
                  : isToday
                  ? 'bg-gray-800 text-indigo-400'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-white'
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
          <div className="flex sticky top-0 z-10 bg-gray-950 border-b border-gray-800">
            <div className="w-16 shrink-0" />
            {COURTS.map((court) => (
              <div
                key={court.id}
                className="flex-1 text-center py-3 border-l border-gray-800"
              >
                <div className="text-sm font-bold text-white">{court.name}</div>
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
            <div key={time} className="flex border-b border-gray-800/50 h-12">
              <div className="w-16 shrink-0 flex items-center justify-center">
                <span className="text-xs text-gray-500">{time}</span>
              </div>

              {COURTS.map((court) => {
                const booking = getBookingForSlot(court.id, time)
                const isStart = booking && isSlotStart(booking, time)

                return (
                  <div
                    key={court.id}
                    className="flex-1 border-l border-gray-800/50 relative"
                  >
                    {isStart && booking ? (
                      <button
                        onClick={() => setDetailBooking(booking)}
                        className="absolute inset-x-1 top-0.5 rounded-md text-white text-xs font-semibold px-2 py-1 text-left overflow-hidden z-10 hover:brightness-110 transition-all"
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
                        className="absolute inset-0 hover:bg-gray-800/60 transition-colors group"
                      >
                        <Plus
                          size={14}
                          className="absolute inset-0 m-auto text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity"
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
      <div className="bg-gray-900 rounded-2xl w-full max-w-md border border-gray-800 shadow-2xl">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
          <div>
            <h2 className="font-bold text-white">New Booking</h2>
            <p className="text-sm text-gray-400">
              <span style={{ color: court.color }}>{court.name}</span> · {date} · {startTime} – {endTime}
            </p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSave} className="p-6 space-y-4">
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1">Duration</label>
            <div className="flex gap-2">
              {[30, 60, 90, 120].map((d) => (
                <button
                  key={d}
                  type="button"
                  onClick={() => setDuration(d)}
                  className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${
                    duration === d
                      ? 'bg-indigo-600 text-white'
                      : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                  }`}
                >
                  {d}m
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="flex items-center gap-2 text-xs font-medium text-gray-400 mb-1">
              <User size={14} /> Player Name *
            </label>
            <input
              value={playerName}
              onChange={(e) => setPlayerName(e.target.value)}
              required
              placeholder="Full name"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div>
            <label className="flex items-center gap-2 text-xs font-medium text-gray-400 mb-1">
              <Phone size={14} /> Phone
            </label>
            <input
              value={playerPhone}
              onChange={(e) => setPlayerPhone(e.target.value)}
              placeholder="+1 (555) 000-0000"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div>
            <label className="flex items-center gap-2 text-xs font-medium text-gray-400 mb-1">
              <FileText size={14} /> Notes
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Equipment, special requests…"
              rows={2}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
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
              <span className="text-sm text-gray-300 flex items-center gap-1.5">
                <RefreshCw size={14} /> Recurring booking
              </span>
            </label>
          </div>

          {isRecurring && (
            <div className="bg-gray-800 rounded-xl p-4 space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-400 mb-2">Repeat on</label>
                <div className="flex gap-1.5">
                  {DAY_NAMES.map((day, i) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() => toggleDay(i)}
                      className={`w-9 h-9 rounded-lg text-xs font-semibold transition-colors ${
                        recurringDays.includes(i)
                          ? 'bg-indigo-600 text-white'
                          : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
                      }`}
                    >
                      {day}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1">Repeat until</label>
                <input
                  type="date"
                  value={recurringUntil}
                  onChange={(e) => setRecurringUntil(e.target.value)}
                  min={date}
                  required={isRecurring}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>
          )}

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2.5 rounded-lg bg-gray-800 text-gray-300 hover:bg-gray-700 font-medium transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex-1 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold transition-colors"
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
      <div className="bg-gray-900 rounded-2xl w-full max-w-sm border border-gray-800 shadow-2xl">
        <div
          className="h-2 rounded-t-2xl"
          style={{ backgroundColor: court.color }}
        />
        <div className="px-6 py-4">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h2 className="font-bold text-white text-lg">{booking.playerName}</h2>
              <p className="text-sm" style={{ color: court.color }}>
                {court.name} · {court.sport}
              </p>
            </div>
            <button onClick={onClose} className="text-gray-400 hover:text-white mt-0.5">
              <X size={20} />
            </button>
          </div>

          <div className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-400">Date</span>
              <span className="text-white">{booking.date}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Time</span>
              <span className="text-white">{booking.startTime} – {booking.endTime}</span>
            </div>
            {booking.playerPhone && (
              <div className="flex justify-between">
                <span className="text-gray-400">Phone</span>
                <span className="text-white">{booking.playerPhone}</span>
              </div>
            )}
            {booking.notes && (
              <div className="flex justify-between">
                <span className="text-gray-400">Notes</span>
                <span className="text-white text-right max-w-[60%]">{booking.notes}</span>
              </div>
            )}
            {booking.isRecurring && (
              <div className="flex justify-between">
                <span className="text-gray-400">Recurring</span>
                <span className="text-indigo-400 flex items-center gap-1">
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
                <p className="text-center text-sm text-gray-400">Are you sure?</p>
                <div className="flex gap-2">
                  <button
                    onClick={() => setConfirming(false)}
                    className="flex-1 py-2.5 rounded-lg bg-gray-800 text-gray-300 hover:bg-gray-700 font-medium transition-colors"
                  >
                    Keep
                  </button>
                  <button
                    onClick={() => onCancel(booking.id)}
                    className="flex-1 py-2.5 rounded-lg bg-red-600 hover:bg-red-500 text-white font-semibold transition-colors"
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
