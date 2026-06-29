import type { NoteItem } from '@/types'
import type { AiConfig } from '@/services/aiSettings'

export interface AiChatMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
}

export interface AiChatResult {
  answer: string
  contextNoteCount: number
  contextChunkCount: number
  usage?: { promptTokens: number; completionTokens: number; totalTokens: number }
}

interface NoteChunk {
  noteId: string
  title: string
  index: number
  text: string
  score: number
}

const TARGET_CHUNK_CHARS = 450
const DEFAULT_MIN_CONTEXT_TOKENS = 800

let tauriFetch: typeof fetch | null = null

async function getFetch(): Promise<typeof fetch> {
  if (tauriFetch) return tauriFetch
  try {
    const mod = await import('@tauri-apps/plugin-http')
    tauriFetch = mod.fetch
  } catch {
    tauriFetch = fetch
  }
  return tauriFetch
}

/** Strip HTML to plain text, replace images with placeholder to save tokens. */
export function htmlToPlainText(html: string, maxLen?: number): string {
  const doc = new DOMParser().parseFromString(html, 'text/html')
  doc.querySelectorAll('img').forEach(img => {
    const alt = img.getAttribute('alt') || ''
    const placeholder = document.createTextNode(alt ? `[图片: ${alt}]` : '[图片]')
    img.replaceWith(placeholder)
  })
  let text = (doc.body.textContent || '')
    .replace(/\r\n/g, '\n')
    .replace(/[\u00A0\u202F\u2007]/g, ' ')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
  if (maxLen && text.length > maxLen) {
    text = text.slice(0, maxLen) + '…'
  }
  return text
}

/** Rough token estimate (≈ 1 token per 3 chars for mixed CJK/Latin). */
export function estimateTokens(text: string): number {
  return Math.ceil(text.length / 3)
}

function splitLongText(text: string, size = TARGET_CHUNK_CHARS): string[] {
  const parts: string[] = []
  const paragraphs = text.split(/\n+/).map(p => p.trim()).filter(Boolean)
  let buf = ''
  for (const p of paragraphs) {
    if (buf && buf.length + p.length + 1 > size) {
      parts.push(buf)
      buf = p
    } else {
      buf = buf ? `${buf}\n${p}` : p
    }
    while (buf.length > size * 1.5) {
      parts.push(buf.slice(0, size))
      buf = buf.slice(size)
    }
  }
  if (buf.trim()) parts.push(buf.trim())
  return parts.length > 0 ? parts : [text.slice(0, size)]
}

/** Split note HTML into semantic chunks (headings / paragraphs). */
export function chunkNoteContent(note: NoteItem): string[] {
  const html = note.content || ''
  if (!html.trim()) return []

  const doc = new DOMParser().parseFromString(html, 'text/html')
  const rawChunks: string[] = []
  let section = ''

  const flush = () => {
    const t = section.trim()
    if (t) rawChunks.push(t)
    section = ''
  }

  for (const node of Array.from(doc.body.childNodes)) {
    if (node.nodeType !== Node.ELEMENT_NODE) {
      const t = node.textContent?.trim()
      if (t) section += (section ? '\n' : '') + t
      continue
    }
    const el = node as HTMLElement
    const tag = el.tagName.toLowerCase()
    if (/^h[1-3]$/.test(tag) && section.trim()) flush()
    const piece = htmlToPlainText(el.outerHTML).trim()
    if (!piece) continue
    if (/^h[1-3]$/.test(tag)) {
      flush()
      section = piece
    } else {
      section += (section ? '\n' : '') + piece
    }
  }
  flush()

  if (rawChunks.length === 0) {
    const plain = htmlToPlainText(html)
    return plain ? splitLongText(plain) : []
  }

  return rawChunks.flatMap(c => (c.length > TARGET_CHUNK_CHARS * 2 ? splitLongText(c) : [c]))
}

function tokenizeQuery(query: string): string[] {
  const q = query.toLowerCase().trim()
  if (!q) return []
  const cjk = q.match(/[\u4e00-\u9fff]{2,}/g) || []
  const words = q.split(/[\s,，。！？；;、]+/).filter(w => w.length >= 2)
  return [...new Set([...cjk, ...words, q])]
}

