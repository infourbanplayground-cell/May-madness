import { Court } from './types'

export const COURTS: Court[] = [
  { id: 'court-1', name: 'Court 1', sport: 'Padel', color: '#FF8A3D' },
  { id: 'court-2', name: 'Court 2', sport: 'Padel', color: '#FFC24B' },
  { id: 'court-3', name: 'Court 3', sport: 'Pickleball', color: '#33A1FF' },
  { id: 'court-4', name: 'Court 4', sport: 'Pickleball', color: '#8DF3E8' },
]

/**
 * Opening hours: 4:00 PM until midnight, in 30-minute increments.
 * 16 slots — the last, 23:30, runs to 24:00.
 * Stored in 24-hour form; see lib/time.ts for AM/PM display.
 */
export const OPENING_HOUR = 16
export const CLOSING_HOUR = 24

export const TIME_SLOTS: string[] = Array.from(
  { length: (CLOSING_HOUR - OPENING_HOUR) * 2 },
  (_, i) => {
    const totalMinutes = OPENING_HOUR * 60 + i * 30
    const h = Math.floor(totalMinutes / 60).toString().padStart(2, '0')
    const m = (totalMinutes % 60).toString().padStart(2, '0')
    return `${h}:${m}`
  }
)
