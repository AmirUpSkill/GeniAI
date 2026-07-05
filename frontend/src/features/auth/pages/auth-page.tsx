import { useEffect, useState } from 'react'
import { Moon, Sun } from 'lucide-react'
import { getCurrentUser, getGoogleLoginUrl } from '../api'
import { GoogleLoginButton } from '../components/google-login-button'
import { paths } from '../../../lib/paths'

type Theme = 'dark' | 'light'

export function AuthPage() {
  const [theme, setTheme] = useState<Theme>('dark')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const isDark = theme === 'dark'

  useEffect(() => {
    let isMounted = true

    getCurrentUser()
      .then(() => {
        if (isMounted) {
          window.location.assign(paths.chat)
        }
      })
      .catch(() => {
        // Staying on the auth page is expected when there is no session yet.
      })

    return () => {
      isMounted = false
    }
  }, [])

  function handleGoogleLogin() {
    try {
      setError(null)
      setIsLoading(true)
      window.location.assign(getGoogleLoginUrl())
    } catch {
      setIsLoading(false)
      setError('Unable to start Google sign in. Check the frontend env values.')
    }
  }

  function toggleTheme() {
    setTheme((currentTheme) => (currentTheme === 'dark' ? 'light' : 'dark'))
  }

  return (
    <main className="auth-page" data-theme={theme}>
      <section className="auth-shell" aria-label="Sign in to Geni">
        <div className="auth-header">
          <div className="brand-lockup" aria-label="Geni">
            <div className="brand-mark">G</div>
            <span>Geni</span>
          </div>

          <button
            aria-label={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
            className="theme-toggle"
            onClick={toggleTheme}
            type="button"
          >
            {isDark ? <Sun aria-hidden="true" size={18} /> : <Moon aria-hidden="true" size={18} />}
          </button>
        </div>

        <div className="auth-copy">
          <p>Sign in to continue to your AI workspace.</p>
        </div>

        <div className="auth-action">
          <GoogleLoginButton isLoading={isLoading} onClick={handleGoogleLogin} />
          {error ? <p className="auth-error">{error}</p> : null}
        </div>
      </section>
    </main>
  )
}
