import { apiClient } from '../../lib/api-client'
import {
  fileSearchDeleteResponseSchema,
  fileSearchDocumentResponseSchema,
  type FileSearchDocument,
} from './schemas'

export async function getFileSearchDocument(
  chatSessionId: string,
): Promise<FileSearchDocument | null> {
  const response = await apiClient(`/api/chat/sessions/${chatSessionId}/document`)
  return fileSearchDocumentResponseSchema.parse(response).data
}

export async function uploadFileSearchDocument(
  chatSessionId: string,
  file: File,
): Promise<FileSearchDocument> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await apiClient(`/api/chat/sessions/${chatSessionId}/document`, {
    body: formData,
    method: 'POST',
  })
  const document = fileSearchDocumentResponseSchema.parse(response).data
  if (document === null) {
    throw new Error('The upload completed without a document.')
  }
  return document
}

export async function deleteFileSearchDocument(chatSessionId: string): Promise<void> {
  const response = await apiClient(`/api/chat/sessions/${chatSessionId}/document`, {
    method: 'DELETE',
  })
  fileSearchDeleteResponseSchema.parse(response)
}
