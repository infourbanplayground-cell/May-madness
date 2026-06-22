'use client'

import { useState, useEffect, useCallback } from 'react'

type Props = {
  endpoint: 'customers' | 'matches' | 'activities' | 'sales'
  title: string
  hasDateRange: boolean
}

function todayStr() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}
function monthStartStr() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-01`
}

export default function MatchPointPanel({ endpoint, title, hasDateRange }: Props) {
  const [dateFrom, setDateFrom] = useState(monthStartStr)
  const [dateTo, setDateTo] = useState(todayStr)
  const [data, setData] = useState<Record<string, unknown>[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [columns, setColumns] = useState<string[]>([])

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams({ endpoint })
      if (hasDateRange) {
        params.set('dateFrom', dateFrom)
        params.set('dateTo', dateTo)
      }
      const res = await fetch(`/api/matchpoint/raw?${params}`)
      const json = await res.json() as { ok: boolean; data?: unknown[]; error?: string }
      if (!json.ok) {
        setError(json.error ?? 'Unknown error')
        setData(null)
      } else {
        const rows = (json.data ?? []) as Record<string, unknown>[]
        setData(rows)
        if (rows.length > 0) {
          setColumns(Object.keys(rows[0]))
        }
      }
    } catch {
      setError('Network error — could not reach the server')
      setData(null)
    } finally {
      setLoading(false)
    }
  }, [endpoint, hasDateRange, dateFrom, dateTo])

  useEffect(() => { load() }, [load])

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center gap-3 px-6 py-3 border-b border-gray-800 shrink-0 flex-wrap">
        <h2 className="text-sm font-semibold text-white mr-2">{title}</h2>

        {hasDateRange && (
          <>
            <div className="flex items-center gap-2">
              <label className="text-xs text-gray-400">From</label>
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-indigo-500"
              />
            </div>
            <div className="flex items-center gap-2">
              <label className="text-xs text-gray-400">To</label>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-indigo-500"
              />
            </div>
          </>
        )}

        <button
          onClick={load}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm font-medium transition-colors"
        >
          <svg className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          {loading ? 'Loading…' : 'Refresh'}
        </button>

        {data && (
          <span className="ml-auto text-xs text-gray-500">{data.length} records</span>
        )}
      </div>

      {/* Body */}
      <div className="flex-1 overflow-auto p-6">
        {error && (
          <div className="max-w-lg mx-auto mt-8 p-5 bg-red-900/20 border border-red-800 rounded-2xl text-center">
            <svg className="w-10 h-10 text-red-500 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <p className="text-red-400 font-semibold mb-1">MatchPoint API Error</p>
            <p className="text-red-300/70 text-sm">{error}</p>
            {error.includes('401') && (
              <p className="text-gray-500 text-xs mt-3">
                The API key may not be authorized yet. Check with MatchPoint support that the key is active and whitelisted.
              </p>
            )}
          </div>
        )}

        {loading && !data && (
          <div className="flex items-center justify-center h-48 text-gray-500 text-sm">
            <svg className="w-5 h-5 animate-spin mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Loading {title.toLowerCase()}…
          </div>
        )}

        {data && data.length === 0 && (
          <div className="flex flex-col items-center justify-center h-48 text-gray-500">
            <svg className="w-10 h-10 mb-3 opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
            </svg>
            <p className="text-sm">No {title.toLowerCase()} found for this period</p>
          </div>
        )}

        {data && data.length > 0 && (
          <div className="rounded-xl border border-gray-800 overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-900 border-b border-gray-800">
                  {columns.map((col) => (
                    <th key={col} className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wide whitespace-nowrap">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.map((row, i) => (
                  <tr
                    key={i}
                    className="border-b border-gray-800/60 hover:bg-gray-900/40 transition-colors"
                  >
                    {columns.map((col) => {
                      const val = row[col]
                      const display = val === null || val === undefined
                        ? <span className="text-gray-600">—</span>
                        : typeof val === 'object'
                        ? <span className="text-gray-500 italic text-xs">{JSON.stringify(val)}</span>
                        : <span className={typeof val === 'boolean' ? (val ? 'text-green-400' : 'text-gray-500') : 'text-gray-200'}>
                            {String(val)}
                          </span>
                      return (
                        <td key={col} className="px-4 py-3 whitespace-nowrap max-w-[200px] overflow-hidden text-ellipsis">
                          {display}
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
