import { computed, reactive, ref } from 'vue'

import { chatStream } from '../api/chat'
import { ApiError } from '../api/http'
import type { ChatMessage } from '../types/chat'

export function useChat() {
  const messages = reactive<ChatMessage[]>([])
  const loading = ref(false)
  const errorMsg = ref<string | null>(null)

  let controller: AbortController | null = null

  const isEmpty = computed(() => messages.length === 0)

  function canSend(text: string): boolean {
    return text.trim().length > 0 && !loading.value
  }

  async function send(text: string): Promise<void> {
    const content = text.trim()
    if (!content || loading.value) return

    errorMsg.value = null
    messages.push({ role: 'user', content })
    messages.push({ role: 'assistant', content: '' })

    loading.value = true
    controller = new AbortController()

    // 不把空占位的 assistant 发给后端
    const history = messages
      .slice(0, -1)
      .map((m) => ({ role: m.role, content: m.content }))

    try {
      await chatStream({
        messages: history,
        signal: controller.signal,
        onEvent: (evt) => {
          const last = messages[messages.length - 1]
          if (!last) return
          if (evt.type === 'delta') {
            last.content += evt.content
          } else if (evt.type === 'error') {
            errorMsg.value = evt.message
          }
        },
      })
    } catch (err: unknown) {
      if (err instanceof DOMException && err.name === 'AbortError') {
        // user stopped — keep whatever was generated so far
      } else if (err instanceof ApiError) {
        errorMsg.value = err.message
      } else {
        errorMsg.value = (err as Error)?.message ?? '请求失败'
      }
    } finally {
      loading.value = false
      controller = null

      const last = messages[messages.length - 1]
      if (last && last.role === 'assistant' && last.content === '') {
        messages.pop()
      }
    }
  }

  function stop(): void {
    controller?.abort()
  }

  function clear(): void {
    if (loading.value) return
    messages.splice(0, messages.length)
    errorMsg.value = null
  }

  return {
    messages,
    loading,
    errorMsg,
    isEmpty,
    canSend,
    send,
    stop,
    clear,
  }
}