function tokenizeSearchQuery(query: string): string[] {
  const q = query.toLowerCase().trim()
  if (!q) return []
  const cjk = q.match(/[\u4e00-\u9fff]{2,}/g) || []
  const words = q.split(/[\s,，。！？；;、,.!?()[\]{}"'`<>:：|/@#$%^&*_+=~\\-]+/).filter(w => w.length >= 2)
  return [...new Set([...cjk, ...words, q])]
}

function tokenizeFinalQuery(query: string): string[] {
  const q = query.toLowerCase().trim()
  if (!q) return []
  const cjk = q.match(/[\u4e00-\u9fff]{2,}/g) || []
  const words = q
    .split(/[^\p{L}\p{N}\u4e00-\u9fff]+/u)
    .filter(w => w.length >= 2)
  return [...new Set([...cjk, ...words, q])]
}

function scoreText(text: string, query: string, titleBoost = 0): number {
  const tokens = tokenizeFinalQuery(query)
  if (tokens.length === 0) return titleBoost
  const lower = text.toLowerCase()
  let score = 0
  for (const tok of tokens) {
    if (lower.includes(tok)) score += tok.length >= 4 ? 4 : 2
  }
  if (score > 0) score += titleBoost
  if (lower.includes(query.toLowerCase().trim())) score += 6
  return score
}

/** Rank & pack note chunks within token budget (RAG-style slicing). */
export function selectContextChunks(
  notes: NoteItem[],
  query: string,
  maxContextTokens: number
): { chunks: NoteChunk[]; noteIds: string[] } {
  if (notes.length === 0) return { chunks: [], noteIds: [] }

  const systemReserve = 700
  const queryReserve = estimateTokens(query) + 150
  const configuredBudget = Number.isFinite(maxContextTokens) ? maxContextTokens : 0
  const budget = Math.max(DEFAULT_MIN_CONTEXT_TOKENS, configuredBudget - systemReserve - queryReserve)

  const allChunks: NoteChunk[] = []
  for (const note of notes) {
    const pieces = chunkNoteContent(note)
    const titleScore = scoreText(note.title, query, 8)
    if (pieces.length === 0) {
      allChunks.push({
        noteId: note.id,
        title: note.title || '无标题',
        index: 0,
        text: '(空)',
        score: titleScore * 0.5,
      })
      continue
    }
    pieces.forEach((text, index) => {
      allChunks.push({
        noteId: note.id,
        title: note.title || '无标题',
        index,
        text,
        score: scoreText(text, query) + titleScore,
      })
    })
  }

  allChunks.sort((a, b) => b.score - a.score || b.text.length - a.text.length || a.noteId.localeCompare(b.noteId))

  const selected: NoteChunk[] = []
  let used = 0
  const seenNotes = new Set<string>()

  for (const chunk of allChunks) {
    const block = formatChunkBlock(chunk)
    const cost = estimateTokens(block)
    if (used + cost > budget && selected.length > 0) continue

    selected.push(chunk)
    used += cost
    seenNotes.add(chunk.noteId)
  }

  if (selected.length === 0) {
    const fallback = allChunks.slice(0, Math.min(3, allChunks.length))
    for (const c of fallback) seenNotes.add(c.noteId)
    return { chunks: fallback, noteIds: [...seenNotes] }
  }

  return { chunks: selected, noteIds: [...seenNotes] }
}

function formatChunkBlock(chunk: NoteChunk): string {
  return `--- [${chunk.noteId}] 《${chunk.title}》#${chunk.index + 1} ---\n${chunk.text}`
}

export function buildChunkContext(chunks: NoteChunk[]): string {
  return chunks.map(formatChunkBlock).join('\n\n')
}

/** @deprecated use selectContextChunks — kept for token estimate in UI */
export function selectNotesForContext(
  notes: NoteItem[],
  query: string,
  maxContextTokens: number
): { notes: NoteItem[]; charLimitPerNote: number | undefined } {
  const { noteIds } = selectContextChunks(notes, query, maxContextTokens)
  return {
    notes: noteIds.map(id => notes.find(n => n.id === id)).filter(Boolean) as NoteItem[],
    charLimitPerNote: undefined,
  }
}

export function buildNoteContext(
  notes: NoteItem[],
  charLimitPerNote?: number
): { context: string } {
  const blocks = notes.map(n => {
    const text = htmlToPlainText(n.content, charLimitPerNote)
    return `--- 笔记 [${n.id}] 《${n.title || '无标题'}》 ---\n${text || '(空)'}`
  })
  return { context: blocks.join('\n\n') }
}

function buildAuthHeaders(config: AiConfig): Record<string, string> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (config.authMode === 'api-key') {
    headers['api-key'] = config.apiKey.trim()
  } else {
    headers['Authorization'] = `Bearer ${config.apiKey.trim()}`
  }
  return headers
}

function buildRequestBody(config: AiConfig, messages: AiChatMessage[]): Record<string, unknown> {
  const body: Record<string, unknown> = {
    model: config.model.trim(),
    messages,
  }

  switch (config.provider) {
    case 'azure':
      body.temperature = 1
      break
    case 'mimo':
      body.temperature = 0.3
      body.max_completion_tokens = 1024
      body.stream = false
      break
    default:
      body.temperature = 0.3
      body.max_tokens = 1024
      break
  }

  return body
}

async function callChatApi(config: AiConfig, messages: AiChatMessage[]): Promise<any> {
  const body = buildRequestBody(config, messages)
  const f = await getFetch()
  const res = await f(config.endpoint.trim(), {
    method: 'POST',
    headers: buildAuthHeaders(config),
    body: JSON.stringify(body),
  })

  const text = await res.text()
  let json: any
  try {
    json = JSON.parse(text)
  } catch {
    throw new Error(`API 返回非 JSON (HTTP ${res.status}): ${text.slice(0, 300)}`)
  }

  if (!res.ok) {
    const errMsg = json.error?.message || json.error?.code || json.error || json.message || `HTTP ${res.status}`
    throw new Error(typeof errMsg === 'string' ? errMsg : JSON.stringify(errMsg))
  }

  return json
}

export async function chatWithNotes(
  config: AiConfig,
  question: string,
  allNotes: NoteItem[],
  history: AiChatMessage[] = []
): Promise<AiChatResult> {
  const { chunks, noteIds } = selectContextChunks(allNotes, question, config.maxContextTokens)
  const context = buildChunkContext(chunks)

  const systemPrompt = `你是 Test Space 笔记助手。根据下方「参考笔记片段」回答用户问题。
规则：
1. 仅基于参考片段作答；若无相关信息，明确说明。
2. 引用笔记时在正文中使用格式：[笔记标题](note:笔记ID)，可多处引用。
3. 不要在回答末尾单独列出「参考笔记」清单。
4. 回答简洁准确，使用与用户相同的语言。`

  const userContent = `参考笔记（共 ${allNotes.length} 篇，检索 ${noteIds.length} 篇 / ${chunks.length} 个片段）：\n${context || '(无参考内容)'}\n\n用户问题：${question}`

  const messages: AiChatMessage[] = [
    { role: 'system', content: systemPrompt },
    ...history.slice(-4),
    { role: 'user', content: userContent },
  ]

  const json = await callChatApi(config, messages)

  const answer = json.choices?.[0]?.message?.content || json.choices?.[0]?.text || ''
  const usage = json.usage
    ? {
        promptTokens: json.usage.prompt_tokens ?? 0,
        completionTokens: json.usage.completion_tokens ?? 0,
        totalTokens: json.usage.total_tokens ?? 0,
      }
    : undefined

  return {
    answer: answer.trim(),
    contextNoteCount: noteIds.length,
    contextChunkCount: chunks.length,
    usage,
  }
}

export async function testAiConnection(config: AiConfig): Promise<string> {
  const messages: AiChatMessage[] = [
    { role: 'system', content: '你是一个助手' },
    { role: 'user', content: '你好，请回复 OK' },
  ]
  const json = await callChatApi(config, messages)
  const answer = json.choices?.[0]?.message?.content || json.choices?.[0]?.text || ''
  return answer.trim().slice(0, 100) || 'OK'
}
