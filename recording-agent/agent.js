#!/usr/bin/env node
'use strict'

const fs = require('fs')
const path = require('path')
const { spawn } = require('child_process')

const CONFIG_PATH = path.join(__dirname, 'config.json')
if (!fs.existsSync(CONFIG_PATH)) {
  console.error('Missing config.json — copy config.example.json to config.json and fill in your values.')
  process.exit(1)
}
const config = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8'))

const TMP_DIR = path.resolve(__dirname, config.tmpDir || './tmp')
fs.mkdirSync(TMP_DIR, { recursive: true })

async function pollOnce() {
  let jobs
  try {
    const res = await fetch(`${config.apiBaseUrl}/api/record/jobs`, {
      headers: { 'x-agent-secret': config.agentSecret },
    })
    if (!res.ok) {
      console.error(`poll failed: ${res.status}`)
      return
    }
    jobs = await res.json()
  } catch (err) {
    console.error('poll error:', err.message)
    return
  }

  for (const job of jobs) {
    await handleJob(job)
  }
}

async function handleJob(job) {
  const rtspUrl = config.cameras[job.courtId]
  const tmpFile = path.join(TMP_DIR, `${job.id}.mp4`)
  console.log(`[${job.id}] recording court=${job.courtId} for ${job.durationMinutes}min`)

  if (!rtspUrl) {
    await reportFail(job.id, `No camera configured for court "${job.courtId}"`)
    return
  }

  try {
    await runFfmpeg(rtspUrl, job.durationMinutes * 60, tmpFile)
    console.log(`[${job.id}] recording finished, uploading…`)
    await uploadRecording(job.id, tmpFile)
    console.log(`[${job.id}] upload complete`)
  } catch (err) {
    console.error(`[${job.id}] failed:`, err.message)
    await reportFail(job.id, err.message)
  } finally {
    fs.rm(tmpFile, { force: true }, () => {})
  }
}

function runFfmpeg(rtspUrl, durationSec, outFile) {
  return new Promise((resolve, reject) => {
    // Re-encodes to a modest, predictable bitrate so uploads/downloads stay
    // reasonable in size. Swap "-c:v libx264 ... -crf 23" for "-c:v copy" if
    // the local machine can't keep up with encoding in real time — that
    // passes the camera's stream through untouched (larger files, no CPU cost).
    const args = [
      '-rtsp_transport', 'tcp',
      '-i', rtspUrl,
      '-t', String(durationSec),
      '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23',
      '-c:a', 'aac', '-b:a', '128k',
      '-movflags', '+faststart',
      '-y', outFile,
    ]
    const proc = spawn('ffmpeg', args)
    let stderr = ''
    proc.stderr.on('data', (d) => {
      stderr += d.toString()
      if (stderr.length > 4000) stderr = stderr.slice(-4000)
    })
    proc.on('error', reject)
    proc.on('exit', (code) => {
      if (code === 0) resolve()
      else reject(new Error(`ffmpeg exited ${code}: ${stderr.slice(-500)}`))
    })
  })
}

async function uploadRecording(jobId, filePath) {
  // fs.openAsBlob streams the file from disk instead of buffering it in
  // memory, which matters here since recordings can run into the hundreds
  // of MB.
  const blob = await fs.openAsBlob(filePath, { type: 'video/mp4' })
  const form = new FormData()
  form.append('file', blob, `${jobId}.mp4`)

  const res = await fetch(`${config.apiBaseUrl}/api/record/jobs/${jobId}/complete`, {
    method: 'POST',
    headers: { 'x-agent-secret': config.agentSecret },
    body: form,
  })
  if (!res.ok) {
    throw new Error(`upload failed: ${res.status} ${await res.text()}`)
  }
}

async function reportFail(jobId, error) {
  try {
    await fetch(`${config.apiBaseUrl}/api/record/jobs/${jobId}/fail`, {
      method: 'POST',
      headers: { 'x-agent-secret': config.agentSecret, 'content-type': 'application/json' },
      body: JSON.stringify({ error }),
    })
  } catch (err) {
    console.error('could not report failure:', err.message)
  }
}

const pollInterval = config.pollIntervalMs || 5000
console.log(`Recording agent started. Polling ${config.apiBaseUrl} every ${pollInterval}ms`)
setInterval(pollOnce, pollInterval)
pollOnce()
