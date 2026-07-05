import { apiClient } from '../../lib/api-client'
import {
  chatDeleteResponseSchema,
  chatMessageListResponseSchema,
  chatMessageResponseSchema,
  chatSessionListResponseSchema,
  chatSessionResponseSchema,
  type ChatMessage,
  type ChatSession,
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
