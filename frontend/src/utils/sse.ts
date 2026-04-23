/**
 * Parse an SSE stream (`text/event-stream`) and invoke `onData` for each
 * `data:` line's payload. Handles multi-line events and chunked reads.
 */
export async function parseSSEStream(
  body: ReadableStream<Uint8Array>,
  onData: (data: string) => void,
): Promise<void> {
  const reader = body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })

      // SSE 事件以 \n\n 分隔
      const parts = buffer.split('\n\n')
      buffer = parts.pop() ?? ''

      for (const part of parts) {
        // 一个事件可能有多行,我们只关心 data:
        const dataLines = part
          .split('\n')
          .filter((line) => line.startsWith('data:'))
          .map((line) => line.slice(5).trimStart())

        if (dataLines.length === 0) continue
        const payload = dataLines.join('\n')
        if (payload) onData(payload)
      }
    }
  } finally {
    reader.releaseLock()
  }
}
