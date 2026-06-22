'use client'

import { useState } from 'react'
import BookingCalendar from '@/components/BookingCalendar'
import LogoutButton from '@/components/LogoutButton'
import MatchPointPanel from '@/components/MatchPointPanel'

type Tab = 'calendar' | 'customers' | 'matches' | 'activities' | 'sales'

const TABS: { id: Tab; label: string; icon: string }[] = [
  { id: 'calendar',    label: 'Calendar',    icon: 'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z' },
  { id: 'customers',   label: 'Customers',   icon: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z' },
  { id: 'matches',     label: 'Matches',     icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z' },
  { id: 'activities',  label: 'Activities',  icon: 'M13 10V3L4 14h7v7l9-11h-7z' },
  { id: 'sales',       label: 'Sales',       icon: 'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z' },
]

export default function HomePage() {
  const [tab, setTab] = useState<Tab>('calendar')

  return (
    <div className="flex flex-col h-screen bg-gray-950">
      {/* Top bar */}
      <header className="flex items-center justify-between px-6 py-3 border-b border-gray-800 bg-gray-950 shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center">
            <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16" />
            </svg>
          </div>
          <span className="font-bold text-white">Urban Playground</span>
          <span className="text-xs bg-indigo-900/50 text-indigo-300 px-2 py-0.5 rounded-full font-medium">Admin</span>
        </div>
        <LogoutButton />
      </header>

      {/* Nav tabs */}
      <nav className="flex border-b border-gray-800 bg-gray-950 shrink-0 px-4 overflow-x-auto">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 whitespace-nowrap transition-colors ${
              tab === t.id
                ? 'border-indigo-500 text-white'
                : 'border-transparent text-gray-400 hover:text-gray-200'
            }`}
          >
            <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={t.icon} />
            </svg>
            {t.label}
          </button>
        ))}
      </nav>

      {/* Content */}
      <main className="flex-1 overflow-hidden">
        {tab === 'calendar'   && <BookingCalendar />}
        {tab === 'customers'  && <MatchPointPanel endpoint="customers"  title="Customers"  hasDateRange={false} />}
        {tab === 'matches'    && <MatchPointPanel endpoint="matches"    title="Matches"    hasDateRange />}
        {tab === 'activities' && <MatchPointPanel endpoint="activities" title="Activities" hasDateRange />}
        {tab === 'sales'      && <MatchPointPanel endpoint="sales"      title="Sales"      hasDateRange />}
      </main>
    </div>
  )
}
