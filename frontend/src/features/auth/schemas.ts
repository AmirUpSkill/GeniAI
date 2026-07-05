import { z } from 'zod'

export const authenticatedUserSchema = z.object({
  id: z.string(),
  email: z.string().email(),
  fullName: z.string(),
  avatarUrl: z.string().nullable(),
  provider: z.string(),
  createdAt: z.string(),
  updatedAt: z.string(),
})

export const authenticatedUserResponseSchema = z.object({
  success: z.boolean(),
  data: authenticatedUserSchema,
})

export const logoutResponseSchema = z.object({
  success: z.boolean(),
  message: z.string(),
})

export type AuthenticatedUser = z.infer<typeof authenticatedUserSchema>
