import { useState } from 'react'
import { Link, useSearchParams, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useMutation } from '@tanstack/react-query'
import { authApi } from '../api/auth'
import { Logo } from '../components/ui/logo'

const MIN_PASSWORD_LENGTH = 8

export function ResetPasswordPage() {
  const { t } = useTranslation('auth')
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const token = searchParams.get('token') || ''
  const [newPassword, setNewPassword] = useState('')
  const [confirmation, setConfirmation] = useState('')

  const confirmReset = useMutation({
    mutationFn: () => authApi.confirmPasswordReset(token, newPassword),
    onSuccess: () => setTimeout(() => navigate('/login'), 1500),
  })

  const passwordsMatch = newPassword === confirmation
  const isLongEnough = newPassword.length >= MIN_PASSWORD_LENGTH
  const canSubmit = !!token && passwordsMatch && isLongEnough && !confirmReset.isPending

  const handleSubmit = (event) => {
    event.preventDefault()
    if (canSubmit) confirmReset.mutate()
  }

  if (!token) {
    return (
      <CenteredCard>
        <p className="text-sm text-red-500">{t('reset.missingToken')}</p>
        <BackToLogin />
      </CenteredCard>
    )
  }

  if (confirmReset.isSuccess) {
    return (
      <CenteredCard>
        <p className="text-sm text-gray-700 dark:text-gray-200">{t('reset.success')}</p>
      </CenteredCard>
    )
  }

  return (
    <CenteredCard>
      <h1 className="text-base font-semibold text-gray-800 dark:text-gray-100 text-center">{t('reset.title')}</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        {confirmReset.isError && (
          <p className="text-sm text-red-500" role="alert">
            {confirmReset.error?.response?.data?.detail || t('reset.failure')}
          </p>
        )}
        <PasswordField
          id="new-password"
          label={t('reset.newPassword')}
          value={newPassword}
          onChange={setNewPassword}
          autoComplete="new-password"
        />
        <PasswordField
          id="confirm-password"
          label={t('reset.confirmPassword')}
          value={confirmation}
          onChange={setConfirmation}
          autoComplete="new-password"
        />
        {!isLongEnough && newPassword.length > 0 && (
          <p className="text-xs text-gray-500 dark:text-gray-400">{t('reset.minLength', { min: MIN_PASSWORD_LENGTH })}</p>
        )}
        {!passwordsMatch && confirmation.length > 0 && (
          <p className="text-xs text-red-500">{t('reset.mismatch')}</p>
        )}
        <button
          type="submit"
          disabled={!canSubmit}
          className="w-full bg-gray-900 text-white rounded-md py-2 text-sm font-medium hover:bg-gray-700 disabled:opacity-50"
        >
          {confirmReset.isPending ? t('reset.updating') : t('reset.update')}
        </button>
      </form>
      <BackToLogin />
    </CenteredCard>
  )
}

function CenteredCard({ children }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 dark:bg-gray-800">
      <div className="bg-white dark:bg-gray-900 shadow-md rounded-xl p-8 w-80 space-y-4">
        <div className="flex justify-center pb-2"><Logo size={32} /></div>
        {children}
      </div>
    </div>
  )
}

function PasswordField({ id, label, value, onChange, autoComplete }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1" htmlFor={id}>{label}</label>
      <input
        id={id}
        type="password"
        autoComplete={autoComplete}
        className="w-full border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-400"
        value={value}
        onChange={event => onChange(event.target.value)}
        required
      />
    </div>
  )
}

function BackToLogin() {
  const { t } = useTranslation('auth')
  return (
    <p className="text-center text-sm">
      <Link to="/login" className="text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-gray-100">{t('forgot.back')}</Link>
    </p>
  )
}
