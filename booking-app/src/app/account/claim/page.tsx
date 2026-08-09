'use client'

import { useState, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'

type Step = 'identify' | 'verify' | 'done'

function ClaimForm() {
  const router = useRouter()
  const next = useSearchParams().get('next') || '/account'

  const [step, setStep] = useState<Step>('identify')
  const [identifier, setIdentifier] = useState('')
  const [masked, setMasked] = useState<string | null>(null)
  const [code, setCode] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [loading, setLoading] = useState(false)

  async function requestCode(e?: React.FormEvent) {
    e?.preventDefault()
    setError(''); setNotice(''); setLoading(true)
    try {
      const res = await fetch('/api/account/claim/request', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ identifier: identifier.trim() }),
      })
      const data = await res.json()
      if (!res.ok) {
        setError(data.error || 'Something went wrong')
        return
      }
      setMasked(data.masked ?? null)
      setStep('verify')
    } catch {
      setError('Network error. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  async function verify(e: React.FormEvent) {
    e.preventDefault()
    setError(''); setLoading(true)
    try {
      const res = await fetch('/api/account/claim/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ identifier: identifier.trim(), code: code.trim(), password }),
      })
      const data = await res.json()
      if (!res.ok) {
        setError(data.error || 'Could not verify that code')
        return
      }
      setStep('done')
      setTimeout(() => router.push(next), 1200)
    } catch {
      setError('Network error. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-4 py-10">
      <div className="w-full max-w-sm">
        <div className="flex justify-center mb-8">
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-600 to-violet-600 flex items-center justify-center shadow-md">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16" />
              </svg>
            </div>
            <span className="text-xl font-bold text-gray-900">Urban Playground</span>
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-8">
          {step === 'identify' && (
            <>
              <h1 className="text-2xl font-bold text-gray-900 mb-1">Set up your account</h1>
              <p className="text-sm text-gray-500 mb-6">
                Already played at Urban Playground? We probably have you on file. Enter the email
                or mobile you use with us and we&apos;ll send a code.
              </p>

              {error && (
                <div className="mb-4 p-3 rounded-xl bg-red-50 border border-red-100 text-red-600 text-sm">
                  {error}
                </div>
              )}

              <form onSubmit={requestCode} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">
                    Email or mobile number
                  </label>
                  <input
                    value={identifier}
                    onChange={(e) => setIdentifier(e.target.value)}
                    required
                    autoFocus
                    placeholder="you@example.com or 9xxxxxxx"
                    className="w-full border border-gray-300 rounded-xl px-4 py-3 text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3 rounded-xl bg-gray-900 hover:bg-gray-800 disabled:opacity-60 text-white font-semibold text-sm transition-colors"
                >
                  {loading ? 'Sending…' : 'Send me a code'}
                </button>
              </form>
            </>
          )}

          {step === 'verify' && (
            <>
              <h1 className="text-2xl font-bold text-gray-900 mb-1">Enter your code</h1>
              <p className="text-sm text-gray-500 mb-6">
                {masked
                  ? <>We sent a 6-digit code to <span className="font-medium text-gray-700">{masked}</span>. It expires in 15 minutes.</>
                  : <>If we have you on file, a 6-digit code is on its way. Check your email, including the spam folder.</>}
              </p>

              {error && (
                <div className="mb-4 p-3 rounded-xl bg-red-50 border border-red-100 text-red-600 text-sm">
                  {error}
                </div>
              )}
              {notice && (
                <div className="mb-4 p-3 rounded-xl bg-green-50 border border-green-100 text-green-700 text-sm">
                  {notice}
                </div>
              )}

              <form onSubmit={verify} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">6-digit code</label>
                  <input
                    value={code}
                    onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    required
                    autoFocus
                    inputMode="numeric"
                    placeholder="123456"
                    className="w-full border border-gray-300 rounded-xl px-4 py-3 text-gray-900 placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-center text-2xl font-bold tracking-[0.4em] tabular-nums"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">Choose a password</label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    minLength={6}
                    placeholder="At least 6 characters"
                    className="w-full border border-gray-300 rounded-xl px-4 py-3 text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading || code.length !== 6}
                  className="w-full py-3 rounded-xl bg-gray-900 hover:bg-gray-800 disabled:opacity-60 text-white font-semibold text-sm transition-colors"
                >
                  {loading ? 'Verifying…' : 'Create my account'}
                </button>
              </form>

              <div className="flex items-center justify-between mt-4 text-sm">
                <button
                  onClick={() => { setStep('identify'); setCode(''); setError('') }}
                  className="text-gray-500 hover:text-gray-700"
                >
                  ← Change details
                </button>
                <button
                  onClick={async () => { await requestCode(); setNotice('New code sent.') }}
                  disabled={loading}
                  className="text-indigo-600 font-medium hover:text-indigo-700 disabled:opacity-50"
                >
                  Resend code
                </button>
              </div>
            </>
          )}

          {step === 'done' && (
            <div className="text-center py-4">
              <div className="w-14 h-14 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-4">
                <svg className="w-7 h-7 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h1 className="text-xl font-bold text-gray-900 mb-1">You&apos;re all set</h1>
              <p className="text-sm text-gray-500">Taking you to your account…</p>
            </div>
          )}
        </div>

        <p className="text-center text-sm text-gray-500 mt-6">
          Already set up?{' '}
          <Link href="/account/login" className="text-indigo-600 font-medium hover:text-indigo-700">
            Sign in
          </Link>
        </p>
        <p className="text-center text-sm text-gray-400 mt-3">
          <Link href="/book" className="hover:text-gray-600 transition-colors">Back to booking</Link>
        </p>
      </div>
    </div>
  )
}

export default function ClaimPage() {
  return (
    <Suspense>
      <ClaimForm />
    </Suspense>
  )
}
