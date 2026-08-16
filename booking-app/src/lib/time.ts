/**
 * Time display helpers.
 *
 * Times are stored and exchanged as 24-hour "HH:MM" everywhere — database,
 * API payloads and MatchPoint. These functions are for display only; never
 * feed their output back into a request.
 */

/** "16:00" -> "4:00 PM". Handles "24:00" as midnight. */
export function formatTime(hhmm: string): string {
  const [h, m] = hhmm.split(':').map(Number)
  if (Number.isNaN(h)) return hhmm
  const hour24 = h % 24
  const period = hour24 >= 12 ? 'PM' : 'AM'
  const hour12 = hour24 % 12 === 0 ? 12 : hour24 % 12
  return `${hour12}:${String(m ?? 0).padStart(2, '0')} ${period}`
}

/** Compact form for tight columns: "4 PM", "4:30 PM". */
export function formatTimeShort(hhmm: string): string {
  const [h, m] = hhmm.split(':').map(Number)
  if (Number.isNaN(h)) return hhmm
  const hour24 = h % 24
  const period = hour24 >= 12 ? 'PM' : 'AM'
  const hour12 = hour24 % 12 === 0 ? 12 : hour24 % 12
  return m ? `${hour12}:${String(m).padStart(2, '0')} ${period}` : `${hour12} ${period}`
}

/** "16:00"–"17:30" -> "4:00 PM – 5:30 PM" */
export function formatRange(start: string, end: string): string {
  return `${formatTime(start)} – ${formatTime(end)}`
}
