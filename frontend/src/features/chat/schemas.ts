import { z } from 'zod'

export const chatSessionSchema = z.object({
  id: z.string(),
  title: z.string(),
  summary: z.string().nullable(),
  createdAt: z.string(),
  updatedAt: z.string(),
})

export const chatSessionResponseSchema = z.object({
  success: z.boolean(),
  data: chatSessionSchema,
})

export const chatSessionListResponseSchema = z.object({
  success: z.boolean(),
  data: z.array(chatSessionSchema),
})

export const chatMessageSchema = z.object({
  id: z.string(),
  chatSessionId: z.string(),
  role: z.enum(['user', 'assistant', 'system']),
  content: z.string(),
  createdAt: z.string(),
})

export const chatMessageResponseSchema = z.object({
  success: z.boolean(),
  data: chatMessageSchema,
})

export const chatMessageListResponseSchema = z.object({
  success: z.boolean(),
  data: z.array(chatMessageSchema),
})

export const chatDeleteResponseSchema = z.object({
  success: z.boolean(),
  message: z.string(),
})

export const chatTurnResponseSchema = z.object({
  success: z.boolean(),
  data: z.object({
    userMessage: chatMessageSchema,
    assistantMessage: chatMessageSchema,
  }),
})

export type ChatMessage = z.infer<typeof chatMessageSchema>
export type ChatSession = z.infer<typeof chatSessionSchema>
