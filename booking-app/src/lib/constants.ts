import { Court } from './types'

export const COURTS: Court[] = [
  { id: 'court-1', name: 'Court 1', sport: 'Padel', color: '#6366f1' },
  { id: 'court-2', name: 'Court 2', sport: 'Padel', color: '#10b981' },
  { id: 'court-3', name: 'Court 3', sport: 'Pickleball', color: '#f59e0b' },
  { id: 'court-4', name: 'Court 4', sport: 'Pickleball', color: '#ef4444' },
]

export const TIME_SLOTS: string[] = Array.from({ length: 28 }, (_, i) => {
  const totalMinutes = 6 * 60 + i * 30
  const h = Math.floor(totalMinutes / 60).toString().padStart(2, '0')
  const m = (totalMinutes % 60).toString().padStart(2, '0')
  return `${h}:${m}`
})
