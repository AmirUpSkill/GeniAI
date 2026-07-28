import { apiClient } from '../../lib/api-client'
import { ApiError } from '../../lib/api-client'
import { env } from '../../lib/env'
import {
  chatDeleteResponseSchema,
  chatMessageListResponseSchema,
  chatMessageResponseSchema,
  chatSessionListResponseSchema,
  chatSessionResponseSchema,
  chatTurnResponseSchema,
  chatTurnStreamEventSchema,
  type ChatMessage,
  type ChatSession,
  type ChatTurnStreamEvent,
} from './schemas'

export async function createChatSession(title = 'New chat'): Promise<ChatSession> {
  const response = await apiClient('/api/chat/sessions', {
    body: { title },
    method: 'POST',
  })
  return chatSessionResponseSchema.parse(response).data
}

export async function listChatSessions(): Promise<ChatSession[]> {
  const response = await apiClient('/api/chat/sessions')
  return chatSessionListResponseSchema.parse(response).data
}

export async function updateChatSessionTitle(
  chatSessionId: string,
  title: string,
): Promise<ChatSession> {
  const response = await apiClient(`/api/chat/sessions/${chatSessionId}`, {
    body: { title },
    method: 'PATCH',
  })
  return chatSessionResponseSchema.parse(response).data
}

export async function deleteChatSession(chatSessionId: string) {
  const response = await apiClient(`/api/chat/sessions/${chatSessionId}`, {
    method: 'DELETE',
  })
  return chatDeleteResponseSchema.parse(response)
}

export async function listChatMessages(chatSessionId: string): Promise<ChatMessage[]> {
  const response = await apiClient(`/api/chat/sessions/${chatSessionId}/messages`)
  return chatMessageListResponseSchema.parse(response).data
}

export async function createChatMessage(
  chatSessionId: string,
  content: string,
): Promise<ChatMessage> {
  const response = await apiClient(`/api/chat/sessions/${chatSessionId}/messages`, {
    body: { content, role: 'user' },
    method: 'POST',
  })
  return chatMessageResponseSchema.parse(response).data
}

export async function createChatTurn(
  chatSessionId: string,
  content: string,
): Promise<{ assistantMessage: ChatMessage; userMessage: ChatMessage }> {
  const response = await apiClient(`/api/chat/sessions/${chatSessionId}/turns`, {
    body: { content },
    method: 'POST',
  })
  return chatTurnResponseSchema.parse(response).data
}

export async function streamChatTurn(
  chatSessionId: string,
  content: string,
  options: {
    onEvent: (event: ChatTurnStreamEvent) => void
    signal: AbortSignal
  },
): Promise<void> {
  const response = await fetch(
    new URL(`/api/chat/sessions/${chatSessionId}/turns/stream`, env.VITE_API_BASE_URL),
    {
      body: JSON.stringify({ content }),
      credentials: 'include',
      headers: {
        Accept: 'application/x-ndjson',
        'Content-Type': 'application/json',
      },
      method: 'POST',
      signal: options.signal,
    },
  )

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as {
      error?: { code?: string; message?: string }
    } | null
    throw new ApiError(
      payload?.error?.message ?? `Request failed with status ${response.status}`,
      response.status,
      payload?.error?.code,
    )
  }
  if (response.body === null) {
    throw new Error('The streaming response did not include a body.')
  }

  await readChatTurnStream(response.body, options.onEvent)
}

export async function readChatTurnStream(
  body: ReadableStream<Uint8Array>,
  onEvent: (event: ChatTurnStreamEvent) => void,
): Promise<void> {
  const reader = body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let terminalEventReceived = false

  function consumeLine(line: string) {
    if (line.trim().length === 0) {
      return
    }
    const event = chatTurnStreamEventSchema.parse(JSON.parse(line))
    onEvent(event)
    if (event.type === 'turn.completed' || event.type === 'turn.error') {
      terminalEventReceived = true
    }
  }

  while (true) {
    const { done, value } = await reader.read()
    buffer += decoder.decode(value, { stream: !done })
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''
    for (const line of lines) {
      consumeLine(line)
    }
    if (done) {
      if (buffer.trim().length > 0) {
        consumeLine(buffer)
      }
      break
    }
  }

  if (!terminalEventReceived) {
    throw new Error('The response stream ended before the turn completed.')
  }
}
