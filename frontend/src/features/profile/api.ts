import { apiClient } from '../../lib/api-client'
import {
  authenticatedUserResponseSchema,
  type AuthenticatedUser,
} from '../auth/schemas'

export async function getProfile(): Promise<AuthenticatedUser> {
  const response = await apiClient('/api/profile/me')
  return authenticatedUserResponseSchema.parse(response).data
}
