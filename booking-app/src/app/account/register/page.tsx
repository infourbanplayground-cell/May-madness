'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Lockup } from '@/components/Brand'

export default function RegisterPage() {
  const router = useRouter()

  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')

    if (password !== confirmPassword) {
      setError('Passwords do not match')
      return
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters')
      return
    }

    setLoading(true)

    try {
      const res = await fetch('/api/account/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name.trim(), phone: phone.trim(), password }),
      })
      const data = await res.json()
      if (!res.ok) {
        setError(data.error || 'Registration failed')
        setLoading(false)
        return
      }
      router.push('/account')
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
          <h1 className="h-display text-3xl mb-1">Create account</h1>
          <p className="text-sm text-faint mb-6">Join to book courts online</p>

          {error && (
            <div className="mb-4 p-3 rounded-xl bg-flare/15 border border-flare/40 text-[#ff9a96] text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-cream/90 mb-1.5">
                Full name
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                placeholder="Your name"
                className="w-full border border-hair rounded-xl px-4 py-3 text-cream placeholder-faint/60 focus:outline-none focus:border-ember text-sm"
              />
            </div>

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
                placeholder="At least 6 characters"
                className="w-full border border-hair rounded-xl px-4 py-3 text-cream placeholder-faint/60 focus:outline-none focus:border-ember text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-cream/90 mb-1.5">
                Confirm password
              </label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                placeholder="Repeat password"
                className="w-full border border-hair rounded-xl px-4 py-3 text-cream placeholder-faint/60 focus:outline-none focus:border-ember text-sm"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-xl bg-ember hover:bg-ember-deep disabled:opacity-60 disabled:cursor-not-allowed text-ink font-semibold text-sm transition-colors shadow-sm"
            >
              {loading ? 'Creating account…' : 'Create account'}
            </button>
          </form>
        </div>

        <p className="text-center text-sm text-faint mt-6">
          Already have an account?{' '}
          <Link href="/account/login" className="text-ember font-medium hover:text-gold">
            Sign in
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
