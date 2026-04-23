export function scrollToBottom(el: HTMLElement | null): void {
  if (el) el.scrollTop = el.scrollHeight
}

export function autosizeTextarea(el: HTMLTextAreaElement | null, maxHeight = 200): void {
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, maxHeight) + 'px'
}
