import 'server-only'
import { Pool } from 'pg'
import { Booking, Member } from './types'
export { COURTS, TIME_SLOTS } from './constants'

const pool = new Pool({ connectionString: process.env.DATABASE_URL })

// ─── DB Init ──────────────────────────────────────────────────────────────────

export async function initDB(): Promise<void> {
  await pool.query(`
    CREATE TABLE IF NOT EXISTS members (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      name TEXT NOT NULL,
      phone TEXT UNIQUE NOT NULL,
      password_hash TEXT NOT NULL,
      created_at TIMESTAMPTZ DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS court_prices (
      court_id TEXT PRIMARY KEY,
      price_per_hour NUMERIC(10,2) DEFAULT 0.00
    );
  `)
}

// ─── Row mappers ──────────────────────────────────────────────────────────────

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
    memberId: (row.member_id as string) ?? undefined,
    priceTotal: row.price_total != null ? Number(row.price_total) : undefined,
    durationMinutes: row.duration_minutes != null ? Number(row.duration_minutes) : undefined,
    bookingSource: (row.booking_source as string) ?? 'admin',
  }
}

function rowToMember(row: Record<string, unknown>): Member {
  return {
    id: row.id as string,
    name: row.name as string,
    phone: row.phone as string,
    createdAt: String(row.created_at),
  }
}

// ─── Bookings ─────────────────────────────────────────────────────────────────

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

export async function getBookingsForMember(memberId: string): Promise<Booking[]> {
  const { rows } = await pool.query(
    'SELECT * FROM bookings WHERE member_id=$1 ORDER BY date DESC, start_time DESC',
    [memberId]
  )
  return rows.map(rowToBooking)
}

export async function getBookingById(id: string): Promise<Booking | null> {
  const { rows } = await pool.query('SELECT * FROM bookings WHERE id=$1', [id])
  if (!rows.length) return null
  return rowToBooking(rows[0])
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
         notes,is_recurring,recurring_days,recurring_until,status,created_at,
         member_id,price_total,duration_minutes,booking_source)
       VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17)`,
      [
        b.id, b.courtId, b.date, b.startTime, b.endTime,
        b.playerName, b.playerPhone, b.notes,
        b.isRecurring, b.recurringDays ?? null,
        b.recurringUntil ?? null, b.status, b.createdAt,
        b.memberId ?? null,
        b.priceTotal ?? null,
        b.durationMinutes ?? null,
        b.bookingSource ?? 'admin',
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

// ─── Members ──────────────────────────────────────────────────────────────────

export async function getMemberByPhone(phone: string): Promise<(Member & { passwordHash: string }) | null> {
  const { rows } = await pool.query('SELECT * FROM members WHERE phone=$1', [phone])
  if (!rows.length) return null
  const row = rows[0] as Record<string, unknown>
  return {
    ...rowToMember(row),
    passwordHash: row.password_hash as string,
  }
}

export async function getMemberById(id: string): Promise<Member | null> {
  const { rows } = await pool.query('SELECT * FROM members WHERE id=$1', [id])
  if (!rows.length) return null
  return rowToMember(rows[0] as Record<string, unknown>)
}

export async function createMember(name: string, phone: string, passwordHash: string): Promise<Member> {
  const { rows } = await pool.query(
    'INSERT INTO members (name, phone, password_hash) VALUES ($1, $2, $3) RETURNING *',
    [name, phone, passwordHash]
  )
  return rowToMember(rows[0] as Record<string, unknown>)
}

// ─── Court prices ─────────────────────────────────────────────────────────────

export async function getCourtPrices(): Promise<Record<string, number>> {
  const { rows } = await pool.query('SELECT court_id, price_per_hour FROM court_prices')
  const result: Record<string, number> = {}
  for (const row of rows) {
    result[row.court_id as string] = Number(row.price_per_hour)
  }
  return result
}

export async function setCourtPrice(courtId: string, pricePerHour: number): Promise<void> {
  await pool.query(
    `INSERT INTO court_prices (court_id, price_per_hour)
     VALUES ($1, $2)
     ON CONFLICT (court_id) DO UPDATE SET price_per_hour = EXCLUDED.price_per_hour`,
    [courtId, pricePerHour]
  )
}
