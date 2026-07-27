import { useCallback, useEffect, useState } from 'react'

import { ApiError } from '../../lib/api-client'
import {
  deleteFileSearchDocument,
  getFileSearchDocument,
  uploadFileSearchDocument,
} from './api'
import type { FileSearchDocument } from './schemas'

const STATUS_POLL_INTERVAL_MS = 2_000

type UseFileSearchDocumentResult = {
  document: FileSearchDocument | null
  error: string | null
  isLoading: boolean
  remove: () => Promise<void>
  upload: (file: File, targetChatSessionId?: string) => Promise<void>
}

/**
 * Owns the complete frontend lifecycle for one chat-scoped document.
 *
 * Polling is active only while Gemini is preparing the document. The hook stops
 * automatically when the document becomes ready, fails, or the chat changes.
 */
export function useFileSearchDocument(
  chatSessionId: string | null,
): UseFileSearchDocumentResult {
  const [document, setDocument] = useState<FileSearchDocument | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadDocument = useCallback(
    async (showLoading: boolean) => {
      if (chatSessionId === null) {
        setDocument(null)
        setError(null)
        return null
      }

      if (showLoading) {
        setIsLoading(true)
      }
      try {
        const nextDocument = await getFileSearchDocument(chatSessionId)
        setDocument(nextDocument)
        setError(null)
        return nextDocument
      } catch (caughtError) {
        setError(getErrorMessage(caughtError, 'Unable to load the chat document.'))
        return null
      } finally {
        if (showLoading) {
          setIsLoading(false)
        }
      }
    },
    [chatSessionId],
  )

  useEffect(() => {
    void loadDocument(true)
  }, [loadDocument])

  useEffect(() => {
    if (document?.status !== 'pending' && document?.status !== 'indexing') {
      return
    }
    const intervalId = window.setInterval(
      () => void loadDocument(false),
      STATUS_POLL_INTERVAL_MS,
    )
    return () => window.clearInterval(intervalId)
  }, [document?.status, loadDocument])

  const upload = useCallback(
    async (file: File, targetChatSessionId?: string) => {
      const resolvedChatSessionId = targetChatSessionId ?? chatSessionId
      if (resolvedChatSessionId === null) {
        throw new Error('Create a chat before attaching a document.')
      }
      setIsLoading(true)
      setError(null)
      try {
        const nextDocument = await uploadFileSearchDocument(resolvedChatSessionId, file)
        setDocument(nextDocument)
      } catch (caughtError) {
        const message = getErrorMessage(caughtError, 'Unable to upload this PDF.')
        setError(message)
        throw new Error(message)
      } finally {
        setIsLoading(false)
      }
    },
    [chatSessionId],
  )

  const remove = useCallback(async () => {
    if (chatSessionId === null || document === null) {
      return
    }
    setIsLoading(true)
    setError(null)
    try {
      await deleteFileSearchDocument(chatSessionId)
      setDocument(null)
    } catch (caughtError) {
      const message = getErrorMessage(caughtError, 'Unable to remove this document.')
      setError(message)
      throw new Error(message)
    } finally {
      setIsLoading(false)
    }
  }, [chatSessionId, document])

  return { document, error, isLoading, remove, upload }
}

function getErrorMessage(error: unknown, fallback: string) {
  if (error instanceof ApiError || error instanceof Error) {
    return error.message
  }
  return fallback
}
