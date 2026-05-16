import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { authApi } from '../api/auth'
import { Logo } from '../components/ui/logo'

export function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const requestReset = useMutation({
    mutationFn: (address) => authApi.requestPasswordReset(address),
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    requestReset.mutate(email)
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 dark:bg-gray-800">
      <form onSubmit={handleSubmit} className="bg-white dark:bg-gray-900 shadow-md rounded-xl p-8 w-80 space-y-4">
        <div className="flex justify-center pb-2"><Logo size={32} /></div>
        <h1 className="text-base font-semibold text-gray-800 dark:text-gray-100 text-center">Forgot your password?</h1>
        {requestReset.isSuccess ? (
          <p className="text-sm text-gray-700 dark:text-gray-200">
            If that email is registered, we just sent a reset link. Check your inbox.
          </p>
        ) : (
          <>
            <p className="text-sm text-gray-600 dark:text-gray-300">
              Enter the email tied to your account and we'll send a reset link.
            </p>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1" htmlFor="email">Email</label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                className="w-full border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-400"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
              />
            </div>
            <button
              type="submit"
              disabled={requestReset.isPending}
              className="w-full bg-gray-900 text-white rounded-md py-2 text-sm font-medium hover:bg-gray-700 disabled:opacity-50"
            >
              {requestReset.isPending ? 'Sending…' : 'Send reset link'}
            </button>
          </>
        )}
        <p className="text-center text-sm">
          <Link to="/login" className="text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-gray-100">Back to sign in</Link>
        </p>
      </form>
    </div>
  )
}
