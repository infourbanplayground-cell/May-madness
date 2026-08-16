'use client'

import { useState, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { Lockup } from '@/components/Brand'

function LoginForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const next = searchParams.get('next') || '/account'

  const [phone, setPhone] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const res = await fetch('/api/account/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone: phone.trim(), password }),
      })
      const data = await res.json()
      if (!res.ok) {
        setError(data.error || 'Login failed')
        setLoading(false)
        return
      }
      router.push(next)
    } catch {
      setError('Network error. Please try again.')
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen heat-bg flex flex-col items-center justify-center px-4">
      <div className="w-full max-w-sm">
        {/* Logo / brand */}
        <div className="flex justify-center mb-8">
          <Lockup height={112} />
        </div>

        <div className="bg-surface rounded-2xl border border-hair shadow-sm p-8">
          <h1 className="h-display text-3xl mb-1">Welcome back</h1>
          <p className="text-sm text-faint mb-6">Sign in to your member account</p>

          {error && (
            <div className="mb-4 p-3 rounded-xl bg-flare/15 border border-flare/40 text-[#ff9a96] text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-cream/90 mb-1.5">
                Phone number
              </label>
              <input
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                required
                placeholder="9123 4567"
                className="w-full border border-hair rounded-xl px-4 py-3 text-cream placeholder-faint/60 focus:outline-none focus:border-ember text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-cream/90 mb-1.5">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder="Enter your password"
                className="w-full border border-hair rounded-xl px-4 py-3 text-cream placeholder-faint/60 focus:outline-none focus:border-ember text-sm"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-xl bg-ember hover:bg-ember-deep disabled:opacity-60 disabled:cursor-not-allowed text-ink font-semibold text-sm transition-colors shadow-sm"
            >
              {loading ? 'Signing in…' : 'Sign in'}
            </button>
          </form>
        </div>

        <div className="mt-6 p-4 rounded-xl bg-ember/10 border border-ember/30">
          <p className="text-sm text-cream font-medium mb-0.5">Played here before?</p>
          <p className="text-sm text-warm">
            If you&apos;ve booked with us previously we already have your details.{' '}
            <Link href="/account/claim" className="font-semibold underline hover:text-gold">
              Set up your account
            </Link>{' '}
            with a code instead of starting from scratch.
          </p>
        </div>

        <p className="text-center text-sm text-faint mt-5">
          New to Urban Playground?{' '}
          <Link href="/account/register" className="text-ember font-medium hover:text-gold">
            Create an account
          </Link>
        </p>

        <p className="text-center text-sm text-faint mt-3">
          <Link href="/book" className="hover:text-warm transition-colors">
            Back to booking
          </Link>
        </p>
      </div>
    </div>
  )
}

export default function LoginPage() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  )
}
