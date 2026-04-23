import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'

const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
  highlight(code, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(code, { language: lang, ignoreIllegals: true }).value
      } catch {
        /* fall through */
      }
    }
    try {
      return hljs.highlightAuto(code).value
    } catch {
      return ''
    }
  },
})

export function renderMarkdown(text: string): string {
  return md.render(text || '')
}
