import 'server-only'
import { Pool, types } from 'pg'
import { Booking, Member } from './types'
export { COURTS, TIME_SLOTS } from './constants'

// Return DATE columns as 'YYYY-MM-DD' strings, not Date objects.
// Without this, pg converts the date to midnight local time before giving us a
// Date object, so .toISOString() on a UTC+4 server rolls the date back one day.
types.setTypeParser(types.builtins.DATE, (val: string) => val)

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
  // Tracks whether an app-created booking has been keyed into MatchPoint by
  // staff. MatchPoint's Query API is read-only, so this is done by hand.
  // bookings is owned by postgres; if the app user lacks rights to alter it the
  // column is added out-of-band and this is a no-op.
  try {
    await pool.query(
      'ALTER TABLE bookings ADD COLUMN IF NOT EXISTS synced_to_matchpoint BOOLEAN NOT NULL DEFAULT FALSE'
    )
  } catch {
    // insufficient privilege — column is managed by the DBA migration
  }
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
    syncedToMatchpoint: Boolean(row.synced_to_matchpoint),
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

/**
 * App-created bookings (not imported from MatchPoint) that staff still need to
 * key into MatchPoint by hand. Cancelled bookings are excluded — nothing to
 * enter. Past bookings are kept so nothing silently disappears from the queue.
 */
export async function getPendingMatchpointEntry(): Promise<Booking[]> {
  const { rows } = await pool.query(
    `SELECT * FROM bookings
      WHERE synced_to_matchpoint = FALSE
        AND status <> 'cancelled'
        AND booking_source <> 'matchpoint'
      ORDER BY date, start_time`
  )
  return rows.map(rowToBooking)
}

export async function setBookingSynced(id: string, synced: boolean): Promise<boolean> {
  const { rowCount } = await pool.query(
    'UPDATE bookings SET synced_to_matchpoint = $2 WHERE id = $1',
    [id, synced]
  )
  return (rowCount ?? 0) > 0
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

// ─── Imported MatchPoint customers ────────────────────────────────────────────
// A local copy of the MatchPoint customer list. Kept locally rather than read
// live so the player list survives cancelling the MatchPoint subscription.

export type StoredCustomer = {
  code: string
  name: string
  email: string
  mobile: string
  memberCode: string
  entryDate: string | null
  status: string
  type: string
  groups: string[]
}

function rowToCustomer(row: Record<string, unknown>): StoredCustomer {
  return {
    code: row.code as string,
    name: row.name as string,
    email: (row.email as string) ?? '',
    mobile: (row.mobile as string) ?? '',
    memberCode: (row.member_code as string) ?? '',
    entryDate: row.entry_date ? String(row.entry_date).slice(0, 10) : null,
    status: (row.status as string) ?? '',
    type: (row.type as string) ?? '',
    groups: (row.groups as string[]) ?? [],
  }
}

/** Upsert a batch of customers. Returns how many rows were newly inserted. */
export async function upsertCustomers(customers: StoredCustomer[]): Promise<number> {
  if (!customers.length) return 0
  const client = await pool.connect()
  let inserted = 0
  try {
    await client.query('BEGIN')
    for (const c of customers) {
      const { rows } = await client.query(
        `INSERT INTO mp_customers
           (code, name, email, mobile, member_code, entry_date, status, type, groups, imported_at)
         VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9, now())
         ON CONFLICT (code) DO UPDATE SET
           name=EXCLUDED.name, email=EXCLUDED.email, mobile=EXCLUDED.mobile,
           member_code=EXCLUDED.member_code, entry_date=EXCLUDED.entry_date,
           status=EXCLUDED.status, type=EXCLUDED.type, groups=EXCLUDED.groups,
           imported_at=now()
         RETURNING (xmax = 0) AS is_new`,
        [
          c.code, c.name, c.email, c.mobile, c.memberCode,
          c.entryDate || null, c.status, c.type, c.groups,
        ]
      )
      if (rows[0]?.is_new) inserted++
    }
    await client.query('COMMIT')
  } catch (e) {
    await client.query('ROLLBACK')
    throw e
  } finally {
    client.release()
  }
  return inserted
}

export async function getCustomerCount(): Promise<{ total: number; lastImport: string | null }> {
  const { rows } = await pool.query(
    'SELECT count(*)::int AS total, max(imported_at) AS last_import FROM mp_customers'
  )
  return {
    total: rows[0].total as number,
    lastImport: rows[0].last_import ? String(rows[0].last_import) : null,
  }
}

/** Name or mobile prefix/substring search, for front-desk autocomplete. */
export async function searchCustomers(query: string, limit = 8): Promise<StoredCustomer[]> {
  const q = query.trim()
  if (q.length < 2) return []
  const { rows } = await pool.query(
    `SELECT * FROM mp_customers
      WHERE lower(name) LIKE lower($1)
         OR mobile LIKE $1
         OR lower(email) LIKE lower($1)
      ORDER BY
        CASE WHEN lower(name) LIKE lower($2) THEN 0 ELSE 1 END,
        name
      LIMIT $3`,
    [`%${q}%`, `${q}%`, limit]
  )
  return rows.map(rowToCustomer)
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
