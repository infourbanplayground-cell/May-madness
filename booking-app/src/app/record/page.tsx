'use client'

import { useState, useEffect, useCallback, Suspense } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { COURTS } from '@/lib/constants'

type RecordingStatus = 'pending' | 'recording' | 'uploading' | 'ready' | 'failed'

type Job = {
  id: string
  courtId: string
  status: RecordingStatus
  durationMinutes: number
  downloadToken?: string
  error?: string
}

const DURATIONS = [
  { value: 60, label: '1h' },
  { value: 90, label: '1.5h' },
  { value: 120, label: '2h' },
]

function statusLabel(status: RecordingStatus): string {
  switch (status) {
    case 'pending': return 'Waiting for the camera to start…'
    case 'recording': return 'Recording your match…'
    case 'uploading': return 'Processing your video…'
    case 'ready': return 'Your video is ready!'
    case 'failed': return 'Something went wrong.'
  }
}

function RecordForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const courtId = searchParams.get('court') || ''
  const jobId = searchParams.get('job')
  const court = COURTS.find((c) => c.id === courtId)

  const [phone, setPhone] = useState('')
  const [duration, setDuration] = useState(90)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [job, setJob] = useState<Job | null>(null)

  const pollStatus = useCallback(async (id: string) => {
    const res = await fetch(`/api/record/status/${id}`)
    if (!res.ok) return null
    const data: Job = await res.json()
    setJob(data)
    return data
  }, [])

  useEffect(() => {
    if (!jobId) return
    const id = jobId
    let cancelled = false
    let timer: ReturnType<typeof setTimeout>

    async function tick() {
      const data = await pollStatus(id)
      if (cancelled) return
      if (data && (data.status === 'ready' || data.status === 'failed')) return
      timer = setTimeout(tick, 4000)
    }
    tick()

    return () => {
      cancelled = true
      clearTimeout(timer)
    }
  }, [jobId, pollStatus])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await fetch('/api/record/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ courtId, phone: phone.trim(), durationMinutes: duration }),
      })
      const data = await res.json()
      if (!res.ok) {
        setError(data.error || 'Could not start recording')
        setLoading(false)
        return
      }
      router.replace(`/record?court=${courtId}&job=${data.id}`)
    } catch {
      setError('Network error. Please try again.')
      setLoading(false)
    }
  }

  if (!court) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center px-4">
        <p className="text-gray-600 text-center">
          Unknown court. Please scan the QR code at your court again.
        </p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-white flex flex-col items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="flex justify-center mb-6">
          <span
            className="px-4 py-1.5 rounded-full text-sm font-semibold text-white"
            style={{ backgroundColor: court.color }}
          >
            {court.name}
          </span>
        </div>

        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-8">
          {!job ? (
            <>
              <h1 className="text-2xl font-bold text-gray-900 mb-1">Record your match</h1>
              <p className="text-sm text-gray-500 mb-6">
                We&apos;ll record this court and send you a download link when you&apos;re done.
              </p>

              {error && (
                <div className="mb-4 p-3 rounded-xl bg-red-50 border border-red-100 text-red-600 text-sm">
                  {error}
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">
                    Phone number
                  </label>
                  <input
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    required
                    placeholder="+968 0000 0000"
                    className="w-full border border-gray-300 rounded-xl px-4 py-3 text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">
                    Duration
                  </label>
                  <div className="grid grid-cols-3 gap-2">
                    {DURATIONS.map((d) => (
                      <button
                        key={d.value}
                        type="button"
                        onClick={() => setDuration(d.value)}
                        className={`py-2.5 rounded-xl text-sm font-semibold border transition-colors ${
                          duration === d.value
                            ? 'bg-indigo-600 border-indigo-600 text-white'
                            : 'bg-white border-gray-300 text-gray-700'
                        }`}
                      >
                        {d.label}
                      </button>
                    ))}
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60 disabled:cursor-not-allowed text-white font-semibold text-sm transition-colors shadow-sm"
                >
                  {loading ? 'Starting…' : 'Start Recording'}
                </button>
              </form>
            </>
          ) : (
            <div className="text-center py-4">
              {job.status !== 'ready' && job.status !== 'failed' && (
                <div className="mx-auto mb-4 w-10 h-10 rounded-full border-2 border-indigo-200 border-t-indigo-600 animate-spin" />
              )}
              <p className="text-gray-900 font-semibold mb-1">{statusLabel(job.status)}</p>
              {job.status === 'failed' && job.error && (
                <p className="text-sm text-red-500 mb-4">{job.error}</p>
              )}
              {job.status === 'ready' && job.downloadToken && (
                <a
                  href={`/api/record/download/${job.downloadToken}`}
                  className="inline-block mt-4 py-3 px-6 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm transition-colors shadow-sm"
                >
                  Download your video
                </a>
              )}
              {job.status === 'failed' && (
                <button
                  onClick={() => router.replace(`/record?court=${courtId}`)}
                  className="mt-2 text-sm text-indigo-600 font-medium"
                >
                  Try again
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default function RecordPage() {
  return (
    <Suspense>
      <RecordForm />
    </Suspense>
  )
}
