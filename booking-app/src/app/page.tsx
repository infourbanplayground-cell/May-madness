import BookingCalendar from '@/components/BookingCalendar'
import LogoutButton from '@/components/LogoutButton'
import MatchPointSync from '@/components/MatchPointSync'

export default function HomePage() {
  return (
    <div className="flex flex-col h-screen">
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
        <div className="flex items-center gap-2">
          <MatchPointSync />
          <LogoutButton />
        </div>
      </header>

      {/* Calendar takes the rest */}
      <main className="flex-1 overflow-hidden">
        <BookingCalendar />
      </main>
    </div>
  )
}
