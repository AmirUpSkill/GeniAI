import { env } from '../../lib/env'
import { paths } from '../../lib/paths'

export function getGoogleLoginUrl() {
  const url = new URL('/api/auth/google/login', env.VITE_API_BASE_URL)
  const redirectUri = new URL(paths.chat, env.VITE_APP_URL)

  url.searchParams.set('redirectUri', redirectUri.toString())

  return url.toString()
}
