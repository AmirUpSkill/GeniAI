import { ArrowLeft, CalendarDays, LogOut, Mail, ShieldCheck, UserRound } from 'lucide-react'
import { useEffect, useState } from 'react'
import { logout } from '../../auth/api'
import type { AuthenticatedUser } from '../../auth/schemas'
import { getProfile } from '../api'
import { paths } from '../../../lib/paths'

type ProfilePageProps = {
  onNavigate: (path: string) => void
}

type ProfileState =
  | { status: 'loading'; user: null; error: null }
  | { status: 'ready'; user: AuthenticatedUser; error: null }
  | { status: 'error'; user: null; error: string }

export function ProfilePage({ onNavigate }: ProfilePageProps) {
  const [profileState, setProfileState] = useState<ProfileState>({
    status: 'loading',
    user: null,
    error: null,
  })
  const [isLoggingOut, setIsLoggingOut] = useState(false)

  useEffect(() => {
    let isMounted = true

    getProfile()
      .then((user) => {
        if (isMounted) {
          setProfileState({ status: 'ready', user, error: null })
        }
      })
      .catch(() => {
        if (isMounted) {
          setProfileState({
            status: 'error',
            user: null,
            error: 'We could not load your profile. Please sign in again.',
          })
        }
      })

    return () => {
      isMounted = false
    }
  }, [])

  async function handleLogout() {
    setIsLoggingOut(true)

    try {
      await logout()
    } finally {
      onNavigate(paths.auth)
    }
  }

  const user = profileState.user

  return (
    <main className="profile-page">
      <section className="profile-shell" aria-labelledby="profile-title">
        <button className="back-button" onClick={() => onNavigate(paths.chat)} type="button">
          <ArrowLeft aria-hidden="true" size={18} />
          <span>Back to chat</span>
        </button>

        {profileState.status === 'loading' ? (
          <div className="profile-loading" role="status">
            Loading profile
          </div>
        ) : null}

        {profileState.status === 'error' ? (
          <div className="profile-error">
            <p>{profileState.error}</p>
            <button onClick={() => onNavigate(paths.auth)} type="button">
              Go to sign in
            </button>
          </div>
        ) : null}

        {user ? (
          <>
            <div className="profile-hero">
              <div className="profile-avatar">
                {user.avatarUrl ? (
                  <img src={user.avatarUrl} alt="" />
                ) : (
                  <UserRound aria-hidden="true" size={32} />
                )}
              </div>
              <div>
                <p className="profile-label">Profile</p>
                <h1 id="profile-title">{user.fullName}</h1>
                <p>{user.email}</p>
              </div>
            </div>

            <dl className="profile-details">
              <div>
                <dt>
                  <Mail aria-hidden="true" size={18} />
                  Email
                </dt>
                <dd>{user.email}</dd>
              </div>
              <div>
                <dt>
                  <ShieldCheck aria-hidden="true" size={18} />
                  Provider
                </dt>
                <dd>{formatProvider(user.provider)}</dd>
              </div>
              <div>
                <dt>
                  <CalendarDays aria-hidden="true" size={18} />
                  Created
                </dt>
                <dd>{formatDate(user.createdAt)}</dd>
              </div>
            </dl>

            <button
              className="logout-button"
              disabled={isLoggingOut}
              onClick={handleLogout}
              type="button"
            >
              <LogOut aria-hidden="true" size={18} />
              <span>{isLoggingOut ? 'Logging out' : 'Logout'}</span>
            </button>
          </>
        ) : null}
      </section>
    </main>
  )
}

function formatProvider(provider: string) {
  return provider.charAt(0).toUpperCase() + provider.slice(1)
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}
