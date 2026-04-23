<script setup lang="ts">
import { nextTick, onMounted, ref, watch } from 'vue'

import { useChat } from '../composables/useChat'
import { autosizeTextarea, scrollToBottom } from '../utils/dom'
import { renderMarkdown } from '../utils/markdown'

const { messages, loading, errorMsg, send, stop, clear } = useChat()

const input = ref('')
const scroller = ref<HTMLDivElement | null>(null)
const textarea = ref<HTMLTextAreaElement | null>(null)

function scheduleScroll() {
  nextTick(() => scrollToBottom(scroller.value))
}

watch(messages, scheduleScroll, { deep: true })
watch(input, () => autosizeTextarea(textarea.value))
onMounted(() => autosizeTextarea(textarea.value))

async function onSend() {
  const text = input.value
  if (!text.trim() || loading.value) return
  input.value = ''
  scheduleScroll()
  await send(text)
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
    e.preventDefault()
    onSend()
  }
}
</script>

<template>
  <div class="h-full flex flex-col max-w-3xl mx-auto w-full">
    <div ref="scroller" class="flex-1 overflow-y-auto px-4 py-6 space-y-6">
      <div
        v-if="messages.length === 0"
        class="h-full flex flex-col items-center justify-center text-center text-slate-400"
      >
        <div class="text-4xl mb-2">💬</div>
        <div class="text-sm">开始一次对话吧,支持 Markdown 与流式输出</div>
      </div>

      <div
        v-for="(m, i) in messages"
        :key="i"
        class="flex gap-3"
        :class="m.role === 'user' ? 'justify-end' : 'justify-start'"
      >
        <div
          v-if="m.role === 'assistant'"
          class="w-8 h-8 shrink-0 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-white text-xs font-bold"
        >
          AI
        </div>

        <div
          class="max-w-[85%] rounded-2xl px-4 py-3 shadow-sm"
          :class="
            m.role === 'user'
              ? 'bg-indigo-600 text-white rounded-br-sm'
              : 'bg-white text-slate-800 rounded-bl-sm border border-slate-200'
          "
        >
          <template v-if="m.role === 'assistant'">
            <div
              class="markdown-body"
              :class="{ 'typing-cursor': loading && i === messages.length - 1 }"
              v-html="renderMarkdown(m.content)"
            />
          </template>
          <template v-else>
            <div class="whitespace-pre-wrap break-words">{{ m.content }}</div>
          </template>
        </div>

        <div
          v-if="m.role === 'user'"
          class="w-8 h-8 shrink-0 rounded-full bg-slate-200 flex items-center justify-center text-slate-700 text-xs font-bold"
        >
          U
        </div>
      </div>

      <div
        v-if="errorMsg"
        class="text-sm text-red-600 bg-red-50 border border-red-200 rounded-md px-3 py-2"
      >
        {{ errorMsg }}
      </div>
    </div>

    <div class="shrink-0 border-t border-slate-200 bg-white p-3">
      <div class="flex items-end gap-2">
        <textarea
          ref="textarea"
          v-model="input"
          rows="1"
          placeholder="输入消息… (Enter 发送 / Shift+Enter 换行)"
          class="flex-1 resize-none rounded-xl border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent"
          @keydown="onKeydown"
        />

        <button
          v-if="loading"
          class="h-10 px-4 rounded-xl bg-rose-500 hover:bg-rose-600 text-white text-sm font-medium transition"
          @click="stop"
        >
          停止
        </button>
        <button
          v-else
          :disabled="input.trim().length === 0"
          class="h-10 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white text-sm font-medium transition"
          @click="onSend"
        >
          发送
        </button>

        <button
          :disabled="loading || messages.length === 0"
          class="h-10 px-3 rounded-xl bg-slate-100 hover:bg-slate-200 disabled:opacity-50 disabled:cursor-not-allowed text-slate-700 text-sm transition"
          title="清空对话"
          @click="clear"
        >
          清空
        </button>
      </div>
      <div class="mt-1.5 text-[11px] text-slate-400 px-1">
        多轮对话已启用,上下文会一并发送给后端。
      </div>
    </div>
  </div>
</template>
