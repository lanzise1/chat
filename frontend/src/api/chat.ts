import type { ChatMessage, SSEEvent } from '../types/chat'
import { parseSSEStream } from '../utils/sse'
import { request } from './http'

export interface ChatStreamOptions {
  messages: ChatMessage[]
  signal?: AbortSignal
  onEvent: (event: SSEEvent) => void
}

/**
 * POST /api/chat and stream the SSE response, dispatching each typed event.
 * Resolves when the stream closes; rejects on network / non-2xx / abort.
 */
export async function chatStream(options: ChatStreamOptions): Promise<void> {
  const { messages, signal, onEvent } = options

  const response = await request({
    url: '/api/chat',
    method: 'POST',
    body: JSON.stringify({ messages }),
    signal,
  })

  if (!response.body) {
    throw new Error('Response has no body; streaming is not supported by this transport.')
  }

  await parseSSEStream(response.body, (data) => {
    try {
      const event = JSON.parse(data) as SSEEvent
      onEvent(event)
    } catch {
      // Malformed frame — ignore.
    }
  })
}

export async function getHealth(): Promise<{ status: string; model: string }> {
  const response = await request({ url: '/api/health', method: 'GET' })
  return response.json()
}
