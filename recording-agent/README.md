# Court Recording Agent

Runs on a local machine at the club (not the VPS). It polls the booking
app's API for recording jobs, records the matching court's camera with
`ffmpeg`, and uploads the finished video back to the VPS.

## How the whole system works

1. Each court has a printed QR code sticker pointing at
   `https://bookings.urbanpadel.om/record?court=court-1`.
2. A player scans it, enters their phone number and picks a duration,
   which creates a "pending" job on the VPS (`POST /api/record/start`).
3. This agent polls `GET /api/record/jobs` every few seconds. When it sees
   a pending job, it looks up that court's camera RTSP URL and records for
   the requested duration with `ffmpeg`.
4. When recording finishes, the agent uploads the MP4 to
   `POST /api/record/jobs/:id/complete`. The VPS then generates a one-time
   download link that the player's browser (still on the scan page) picks
   up automatically.

## Prerequisites (on the local machine at the club)

- Node.js >= 20 (uses `fs.openAsBlob` and the built-in `fetch`/`FormData`)
- `ffmpeg` installed and on `PATH` (`apt install ffmpeg`)
- Network access to both the court cameras (RTSP, usually on the club's
  LAN) and to `bookings.urbanpadel.om` (outbound HTTPS)
- Cameras must support RTSP (most PoE IP cameras do) — find each camera's
  RTSP URL from its admin page or manual, e.g.
  `rtsp://user:pass@192.168.1.101:554/stream1`

## Setup

```bash
cd recording-agent
npm install
cp config.example.json config.json
```

Edit `config.json`:
- `apiBaseUrl`: `https://bookings.urbanpadel.om`
- `agentSecret`: must match `RECORDING_AGENT_SECRET` in the VPS's
  `/opt/booking-app/.env.local` — generate with `openssl rand -hex 32`
- `cameras`: map each `court-N` (must match the court IDs in
  `booking-app/src/lib/constants.ts`) to its RTSP URL

Test a single camera works before wiring up the full system:
```bash
ffplay "rtsp://user:pass@192.168.1.101:554/stream1"
```

Run the agent:
```bash
npm start
```

Generate the QR codes to print and stick at each court:
```bash
npm run qr
# -> qr-codes/court-1.png, court-2.png, ...
```

## Running as a service (recommended)

Copy `recording-agent.service` to `/etc/systemd/system/`, adjust
`WorkingDirectory`/`ExecStart` if you didn't install to
`/opt/court-recording-agent`, then:

```bash
sudo useradd -r -s /usr/sbin/nologin recorder   # if not already present
sudo systemctl daemon-reload
sudo systemctl enable --now recording-agent
sudo journalctl -u recording-agent -f
```

## Notes / tradeoffs

- The agent re-encodes with `libx264 -crf 23` rather than a raw passthrough
  so file sizes stay predictable for downloads over mobile data. If the
  local machine is underpowered, switch `agent.js` to `-c:v copy` (see
  comment in `runFfmpeg`) to skip encoding entirely — files will be larger.
- Recordings only live on the VPS for 48 hours (`expires_at` on the
  `recordings` table) before their download link stops working. Add a cron
  job on the VPS to actually delete expired files from disk, e.g.:
  ```
  find /opt/booking-app/recordings -type f -mtime +2 -delete
  ```
- One camera recording per court at a time is assumed — if two players
  scan the same court's QR code close together, jobs will queue and record
  back-to-back rather than in parallel.
