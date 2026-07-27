import { describe, expect, it } from 'vitest'

import { readChatTurnStream } from './api'
import type { ChatTurnStreamEvent } from './schemas'

function streamFromChunks(chunks: Uint8Array[]) {
  return new ReadableStream<Uint8Array>({
    start(controller) {
      for (const chunk of chunks) {
        controller.enqueue(chunk)
      }
      controller.close()
    },
  })
}

function completedEvent() {
  return JSON.stringify({
    type: 'turn.completed',
    assistantMessage: {
      id: 'msg_2',
      chatSessionId: 'chat_1',
      role: 'assistant',
      content: 'Hello 🌍',
      citations: [],
      createdAt: '2026-07-27T12:00:00Z',
    },
  })
}

describe('readChatTurnStream', () => {
  it('parses events split across arbitrary UTF-8 byte boundaries', async () => {
    const encoder = new TextEncoder()
    const payload = encoder.encode(
      `${JSON.stringify({ type: 'text.delta', delta: 'Hello 🌍' })}\n${completedEvent()}\n`,
    )
    const events: ChatTurnStreamEvent[] = []

    await readChatTurnStream(
      streamFromChunks([
        payload.slice(0, 7),
        payload.slice(7, 42),
        payload.slice(42, 49),
        payload.slice(49),
      ]),
      (event) => events.push(event),
    )

    expect(events.map((event) => event.type)).toEqual([
      'text.delta',
      'turn.completed',
    ])
    expect(events[0]).toEqual({ type: 'text.delta', delta: 'Hello 🌍' })
  })

  it('parses multiple events delivered in one network chunk', async () => {
    const encoder = new TextEncoder()
    const events: ChatTurnStreamEvent[] = []

    await readChatTurnStream(
      streamFromChunks([
        encoder.encode(
          `${JSON.stringify({ type: 'text.delta', delta: 'A' })}\n${JSON.stringify({
            type: 'text.delta',
            delta: 'B',
          })}\n${completedEvent()}\n`,
        ),
      ]),
      (event) => events.push(event),
    )

    expect(events).toHaveLength(3)
  })

  it('rejects malformed events', async () => {
    const encoder = new TextEncoder()

    await expect(
      readChatTurnStream(
        streamFromChunks([encoder.encode('{"type":"unknown"}\n')]),
        () => undefined,
      ),
    ).rejects.toThrow()
  })

  it('rejects a stream without a terminal event', async () => {
    const encoder = new TextEncoder()

    await expect(
      readChatTurnStream(
        streamFromChunks([
          encoder.encode(`${JSON.stringify({ type: 'text.delta', delta: 'partial' })}\n`),
        ]),
        () => undefined,
      ),
    ).rejects.toThrow('ended before the turn completed')
  })
})
