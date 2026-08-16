'use client'

import { useState } from 'react'

type SyncResult = {
  ok: boolean
  fetched?: number
  imported?: number
  skipped?: number
  dateFrom?: string
  dateTo?: string
  error?: string
}

function todayStr() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}
function monthStartStr() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-01`
}

export default function MatchPointSync() {
  const [open, setOpen] = useState(false)
  const [dateFrom, setDateFrom] = useState(monthStartStr)
  const [dateTo, setDateTo] = useState(todayStr)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<SyncResult | null>(null)

  async function handleSync() {
    setLoading(true)
    setResult(null)
    try {
      const res = await fetch('/api/matchpoint/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dateFrom, dateTo }),
      })
      const data: SyncResult = await res.json()
      setResult(data)
    } catch {
      setResult({ ok: false, error: 'Network error' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg bg-surface-2 hover:bg-surface-3 text-cream/90 hover:text-cream transition-colors"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        MatchPoint Sync
      </button>

      {open && (
        <div className="absolute right-0 top-10 z-50 w-80 bg-surface border border-hair rounded-xl shadow-2xl p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-cream">Sync from MatchPoint</h3>
            <button onClick={() => setOpen(false)} className="text-faint hover:text-cream/90">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div className="space-y-2 mb-4">
            <div>
              <label className="text-xs text-warm mb-1 block">From</label>
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="w-full bg-surface-2 border border-hair rounded-lg px-3 py-1.5 text-sm text-cream focus:outline-none focus:border-ember"
              />
            </div>
            <div>
              <label className="text-xs text-warm mb-1 block">To</label>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="w-full bg-surface-2 border border-hair rounded-lg px-3 py-1.5 text-sm text-cream focus:outline-none focus:border-ember"
              />
            </div>
          </div>

          <button
            onClick={handleSync}
            disabled={loading}
            className="w-full py-2 rounded-lg bg-ember hover:bg-ember-deep disabled:opacity-50 disabled:cursor-not-allowed text-ink text-sm font-medium transition-colors"
          >
            {loading ? 'Syncing…' : 'Import Bookings'}
          </button>

          {result && (
            <div className={`mt-3 p-3 rounded-lg text-xs ${result.ok ? 'bg-green-900/40 text-green-300' : 'bg-red-900/40 text-red-300'}`}>
              {result.ok ? (
                <>
                  <p className="font-semibold mb-1">Sync complete</p>
                  <p>Fetched: {result.fetched} · Imported: {result.imported} · Skipped: {result.skipped}</p>
                  <p className="text-warm mt-1">{result.dateFrom} → {result.dateTo}</p>
                </>
              ) : (
                <>
                  <p className="font-semibold mb-1">Sync failed</p>
                  <p>{result.error}</p>
                </>
              )}
            </div>
          )}

          <p className="mt-3 text-xs text-faint/70">
            Pulls bookings from TPC-MatchPoint and imports new ones into the local database.
          </p>
        </div>
      )}
    </div>
  )
}
