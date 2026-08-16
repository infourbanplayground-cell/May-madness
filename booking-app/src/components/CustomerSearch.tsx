'use client'

import { useState, useEffect, useRef } from 'react'
import { User, Search, X, Check } from 'lucide-react'

export type CustomerHit = {
  code: string
  name: string
  email: string
  mobile: string
  memberCode: string
}

/**
 * Front-desk player lookup against the imported MatchPoint customer list.
 * Typing filters by name, mobile or email; picking one fills the booking form.
 * The caller keeps ownership of name/phone so a walk-in can still be typed
 * free-hand without selecting anybody.
 */
export default function CustomerSearch({
  name,
  phone,
  onChange,
}: {
  name: string
  phone: string
  onChange: (v: { name: string; phone: string }) => void
}) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<CustomerHit[]>([])
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [picked, setPicked] = useState<CustomerHit | null>(null)
  const boxRef = useRef<HTMLDivElement>(null)

  // Debounced search
  useEffect(() => {
    const q = query.trim()
    if (q.length < 2) {
      setResults([])
      return
    }
    let cancelled = false
    setLoading(true)
    const t = setTimeout(async () => {
      try {
        const res = await fetch(`/api/admin/customers/search?q=${encodeURIComponent(q)}`)
        const json = await res.json()
        if (!cancelled && json.ok) {
          setResults(json.results)
          setOpen(true)
        }
      } catch {
        if (!cancelled) setResults([])
      } finally {
        if (!cancelled) setLoading(false)
      }
    }, 200)
    return () => { cancelled = true; clearTimeout(t) }
  }, [query])

  // Close on outside click
  useEffect(() => {
    function onDoc(e: MouseEvent) {
      if (boxRef.current && !boxRef.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onDoc)
    return () => document.removeEventListener('mousedown', onDoc)
  }, [])

  function pick(c: CustomerHit) {
    setPicked(c)
    onChange({ name: c.name, phone: c.mobile })
    setQuery('')
    setResults([])
    setOpen(false)
  }

  function clearPick() {
    setPicked(null)
    onChange({ name: '', phone: '' })
  }

  if (picked) {
    return (
      <div>
        <label className="flex items-center gap-2 text-xs font-medium text-warm mb-1">
          <User size={14} /> Player *
        </label>
        <div className="flex items-center gap-3 bg-indigo-950/40 border border-indigo-800 rounded-lg px-3 py-2.5">
          <div className="w-7 h-7 rounded-full bg-ember text-cream text-xs font-bold flex items-center justify-center shrink-0">
            {picked.name.charAt(0).toUpperCase()}
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-cream truncate">{picked.name}</p>
            <p className="text-xs text-warm truncate">
              {picked.mobile || 'no phone on file'}
              {picked.memberCode && <> · member {picked.memberCode}</>}
            </p>
          </div>
          <Check size={15} className="text-green-400 shrink-0" />
          <button
            type="button"
            onClick={clearPick}
            title="Choose someone else"
            className="text-faint hover:text-cream shrink-0"
          >
            <X size={16} />
          </button>
        </div>
      </div>
    )
  }

  return (
    <div ref={boxRef} className="relative">
      <label className="flex items-center gap-2 text-xs font-medium text-warm mb-1">
        <User size={14} /> Player *
      </label>

      {/* Lookup */}
      <div className="flex items-center gap-2 bg-surface-2 border border-hair rounded-lg px-3 py-2.5 focus-within:ring-2 focus-within:ring-indigo-500">
        <Search size={14} className="text-faint shrink-0" />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => results.length && setOpen(true)}
          placeholder="Search name, phone or email…"
          className="bg-transparent text-cream placeholder-faint/60 focus:outline-none w-full text-sm"
        />
        {loading && <span className="text-[10px] text-faint shrink-0">…</span>}
      </div>

      {/* Results */}
      {open && results.length > 0 && (
        <div className="absolute z-30 left-0 right-0 mt-1 bg-surface border border-hair rounded-xl shadow-2xl overflow-hidden max-h-60 overflow-y-auto">
          {results.map((c) => (
            <button
              key={c.code}
              type="button"
              onClick={() => pick(c)}
              className="w-full flex items-center gap-3 px-3 py-2 hover:bg-surface-2 text-left transition-colors"
            >
              <div className="w-6 h-6 rounded-full bg-gray-700 text-cream text-[11px] font-bold flex items-center justify-center shrink-0">
                {c.name.charAt(0).toUpperCase()}
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm text-cream truncate">{c.name}</p>
                <p className="text-[11px] text-faint truncate">
                  {c.mobile || c.email || '—'}
                </p>
              </div>
            </button>
          ))}
        </div>
      )}

      {open && query.trim().length >= 2 && !loading && results.length === 0 && (
        <div className="absolute z-30 left-0 right-0 mt-1 bg-surface border border-hair rounded-xl px-3 py-2.5">
          <p className="text-xs text-faint">
            No match — type the name below to book a walk-in.
          </p>
        </div>
      )}

      {/* Manual entry fallback */}
      <div className="grid grid-cols-2 gap-2 mt-2">
        <input
          value={name}
          onChange={(e) => onChange({ name: e.target.value, phone })}
          required
          placeholder="Or type name"
          className="bg-surface-2 border border-hair rounded-lg px-3 py-2 text-cream placeholder-faint/60 text-sm focus:outline-none focus:ring-2 focus:ring-ember"
        />
        <input
          value={phone}
          onChange={(e) => onChange({ name, phone: e.target.value })}
          placeholder="Phone"
          className="bg-surface-2 border border-hair rounded-lg px-3 py-2 text-cream placeholder-faint/60 text-sm focus:outline-none focus:ring-2 focus:ring-ember"
        />
      </div>
    </div>
  )
}
