'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Emblem } from '@/components/Brand'
import { formatTime } from '@/lib/time'
import { Member, Booking } from '@/lib/types'

const COURT_COLORS: Record<string, string> = {
  'court-1': '#FF8A3D',
  'court-2': '#FFC24B',
  'court-3': '#33A1FF',
  'court-4': '#8DF3E8',
}

const COURT_NAMES: Record<string, string> = {
  'court-1': 'Court 1',
  'court-2': 'Court 2',
  'court-3': 'Court 3',
  'court-4': 'Court 4',
}

function formatDate(dateStr: string): string {
  const [year, month, day] = dateStr.split('-').map(Number)
  const date = new Date(year, month - 1, day)
  return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' })
}

function BookingCard({
  booking,
  onCancel,
}: {
  booking: Booking
  onCancel?: (id: string) => void
}) {
  const [confirming, setConfirming] = useState(false)
  const [cancelling, setCancelling] = useState(false)
  const color = COURT_COLORS[booking.courtId] ?? '#6366f1'
  const courtName = COURT_NAMES[booking.courtId] ?? booking.courtId

  async function handleCancel() {
    setCancelling(true)
    try {
      const res = await fetch(`/api/account/bookings/${booking.id}`, { method: 'DELETE' })
      if (res.ok) {
        onCancel?.(booking.id)
      }
    } finally {
      setCancelling(false)
      setConfirming(false)
    }
  }

  return (
    <div className="bg-surface rounded-2xl border border-hair shadow-sm overflow-hidden">
      <div className="h-1.5" style={{ backgroundColor: color }} />
      <div className="p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="font-semibold text-cream text-sm">{courtName}</span>
              {booking.status === 'cancelled' && (
                <span className="text-xs bg-flare/20 text-[#ff9a96] px-2 py-0.5 rounded-full font-medium">
                  Cancelled
                </span>
              )}
            </div>
            <p className="text-warm text-sm">{formatDate(booking.date)}</p>
            <p className="text-faint text-sm">
              {formatTime(booking.startTime)} – {formatTime(booking.endTime)}
              {booking.durationMinutes && (
                <span className="ml-1.5 text-faint">
                  ({booking.durationMinutes >= 60 ? `${booking.durationMinutes / 60}h` : `${booking.durationMinutes}m`})
                </span>
              )}
            </p>
            {booking.priceTotal != null && booking.priceTotal > 0 && (
              <p className="text-ember font-semibold text-sm mt-1">
                OMR {booking.priceTotal.toFixed(2)}
              </p>
            )}
          </div>

          {onCancel && booking.status === 'confirmed' && (
            <div className="shrink-0">
              {!confirming ? (
                <button
                  onClick={() => setConfirming(true)}
                  className="text-sm text-red-500 hover:text-red-700 font-medium transition-colors"
                >
                  Cancel
                </button>
              ) : (
                <div className="flex flex-col items-end gap-1.5">
                  <span className="text-xs text-faint">Are you sure?</span>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setConfirming(false)}
                      className="text-xs text-faint hover:text-cream/90 font-medium"
                    >
                      Keep
                    </button>
                    <button
                      onClick={handleCancel}
                      disabled={cancelling}
                      className="text-xs text-red-500 hover:text-red-700 font-semibold disabled:opacity-50"
                    >
                      {cancelling ? 'Cancelling…' : 'Yes, cancel'}
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default function AccountPage() {
  const router = useRouter()
  const [member, setMember] = useState<Member | null>(null)
  const [upcomingBookings, setUpcomingBookings] = useState<Booking[]>([])
  const [pastBookings, setPastBookings] = useState<Booking[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'upcoming' | 'past'>('upcoming')

  const fetchData = useCallback(async () => {
    const res = await fetch('/api/account/me')
    if (!res.ok) {
      router.push('/account/login')
      return
    }
    const data = await res.json()
    setMember(data.member)
    setUpcomingBookings(data.upcomingBookings)
    setPastBookings(data.pastBookings)
    setLoading(false)
  }, [router])

  useEffect(() => { fetchData() }, [fetchData])

  function handleCancelled(id: string) {
    setUpcomingBookings((prev) =>
      prev.map((b) => b.id === id ? { ...b, status: 'cancelled' as const } : b)
    )
  }

  async function handleLogout() {
    await fetch('/api/account/logout', { method: 'POST' })
    router.push('/account/login')
  }

  if (loading) {
    return (
      <div className="min-h-screen heat-bg flex items-center justify-center">
        <div className="text-faint text-sm">Loading…</div>
      </div>
    )
  }

  const confirmedUpcoming = upcomingBookings.filter((b) => b.status === 'confirmed')
  const displayUpcoming = upcomingBookings

  return (
    <div className="min-h-screen heat-bg">
      {/* Header */}
      <header className="bg-surface border-b border-hair sticky top-0 z-10">
        <div className="max-w-lg mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Link href="/book" className="flex items-center gap-2">
              <Emblem size={30} />
              <span className="h-display text-base">Urban Playground</span>
            </Link>
          </div>
          <button
            onClick={handleLogout}
            className="text-sm text-faint hover:text-cream/90 font-medium transition-colors"
          >
            Sign out
          </button>
        </div>
      </header>

      <main className="max-w-lg mx-auto px-4 py-6 space-y-6">
        {/* Member greeting */}
        <div className="bg-surface rounded-2xl border border-hair shadow-sm p-5">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-full bg-ember/15 flex items-center justify-center shrink-0">
              <span className="text-ember font-bold text-lg">
                {member?.name?.[0]?.toUpperCase() ?? '?'}
              </span>
            </div>
            <div>
              <p className="font-semibold text-cream">{member?.name}</p>
              <p className="text-sm text-faint">{member?.phone}</p>
            </div>
          </div>

          <div className="mt-4 flex gap-3">
            <div className="flex-1 bg-ember/10 rounded-xl p-3 text-center">
              <p className="text-2xl font-bold text-ember">{confirmedUpcoming.length}</p>
              <p className="text-xs text-ember font-medium mt-0.5">Upcoming</p>
            </div>
            <div className="flex-1 bg-surface-2 rounded-xl p-3 text-center">
              <p className="text-2xl font-bold text-warm">{pastBookings.length}</p>
              <p className="text-xs text-faint font-medium mt-0.5">Past</p>
            </div>
          </div>
        </div>

        {/* Book CTA */}
        <Link
          href="/book"
          className="block w-full py-3.5 rounded-xl bg-ember hover:bg-ember-deep text-ink font-semibold text-sm text-center transition-colors shadow-sm"
        >
          Book a court
        </Link>

        {/* Tabs */}
        <div className="flex bg-surface-2 rounded-xl p-1">
          <button
            onClick={() => setActiveTab('upcoming')}
            className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === 'upcoming'
                ? 'bg-surface text-cream shadow-sm'
                : 'text-faint hover:text-cream/90'
            }`}
          >
            Upcoming
            {confirmedUpcoming.length > 0 && (
              <span className="ml-1.5 bg-ember text-ink text-xs px-1.5 py-0.5 rounded-full">
                {confirmedUpcoming.length}
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTab('past')}
            className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === 'past'
                ? 'bg-surface text-cream shadow-sm'
                : 'text-faint hover:text-cream/90'
            }`}
          >
            History
          </button>
        </div>

        {/* Booking lists */}
        {activeTab === 'upcoming' && (
          <div className="space-y-3">
            {displayUpcoming.length === 0 ? (
              <div className="text-center py-12 text-faint">
                <p className="text-4xl mb-3">🎾</p>
                <p className="font-medium text-warm">No upcoming bookings</p>
                <p className="text-sm mt-1">Book a court to get started</p>
              </div>
            ) : (
              displayUpcoming.map((b) => (
                <BookingCard
                  key={b.id}
                  booking={b}
                  onCancel={b.status === 'confirmed' ? handleCancelled : undefined}
                />
              ))
            )}
          </div>
        )}

        {activeTab === 'past' && (
          <div className="space-y-3">
            {pastBookings.length === 0 ? (
              <div className="text-center py-12 text-faint">
                <p className="text-sm">No booking history yet</p>
              </div>
            ) : (
              pastBookings.map((b) => (
                <BookingCard key={b.id} booking={b} />
              ))
            )}
          </div>
        )}
      </main>
    </div>
  )
}
