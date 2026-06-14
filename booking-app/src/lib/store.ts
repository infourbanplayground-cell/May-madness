import 'server-only'
import { Pool } from 'pg'
import { Booking } from './types'
export { COURTS, TIME_SLOTS } from './constants'

const pool = new Pool({ connectionString: process.env.DATABASE_URL })

function rowToBooking(row: Record<string, unknown>): Booking {
  const dateVal = row.date instanceof Date
    ? row.date.toISOString().split('T')[0]
    : String(row.date).split('T')[0]
  const untilVal = row.recurring_until
    ? (row.recurring_until instanceof Date
        ? row.recurring_until.toISOString().split('T')[0]
        : String(row.recurring_until).split('T')[0])
    : undefined
  return {
    id: row.id as string,
    courtId: row.court_id as string,
    date: dateVal,
    startTime: String(row.start_time).slice(0, 5),
    endTime: String(row.end_time).slice(0, 5),
    playerName: row.player_name as string,
    playerPhone: (row.player_phone as string) ?? '',
    notes: (row.notes as string) ?? '',
    isRecurring: row.is_recurring as boolean,
    recurringDays: row.recurring_days as number[] | undefined,
    recurringUntil: untilVal,
    status: row.status as 'confirmed' | 'cancelled',
    createdAt: String(row.created_at),
  }
}

export async function getBookings(): Promise<Booking[]> {
  const { rows } = await pool.query(
    'SELECT * FROM bookings ORDER BY date, start_time'
  )
  return rows.map(rowToBooking)
}

export async function getBookingsForDate(date: string): Promise<Booking[]> {
  const { rows } = await pool.query(
    "SELECT * FROM bookings WHERE date=$1 AND status!='cancelled' ORDER BY start_time",
    [date]
  )
  return rows.map(rowToBooking)
}

export async function addBooking(booking: Booking): Promise<void> {
  const toInsert: Booking[] = [booking]

  if (booking.isRecurring && booking.recurringDays && booking.recurringUntil) {
    const until = new Date(booking.recurringUntil)
    const cursor = new Date(booking.date)
    cursor.setDate(cursor.getDate() + 1)
    while (cursor <= until) {
      if (booking.recurringDays.includes(cursor.getDay())) {
        const d = cursor.toISOString().split('T')[0]
        toInsert.push({ ...booking, id: `${booking.id}-${d}`, date: d, isRecurring: false })
      }
      cursor.setDate(cursor.getDate() + 1)
    }
  }

  for (const b of toInsert) {
    await pool.query(
      `INSERT INTO bookings
        (id,court_id,date,start_time,end_time,player_name,player_phone,
         notes,is_recurring,recurring_days,recurring_until,status,created_at)
       VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)`,
      [
        b.id, b.courtId, b.date, b.startTime, b.endTime,
        b.playerName, b.playerPhone, b.notes,
        b.isRecurring, b.recurringDays ?? null,
        b.recurringUntil ?? null, b.status, b.createdAt,
      ]
    )
  }
}

export async function cancelBooking(id: string): Promise<void> {
  await pool.query("UPDATE bookings SET status='cancelled' WHERE id=$1", [id])
}

export async function updateBooking(id: string, patch: Partial<Booking>): Promise<void> {
  const fields: string[] = []
  const vals: unknown[] = []
  let i = 1
  if (patch.playerName !== undefined) { fields.push(`player_name=$${i++}`); vals.push(patch.playerName) }
  if (patch.playerPhone !== undefined) { fields.push(`player_phone=$${i++}`); vals.push(patch.playerPhone) }
  if (patch.notes !== undefined) { fields.push(`notes=$${i++}`); vals.push(patch.notes) }
  if (patch.startTime !== undefined) { fields.push(`start_time=$${i++}`); vals.push(patch.startTime) }
  if (patch.endTime !== undefined) { fields.push(`end_time=$${i++}`); vals.push(patch.endTime) }
  if (patch.status !== undefined) { fields.push(`status=$${i++}`); vals.push(patch.status) }
  if (!fields.length) return
  vals.push(id)
  await pool.query(`UPDATE bookings SET ${fields.join(',')} WHERE id=$${i}`, vals)
}
