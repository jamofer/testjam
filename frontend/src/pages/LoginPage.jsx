import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useLogin } from '../hooks/useAuth'
import { Logo } from '../components/ui/logo'
import { loginErrorMessage } from '../lib/auth-errors'

export function LoginPage() {
  const { t } = useTranslation('auth')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const login = useLogin()
  const navigate = useNavigate()

  const handleSubmit = (event) => {
    event.preventDefault()
    login.mutate({ username, password }, {
      onSuccess: () => navigate('/projects'),
    })
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 dark:bg-gray-800">
      <form onSubmit={handleSubmit} className="bg-white dark:bg-gray-900 shadow-md rounded-xl p-8 w-80 space-y-4">
        <div className="flex justify-center pb-2"><Logo size={32} /></div>
        {login.isError && (
          <p className="text-sm text-red-500" role="alert">
            {loginErrorMessage(login.error)}
          </p>
        )}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1" htmlFor="username">{t('login.username')}</label>
          <input
            id="username"
            name="username"
            autoComplete="username"
            className="w-full border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-400"
            value={username}
            onChange={event => setUsername(event.target.value)}
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1" htmlFor="password">{t('login.password')}</label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            className="w-full border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-400"
            value={password}
            onChange={event => setPassword(event.target.value)}
            required
          />
        </div>
        <button
          type="submit"
          disabled={login.isPending}
          className="w-full bg-gray-900 text-white rounded-md py-2 text-sm font-medium hover:bg-gray-700 disabled:opacity-50"
        >
          {login.isPending ? t('login.signingIn') : t('login.signIn')}
        </button>
        <p className="text-center text-sm">
          <Link to="/forgot-password" className="text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-gray-100">
            {t('login.forgotPassword')}
          </Link>
        </p>
      </form>
    </div>
  )
}
