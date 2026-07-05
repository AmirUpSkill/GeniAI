import { env } from '../../lib/env'
import { paths } from '../../lib/paths'
import { apiClient } from '../../lib/api-client'
import {
  authenticatedUserResponseSchema,
  logoutResponseSchema,
  type AuthenticatedUser,
} from './schemas'

export function getGoogleLoginUrl() {
  const url = new URL('/api/auth/google/login', env.VITE_API_BASE_URL)
  const redirectUri = new URL(paths.chat, env.VITE_APP_URL)

  url.searchParams.set('redirectUri', redirectUri.toString())

  return url.toString()
}

export async function getCurrentUser(): Promise<AuthenticatedUser> {
  const response = await apiClient('/api/auth/me')
  return authenticatedUserResponseSchema.parse(response).data
}

export async function logout() {
  const response = await apiClient('/api/auth/logout', { method: 'POST' })
  return logoutResponseSchema.parse(response)
}
