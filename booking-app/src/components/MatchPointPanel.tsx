'use client'

import { useState, useEffect, useCallback, useMemo, Fragment } from 'react'
import { Search, RefreshCw, ChevronRight, AlertTriangle, Inbox } from 'lucide-react'

type Props = {
  endpoint: 'customers' | 'matches' | 'activities' | 'sales'
  title: string
  hasDateRange: boolean
}

type Row = Record<string, unknown>

function todayStr() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}
function monthStartStr() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-01`
}

function isObjectArray(v: unknown): v is Row[] {
  return Array.isArray(v) && v.length > 0 && typeof v[0] === 'object' && v[0] !== null
}

/** Mini table for nested arrays (Participants, Payments, Lines…) */
function SubTable({ rows }: { rows: Row[] }) {
  const cols = Object.keys(rows[0])
  return (
    <div className="rounded-lg border border-gray-800 overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="bg-gray-800/60">
            {cols.map((c) => (
              <th key={c} className="px-2.5 py-1.5 text-left font-semibold text-gray-400 whitespace-nowrap">{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-t border-gray-800/60">
              {cols.map((c) => (
                <td key={c} className="px-2.5 py-1.5 text-gray-300 whitespace-nowrap">
                  {r[c] === null || r[c] === undefined || r[c] === ''
                    ? '—'
                    : typeof r[c] === 'object' ? JSON.stringify(r[c]) : String(r[c])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function DetailPane({ row }: { row: Row }) {
  const scalars = Object.entries(row).filter(([, v]) => typeof v !== 'object' || v === null)
  const nested = Object.entries(row).filter(([, v]) => isObjectArray(v)) as [string, Row[]][]
  const plainObjects = Object.entries(row).filter(
    ([, v]) => typeof v === 'object' && v !== null && !Array.isArray(v)
  ) as [string, Row][]

  return (
    <div className="p-4 bg-gray-900/80 space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-3 gap-x-6 gap-y-2">
        {scalars.map(([k, v]) => (
          <div key={k} className="min-w-0">
            <p className="text-[10px] uppercase tracking-wide text-gray-500">{k}</p>
            <p className="text-sm text-gray-200 truncate">
              {v === null || v === undefined || v === '' ? '—' : String(v)}
            </p>
          </div>
        ))}
      </div>
      {plainObjects.map(([k, obj]) => (
        <div key={k}>
          <p className="text-xs font-semibold text-gray-400 mb-1.5">{k}</p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-x-6 gap-y-1">
            {Object.entries(obj).map(([ok, ov]) => (
              <div key={ok}>
                <span className="text-[10px] text-gray-500">{ok}: </span>
                <span className="text-xs text-gray-300">{ov === null || ov === '' ? '—' : String(ov)}</span>
              </div>
            ))}
          </div>
        </div>
      ))}
      {nested.map(([k, rows]) => (
        <div key={k}>
          <p className="text-xs font-semibold text-gray-400 mb-1.5">{k} ({rows.length})</p>
          <SubTable rows={rows} />
        </div>
      ))}
    </div>
  )
}

export default function MatchPointPanel({ endpoint, title, hasDateRange }: Props) {
  const [dateFrom, setDateFrom] = useState(monthStartStr)
  const [dateTo, setDateTo] = useState(todayStr)
  const [data, setData] = useState<Row[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [query, setQuery] = useState('')
  const [expanded, setExpanded] = useState<number | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    setExpanded(null)
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
        setData((json.data ?? []) as Row[])
      }
    } catch {
      setError('Network error — could not reach the server')
      setData(null)
    } finally {
      setLoading(false)
    }
  }, [endpoint, hasDateRange, dateFrom, dateTo])

  useEffect(() => { load() }, [load])

  const filtered = useMemo(() => {
    if (!data) return null
    if (!query.trim()) return data
    const q = query.toLowerCase()
    return data.filter((row) => JSON.stringify(row).toLowerCase().includes(q))
  }, [data, query])

  // Columns: scalar fields only; nested shown via expansion
  const columns = useMemo(() => {
    if (!filtered?.length) return []
    return Object.keys(filtered[0]).filter((k) => {
      const v = filtered[0][k]
      return typeof v !== 'object' || v === null
    })
  }, [filtered])

  const hasNested = useMemo(() => {
    if (!filtered?.length) return false
    return Object.values(filtered[0]).some((v) => typeof v === 'object' && v !== null)
  }, [filtered])

  // Sales summary
  const salesSummary = useMemo(() => {
    if (endpoint !== 'sales' || !filtered) return null
    const active = filtered.filter((r) => !r.IsCanceled)
    const total = active.reduce((s, r) => s + (Number(r.Total) || 0), 0)
    const paid = active.filter((r) => r.Paid).length
    return { total, docs: active.length, paid, unpaid: active.length - paid }
  }, [endpoint, filtered])

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center gap-3 px-6 py-3 border-b border-gray-800 shrink-0 flex-wrap">
        <h2 className="text-sm font-semibold text-white mr-1">{title}</h2>

        {hasDateRange && (
          <>
            <input
              type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)}
              className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-indigo-500"
            />
            <span className="text-gray-600 text-xs">→</span>
            <input
              type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)}
              className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-indigo-500"
            />
          </>
        )}

        <div className="flex items-center gap-2 bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 focus-within:border-indigo-500 min-w-[180px]">
          <Search size={14} className="text-gray-500 shrink-0" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={`Search ${title.toLowerCase()}…`}
            className="bg-transparent text-sm text-white placeholder-gray-500 focus:outline-none w-full"
          />
        </div>

        <button
          onClick={load}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm font-medium transition-colors"
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          {loading ? 'Loading…' : 'Refresh'}
        </button>

        {filtered && (
          <span className="ml-auto text-xs text-gray-500">
            {filtered.length}{query && data ? ` of ${data.length}` : ''} records
          </span>
        )}
      </div>

      {/* Sales summary chips */}
      {salesSummary && (
        <div className="flex gap-3 px-6 py-3 border-b border-gray-800 shrink-0 flex-wrap">
          <div className="bg-gray-900 border border-gray-800 rounded-xl px-4 py-2">
            <p className="text-[10px] uppercase tracking-wide text-gray-500">Revenue</p>
            <p className="text-lg font-bold text-white tabular-nums">OMR {salesSummary.total.toFixed(2)}</p>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl px-4 py-2">
            <p className="text-[10px] uppercase tracking-wide text-gray-500">Documents</p>
            <p className="text-lg font-bold text-white tabular-nums">{salesSummary.docs}</p>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl px-4 py-2">
            <p className="text-[10px] uppercase tracking-wide text-gray-500">Paid</p>
            <p className="text-lg font-bold text-green-400 tabular-nums">{salesSummary.paid}</p>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl px-4 py-2">
            <p className="text-[10px] uppercase tracking-wide text-gray-500">Unpaid</p>
            <p className="text-lg font-bold text-amber-400 tabular-nums">{salesSummary.unpaid}</p>
          </div>
        </div>
      )}

      {/* Body */}
      <div className="flex-1 overflow-auto p-6">
        {error && (
          <div className="max-w-lg mx-auto mt-8 p-5 bg-red-900/20 border border-red-800 rounded-2xl text-center">
            <AlertTriangle size={32} className="text-red-500 mx-auto mb-3" />
            <p className="text-red-400 font-semibold mb-1">MatchPoint API Error</p>
            <p className="text-red-300/70 text-sm">{error}</p>
          </div>
        )}

        {loading && !filtered && !error && (
          <div className="flex items-center justify-center h-48 text-gray-500 text-sm gap-2">
            <RefreshCw size={16} className="animate-spin" /> Loading {title.toLowerCase()}…
          </div>
        )}

        {filtered && filtered.length === 0 && (
          <div className="flex flex-col items-center justify-center h-48 text-gray-500">
            <Inbox size={36} className="mb-3 opacity-40" />
            <p className="text-sm">
              {query ? `No ${title.toLowerCase()} match “${query}”` : `No ${title.toLowerCase()} found for this period`}
            </p>
          </div>
        )}

        {filtered && filtered.length > 0 && (
          <div className="rounded-xl border border-gray-800 overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-900 border-b border-gray-800">
                  {hasNested && <th className="w-8" />}
                  {columns.map((col) => (
                    <th key={col} className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wide whitespace-nowrap">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map((row, i) => (
                  <Fragment key={i}>
                    <tr
                      onClick={() => hasNested && setExpanded(expanded === i ? null : i)}
                      className={`border-b border-gray-800/60 transition-colors ${
                        hasNested ? 'cursor-pointer hover:bg-gray-900/60' : 'hover:bg-gray-900/40'
                      } ${expanded === i ? 'bg-gray-900/60' : ''}`}
                    >
                      {hasNested && (
                        <td className="pl-3">
                          <ChevronRight
                            size={14}
                            className={`text-gray-600 transition-transform ${expanded === i ? 'rotate-90' : ''}`}
                          />
                        </td>
                      )}
                      {columns.map((col) => {
                        const val = row[col]
                        return (
                          <td key={col} className="px-4 py-3 whitespace-nowrap max-w-[220px] overflow-hidden text-ellipsis">
                            {val === null || val === undefined || val === '' ? (
                              <span className="text-gray-600">—</span>
                            ) : typeof val === 'boolean' ? (
                              <span className={val ? 'text-green-400' : 'text-gray-500'}>{String(val)}</span>
                            ) : (
                              <span className="text-gray-200">{String(val)}</span>
                            )}
                          </td>
                        )
                      })}
                    </tr>
                    {expanded === i && (
                      <tr className="border-b border-gray-800">
                        <td colSpan={columns.length + (hasNested ? 1 : 0)}>
                          <DetailPane row={row} />
                        </td>
                      </tr>
                    )}
                  </Fragment>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
