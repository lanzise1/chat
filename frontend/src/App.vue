<script setup lang="ts">
import ChatView from './components/ChatView.vue'
</script>

<template>
  <div class="h-full flex flex-col">
    <header class="h-14 shrink-0 border-b border-slate-200 bg-white flex items-center px-6">
      <div class="flex items-center gap-2">
        <div class="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500"></div>
        <div>
          <div class="text-sm font-semibold">LangChain Chat</div>
          <div class="text-xs text-slate-500">Vue 3 · TypeScript · Tailwind · Streaming</div>
        </div>
      </div>
    </header>
    <main class="flex-1 min-h-0">
      <ChatView />
    </main>
  </div>
</template>
