# Urban Playground — Booking App Handover

## Project Goal
Migrate from TPC-Matchpoint to a custom booking web app for Urban Playground (urbanpadel.om).
Target deployment: `bookings.urbanpadel.om`
Style reference: Playtomic

---

## What's Been Built

### Location
`/booking-app/` inside the repo `infourbanplayground-cell/May-madness`
Branch: `claude/tpc-matchpoint-migration-strategy-2cnxok`

### Tech Stack
- **Framework:** Next.js 16 (App Router, TypeScript)
- **Styling:** Tailwind CSS
- **Icons:** lucide-react
- **Dates:** date-fns
- **Auth:** Cookie-based session (httpOnly, 7-day expiry)
- **Data:** In-memory store (ready to swap for Supabase)

### Features Complete
| Feature | File |
|---|---|
| Password-protected login | `src/app/login/page.tsx` |
| Admin session middleware | `src/proxy.ts` |
| Login / logout API | `src/app/api/auth/login/route.ts` |
| 4-court Playtomic-style calendar | `src/components/BookingCalendar.tsx` |
| Click-to-book modal | inside `BookingCalendar.tsx` |
| Recurring bookings (by day of week + end date) | `src/lib/store.ts` |
| Cancel booking with confirmation | `BookingCalendar.tsx` |
| Bookings REST API (GET / POST / DELETE / PATCH) | `src/app/api/bookings/` |
| Sign out button | `src/components/LogoutButton.tsx` |

### Courts Configured
| Court | Sport | Color |
|---|---|---|
| Court 1 | Padel | Indigo |
| Court 2 | Padel | Green |
| Court 3 | Pickleball | Amber |
| Court 4 | Pickleball | Red |

Edit courts in `src/lib/store.ts` → `COURTS` array.

### Time Slots
06:00 → 19:30 in 30-minute increments. Edit in `src/lib/store.ts` → `TIME_SLOTS`.

---

## Environment Variables

File: `booking-app/.env.local` (gitignored — must recreate on each server)

```
ADMIN_PASSWORD=urbanplayground2026     ← change this before going live
NEXT_PUBLIC_VENUE_NAME=Urban Playground
```

---

## Running Locally

```bash
cd booking-app
npm install
npm run dev
# → http://localhost:3000
# Password: urbanplayground2026
```

---

## Deployment Target

- **Domain:** bookings.urbanpadel.om
- **Current site:** urbanpadel.om is live on Cloudflare
- **Deployment method:** TBD — owner to re-share hosting credentials
  - Site is behind Cloudflare (confirmed via curl)
  - Previous session had hosting access but credentials don't persist between sessions

### What's Needed to Deploy
1. Hosting credentials (cPanel / SSH / FTP — whichever was used before)
2. Set `ADMIN_PASSWORD` env var on the server
3. Add DNS record in Cloudflare: `bookings` CNAME → server

---

## What's NOT Built Yet (Next Steps)

### High Priority
- [ ] **Persistent database** — currently in-memory (resets on server restart)
  - Recommended: Supabase (free tier, Postgres, drop-in replacement)
  - Schema ready to create: `bookings` table matching `src/lib/types.ts`
- [ ] **Deploy to bookings.urbanpadel.om**

### Medium Priority
- [ ] **Member self-service booking** — public-facing page where members book their own slots
- [ ] **SMS / WhatsApp confirmation** — notify player when admin books for them
- [ ] **Daily view / week view toggle**
- [ ] **Booking list / search** — view all upcoming bookings in a table

### Low Priority
- [ ] **Court names editable from UI** — currently hardcoded in store.ts
- [ ] **Export bookings to CSV**
- [ ] **Block-out times** (maintenance, private events)

---

## Data Model

```typescript
type Booking = {
  id: string
  courtId: string          // 'court-1' | 'court-2' | 'court-3' | 'court-4'
  date: string             // 'YYYY-MM-DD'
  startTime: string        // 'HH:MM' (24h)
  endTime: string          // 'HH:MM' (24h)
  playerName: string
  playerPhone: string
  notes: string
  isRecurring: boolean
  recurringDays?: number[] // 0=Sun, 1=Mon … 6=Sat
  recurringUntil?: string  // 'YYYY-MM-DD'
  status: 'confirmed' | 'cancelled'
  createdAt: string        // ISO timestamp
}
```

---

## Swapping to Supabase (when ready)

1. Create a Supabase project at supabase.com
2. Run this SQL in the Supabase editor:

```sql
create table bookings (
  id uuid primary key default gen_random_uuid(),
  court_id text not null,
  date date not null,
  start_time time not null,
  end_time time not null,
  player_name text not null,
  player_phone text,
  notes text,
  is_recurring boolean default false,
  recurring_days int[],
  recurring_until date,
  status text default 'confirmed',
  created_at timestamptz default now()
);
```

3. Add to `.env.local`:
```
NEXT_PUBLIC_SUPABASE_URL=...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
```

4. Replace `src/lib/store.ts` functions with Supabase client calls — the API routes don't need to change.

---

## Key Files Map

```
booking-app/
├── src/
│   ├── proxy.ts                          ← auth guard (all routes)
│   ├── app/
│   │   ├── layout.tsx                    ← root layout
│   │   ├── page.tsx                      ← main dashboard page
│   │   ├── login/page.tsx                ← login screen
│   │   ├── globals.css                   ← base styles
│   │   └── api/
│   │       ├── auth/login/route.ts       ← POST /api/auth/login
│   │       ├── auth/logout/route.ts      ← POST /api/auth/logout
│   │       └── bookings/
│   │           ├── route.ts              ← GET /api/bookings, POST /api/bookings
│   │           └── [id]/route.ts         ← DELETE/PATCH /api/bookings/:id
│   ├── components/
│   │   ├── BookingCalendar.tsx           ← main UI (calendar + modals)
│   │   └── LogoutButton.tsx             ← sign out button
│   └── lib/
│       ├── types.ts                      ← Court, Booking types
│       └── store.ts                      ← data layer (swap for Supabase here)
└── .env.local                            ← secrets (gitignored)
```
