import { z } from 'zod'

export const fileSearchDocumentSchema = z.object({
  id: z.string(),
  chatSessionId: z.string(),
  originalName: z.string(),
  contentType: z.string(),
  sizeBytes: z.number(),
  status: z.enum(['pending', 'indexing', 'ready', 'failed']),
  failureMessage: z.string().nullable(),
  createdAt: z.string(),
  updatedAt: z.string(),
  readyAt: z.string().nullable(),
})

export const fileSearchDocumentResponseSchema = z.object({
  success: z.boolean(),
  data: fileSearchDocumentSchema.nullable(),
})

export const fileSearchCitationSchema = z.object({
  id: z.string(),
  documentId: z.string(),
  position: z.number(),
  fileName: z.string(),
  pageNumber: z.number().nullable(),
  sourceExcerpt: z.string(),
  mediaId: z.string().nullable(),
  customMetadata: z.record(z.string(), z.unknown()).nullable(),
})

export const fileSearchDeleteResponseSchema = z.object({
  success: z.boolean(),
  message: z.string(),
})

export type FileSearchDocument = z.infer<typeof fileSearchDocumentSchema>
export type FileSearchCitation = z.infer<typeof fileSearchCitationSchema>
