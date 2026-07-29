import { marked } from 'marked'
import hljs from 'highlight.js/lib/core'
import DOMPurify from 'dompurify'

import javascript from 'highlight.js/lib/languages/javascript'
import typescript from 'highlight.js/lib/languages/typescript'
import python from 'highlight.js/lib/languages/python'
import bash from 'highlight.js/lib/languages/bash'
import json from 'highlight.js/lib/languages/json'
import xml from 'highlight.js/lib/languages/xml'
import css from 'highlight.js/lib/languages/css'
import sql from 'highlight.js/lib/languages/sql'
import rust from 'highlight.js/lib/languages/rust'
import java from 'highlight.js/lib/languages/java'
import cpp from 'highlight.js/lib/languages/cpp'
import go from 'highlight.js/lib/languages/go'
import shell from 'highlight.js/lib/languages/shell'
import yaml from 'highlight.js/lib/languages/yaml'
import markdown from 'highlight.js/lib/languages/markdown'
import kotlin from 'highlight.js/lib/languages/kotlin'
import swift from 'highlight.js/lib/languages/swift'
import dart from 'highlight.js/lib/languages/dart'

hljs.registerLanguage('javascript', javascript)
hljs.registerLanguage('js', javascript)
hljs.registerLanguage('typescript', typescript)
hljs.registerLanguage('ts', typescript)
hljs.registerLanguage('python', python)
hljs.registerLanguage('py', python)
hljs.registerLanguage('bash', bash)
hljs.registerLanguage('sh', bash)
hljs.registerLanguage('json', json)
hljs.registerLanguage('xml', xml)
hljs.registerLanguage('html', xml)
hljs.registerLanguage('css', css)
hljs.registerLanguage('sql', sql)
hljs.registerLanguage('rust', rust)
hljs.registerLanguage('rs', rust)
hljs.registerLanguage('java', java)
hljs.registerLanguage('cpp', cpp)
hljs.registerLanguage('c', cpp)
hljs.registerLanguage('go', go)
hljs.registerLanguage('shell', shell)
hljs.registerLanguage('yaml', yaml)
hljs.registerLanguage('yml', yaml)
hljs.registerLanguage('markdown', markdown)
hljs.registerLanguage('md', markdown)
hljs.registerLanguage('kotlin', kotlin)
hljs.registerLanguage('swift', swift)
hljs.registerLanguage('dart', dart)

function escapeHtml(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
}

function escapeAttr(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

const NOTE_LINK_RE = /\[([^\]]+)\]\(note:([a-f0-9-]+)(?:#([^)]*))?\)/g

function renderNoteLinks(html: string): string {
  return html.replace(NOTE_LINK_RE, (_match, displayText, noteId, heading) => {
    const href = heading
      ? `/notes-space?noteId=${encodeURIComponent(noteId)}&heading=${encodeURIComponent(heading)}`
      : `/notes-space?noteId=${encodeURIComponent(noteId)}`
    return `<a href="${href}" class="text-secondary underline hover:text-secondary/80 cursor-pointer" data-note-link="${escapeHtml(noteId)}">${escapeHtml(displayText)}</a>`
  })
}

const PURIFY_CONFIG = {
  ALLOWED_TAGS: [
    'p', 'br', 'strong', 'em', 's', 'del', 'code', 'pre', 'blockquote',
    'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'a', 'span', 'div', 'img',
    'button', 'hr',
  ],
  ALLOWED_ATTR: [
    'href', 'target', 'rel', 'class', 'style',
    'data-note-link', 'data-copy-code', 'data-lang',
    'src', 'alt', 'title',
  ],
  FORCE_BODY: true,
}

let markedConfigured = false

const renderCache = new Map<string, string>()
const CACHE_MAX = 200

function ensureMarkedConfigured() {
  if (markedConfigured) return
  markedConfigured = true

  const renderer: Partial<import('marked').RendererObject> = {
    code({ text, lang }: { text: string; lang?: string | null }) {
      const language = lang && hljs.getLanguage(lang) ? lang : null
      let highlighted: string
      try {
        highlighted = language
          ? hljs.highlight(text, { language }).value
          : hljs.highlightAuto(text).value
      } catch {
        highlighted = escapeHtml(text)
      }
      const langLabel = language || 'text'
      return `<div class="ai-code-block" data-lang="${escapeHtml(langLabel)}"><div class="ai-code-header"><span class="ai-code-lang">${escapeHtml(langLabel)}</span><button class="ai-code-copy" data-copy-code="${escapeAttr(text)}"><span class="material-symbols-outlined text-[12px]">content_copy</span></button></div><pre><code class="hljs language-${escapeHtml(langLabel)}">${highlighted}</code></pre></div>`
    },
    codespan({ text }: { text: string }) {
      return `<code class="ai-inline-code">${text}</code>`
    },
    link({ href, text }: { href: string; text: string }) {
      if (href.startsWith('note:')) return `[${text}](${href})`
      return `<a href="${escapeHtml(href)}" target="_blank" rel="noopener" class="text-secondary underline hover:text-secondary/80">${text}</a>`
    },
  }

  marked.use({ renderer, breaks: true })
}

export function renderMarkdown(text: string): string {
  if (!text) return ''
  const cached = renderCache.get(text)
  if (cached) return cached
  ensureMarkedConfigured()
  let html = marked.parse(text, { async: false }) as string
  html = renderNoteLinks(html)
  html = html.replace(/<table>/g, '<div style="overflow-x:auto;max-width:100%"><table class="ai-table">').replace(/<\/table>/g, '</table></div>')
  const result = DOMPurify.sanitize(html, PURIFY_CONFIG)
  if (renderCache.size >= CACHE_MAX) {
    const first = renderCache.keys().next().value!
    renderCache.delete(first)
  }
  renderCache.set(text, result)
  return result
}

export function renderStreamingMarkdown(text: string): string {
  if (!text) return '<span class="ai-cursor"></span>'
  ensureMarkedConfigured()
  let html = marked.parse(text, { async: false }) as string
  html = renderNoteLinks(html)
  html = html.replace(/<table>/g, '<div style="overflow-x:auto;max-width:100%"><table class="ai-table">').replace(/<\/table>/g, '</table></div>')
  html = DOMPurify.sanitize(html, PURIFY_CONFIG)
  return html + '<span class="ai-cursor"></span>'
}
