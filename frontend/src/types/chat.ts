export type Role = 'user' | 'assistant' | 'system'

export interface ChatMessage {
  role: Role
  content: string
}

export type SSEEvent =
  | { type: 'delta'; content: string }
  | { type: 'done' }
  | { type: 'error'; message: string }
