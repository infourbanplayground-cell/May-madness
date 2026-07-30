'use client'

import { useState, useEffect, useCallback } from 'react'
import { RefreshCw, Download, Check, ClipboardCheck, Undo2 } from 'lucide-react'
import { Booking } from '@/lib/types'

type PendingBooking = Booking & { courtName: string }

function formatDate(dateStr: string): string {
  const [y, m, d] = dateStr.split('-').map(Number)
  return new Date(y, m - 1, d).toLocaleDateString('en-GB', {
    weekday: 'short', day: 'numeric', month: 'short',
  })
}

export default function PendingEntry({ onCountChange }: { onCountChange?: (n: number) => void }) {
  const [rows, setRows] = useState<PendingBooking[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [busyId, setBusyId] = useState<string | null>(null)
  const [justDone, setJustDone] = useState<PendingBooking | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch('/api/admin/pending')
      const json = await res.json()
      if (!json.ok) throw new Error(json.error ?? 'Failed to load')
      setRows(json.bookings)
      onCountChange?.(json.count)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Network error')
    } finally {
      setLoading(false)
    }
  }, [onCountChange])

  useEffect(() => { load() }, [load])

  async function mark(b: PendingBooking, synced: boolean) {
    setBusyId(b.id)
    try {
      const res = await fetch('/api/admin/pending', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: b.id, synced }),
      })
      if (!res.ok) throw new Error('Update failed')
      if (synced) setJustDone(b)
      await load()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Update failed')
    } finally {
      setBusyId(null)
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center gap-3 px-6 py-3 border-b border-gray-800 shrink-0 flex-wrap">
        <div>
          <h2 className="text-sm font-semibold text-white">To enter in MatchPoint</h2>
          <p className="text-xs text-gray-500">
            Bookings taken here that still need keying into MatchPoint by hand
          </p>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <a
            href="/api/admin/pending/export"
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              rows.length
                ? 'bg-gray-800 hover:bg-gray-700 text-gray-200'
                : 'bg-gray-900 text-gray-600 pointer-events-none'
            }`}
          >
            <Download size={14} /> CSV
          </a>
          <button
            onClick={load}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm font-medium transition-colors"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-auto p-6">
        {error && (
          <div className="mb-4 p-3 rounded-xl bg-red-900/30 border border-red-800 text-red-400 text-sm">
            {error}
          </div>
        )}

        {justDone && (
          <div className="mb-4 flex items-center gap-3 p-3 rounded-xl bg-green-900/25 border border-green-800/60 text-sm">
            <Check size={16} className="text-green-400 shrink-0" />
            <span className="text-green-300">
              Marked <span className="font-semibold">{justDone.playerName}</span> ({formatDate(justDone.date)}{' '}
              {justDone.startTime}) as entered.
            </span>
            <button
              onClick={() => { mark(justDone, false); setJustDone(null) }}
              className="ml-auto flex items-center gap-1 text-xs text-gray-400 hover:text-white"
            >
              <Undo2 size={12} /> Undo
            </button>
          </div>
        )}

        {loading && !rows.length && (
          <div className="flex items-center justify-center h-40 text-gray-500 text-sm gap-2">
            <RefreshCw size={16} className="animate-spin" /> Loading…
          </div>
        )}

        {!loading && rows.length === 0 && !error && (
          <div className="flex flex-col items-center justify-center h-56 text-center">
            <div className="w-14 h-14 rounded-full bg-green-900/30 flex items-center justify-center mb-4">
              <ClipboardCheck size={26} className="text-green-400" />
            </div>
            <p className="text-white font-semibold mb-1">Nothing waiting</p>
            <p className="text-sm text-gray-500 max-w-xs">
              Every booking taken in this app has been entered into MatchPoint.
            </p>
          </div>
        )}

        {rows.length > 0 && (
          <>
            <p className="text-xs text-gray-500 mb-3">
              {rows.length} booking{rows.length === 1 ? '' : 's'} waiting. Enter each one in MatchPoint,
              then tick it off here.
            </p>
            <div className="space-y-2">
              {rows.map((b) => (
                <div
                  key={b.id}
                  className="flex items-center gap-4 bg-gray-900 border border-gray-800 rounded-xl px-4 py-3"
                >
                  <div className="text-center shrink-0 w-16">
                    <p className="text-[11px] text-gray-500">{formatDate(b.date)}</p>
                    <p className="text-sm font-bold text-white tabular-nums">{b.startTime}</p>
                  </div>

                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-semibold text-white truncate">{b.playerName}</p>
                    <p className="text-xs text-gray-400 truncate">
                      {b.courtName} · {b.startTime}–{b.endTime}
                      {b.playerPhone && <> · {b.playerPhone}</>}
                    </p>
                  </div>

                  <span
                    className={`text-[10px] px-2 py-0.5 rounded-full shrink-0 ${
                      b.bookingSource === 'member'
                        ? 'bg-indigo-900/50 text-indigo-300'
                        : 'bg-gray-800 text-gray-400'
                    }`}
                  >
                    {b.bookingSource === 'member' ? 'Online' : 'Front desk'}
                  </span>

                  {b.priceTotal != null && b.priceTotal > 0 && (
                    <span className="text-xs text-gray-400 tabular-nums shrink-0">
                      OMR {b.priceTotal.toFixed(2)}
                    </span>
                  )}

                  <button
                    onClick={() => mark(b, true)}
                    disabled={busyId === b.id}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-green-600 hover:bg-green-500 disabled:opacity-50 text-white text-xs font-semibold transition-colors shrink-0"
                  >
                    <Check size={13} />
                    {busyId === b.id ? 'Saving…' : 'Entered'}
                  </button>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
