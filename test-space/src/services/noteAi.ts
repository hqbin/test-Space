import type { NoteItem } from '@/types'
import type { AiConfig } from '@/services/aiSettings'
import type { AiMemory } from '@/services/database'

export interface AiChatMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
}

export interface AiChatResult {
  answer: string
  contextNoteCount: number
  contextChunkCount: number
  memoryCount: number
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

/** Get plain text from a note, preferring cached plainText field. */
export function getNotePlainText(note: NoteItem): string {
  return note.plainText || htmlToPlainText(note.content || '')
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
  if (!html.trim()) {
    if (note.plainText) return splitLongText(note.plainText)
    return []
  }

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
  // Split CJK-Latin boundaries so "设备MAC地址烧写" → "设备 MAC 地址烧写"
  const spaced = q.replace(/([\u4e00-\u9fff])([a-z\d]+)/g, '$1 $2')
                  .replace(/([a-z\d]+)([\u4e00-\u9fff])/g, '$1 $2')
  const cjk = spaced.match(/[\u4e00-\u9fff]{2,}/g) || []
  const words = spaced
    .split(/[^\p{L}\p{N}\u4e00-\u9fff]+/u)
    .filter(w => w.length >= 2)
  return [...new Set([...cjk, ...words, q])]
}

/** Tokenize document text (with duplicates, for BM25 term frequency). */
function tokenizeDoc(text: string): string[] {
  const lower = text.toLowerCase().trim()
  if (!lower) return []
  const spaced = lower.replace(/([\u4e00-\u9fff])([a-z\d]+)/g, '$1 $2')
                      .replace(/([a-z\d]+)([\u4e00-\u9fff])/g, '$1 $2')
  const cjk = spaced.match(/[\u4e00-\u9fff]{2,}/g) || []
  const words = spaced
    .split(/[^\p{L}\p{N}\u4e00-\u9fff]+/u)
    .filter(w => w.length >= 2)
  return [...cjk, ...words]
}

/** Compute BM25 corpus statistics (IDF + avg doc length). */
function computeBm25Stats(texts: string[]): { idf: Map<string, number>; avgdl: number } {
  const docLengths: number[] = []
  const df = new Map<string, number>()

  for (const text of texts) {
    const tokens = tokenizeDoc(text)
    if (tokens.length === 0) continue
    docLengths.push(tokens.length)
    const unique = new Set(tokens)
    for (const t of unique) {
      df.set(t, (df.get(t) || 0) + 1)
    }
  }

  const N = docLengths.length
  const avgdl = N > 0 ? docLengths.reduce((a, b) => a + b, 0) / N : 1

  const idf = new Map<string, number>()
  for (const [term, docFreq] of df) {
    idf.set(term, Math.log(1 + (N - docFreq + 0.5) / (docFreq + 0.5)))
  }

  return { idf, avgdl }
}

/** BM25 score for a document against a query. */
function bm25Score(text: string, query: string, stats: { idf: Map<string, number>; avgdl: number }): number {
  const queryTokens = tokenizeFinalQuery(query)
  if (queryTokens.length === 0 || !stats.avgdl) return 0

  const docTokens = tokenizeDoc(text)
  if (docTokens.length === 0) return 0

  const docLen = docTokens.length
  const tfMap = new Map<string, number>()
  for (const t of docTokens) {
    tfMap.set(t, (tfMap.get(t) || 0) + 1)
  }

  const k1 = 1.5; const b = 0.75
  let score = 0

  for (const qToken of queryTokens) {
    if (qToken.length < 2) continue
    const tf = tfMap.get(qToken) || 0
    if (tf === 0) continue
    const idf = stats.idf.get(qToken)
    if (!idf || idf <= 0) continue
    score += idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * docLen / stats.avgdl))
  }

  return score
}

/** Score memories by query term overlap — simple lightweight ranking. */
export function scoreMemories(query: string, memories: AiMemory[]): AiMemory[] {
  if (!query.trim() || memories.length === 0) return []
  const queryTokens = new Set(tokenizeFinalQuery(query))
  if (queryTokens.size === 0) return memories.slice(0, 10)

  const scored = memories.map(m => {
    const docTokens = tokenizeDoc(m.content)
    let score = 0
    for (const t of docTokens) {
      if (queryTokens.has(t)) score++
    }
    if (m.content.toLowerCase().includes(query.toLowerCase())) score += 3
    return { memory: m, score }
  })

  scored.sort((a, b) => b.score - a.score)
  return scored.filter(s => s.score > 0).slice(0, 10).map(s => s.memory)
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

  // Step 1: chunk all notes
  const allChunks: NoteChunk[] = []
  for (const note of notes) {
    const pieces = chunkNoteContent(note)
    if (pieces.length === 0) {
      allChunks.push({
        noteId: note.id,
        title: note.title || '无标题',
        index: 0,
        text: '(空)',
        score: 0,
      })
      continue
    }
    pieces.forEach((text, index) => {
      allChunks.push({
        noteId: note.id,
        title: note.title || '无标题',
        index,
        text,
        score: 0,
      })
    })
  }

  // Step 2: BM25 scoring (corpus-aware)
  if (query.trim()) {
    const contentChunks = allChunks.filter(c => c.text !== '(空)')
    const stats = contentChunks.length > 0
      ? computeBm25Stats(contentChunks.map(c => c.text))
      : { idf: new Map(), avgdl: 1 }

    // Precompute title BM25 per note
    const titleScores = new Map<string, number>()
    for (const note of notes) {
      titleScores.set(note.id, bm25Score(note.title || '', query, stats))
    }

    for (const chunk of allChunks) {
      if (chunk.text === '(空)') continue
      const ts = bm25Score(chunk.text, query, stats)
      const titleBm25 = titleScores.get(chunk.noteId) || 0
      chunk.score = ts + titleBm25 * 3 + (titleBm25 > 0 ? 2 : 0)
    }
  } else {
    for (const chunk of allChunks) {
      chunk.score = chunk.text === '(空)' ? 0.5 : 1
    }
  }

  // Group by note for diverse packing: every note gets at least one chunk
  const byNote = new Map<string, NoteChunk[]>()
  for (const chunk of allChunks) {
    const list = byNote.get(chunk.noteId) || []
    list.push(chunk)
    byNote.set(chunk.noteId, list)
  }
  for (const list of byNote.values()) {
    list.sort((a, b) => b.score - a.score || a.text.length - b.text.length)
  }

  const selected: NoteChunk[] = []
  let used = 0

  // Round 1: pick the best chunk from each note (budget permitting)
  for (const note of notes) {
    const chunks = byNote.get(note.id)
    if (!chunks || chunks.length === 0) continue
    const cost = estimateTokens(formatChunkBlock(chunks[0]))
    if (used + cost <= budget) {
      selected.push(chunks[0])
      used += cost
    }
  }

  // Round 2: fill remaining budget with next-best chunks in score order
  const selectedIds = new Set(selected.map(c => `${c.noteId}-${c.index}`))
  const remaining = allChunks.filter(c => !selectedIds.has(`${c.noteId}-${c.index}`))
  remaining.sort((a, b) => b.score - a.score || a.text.length - b.text.length || a.noteId.localeCompare(b.noteId))
  for (const chunk of remaining) {
    const cost = estimateTokens(formatChunkBlock(chunk))
    if (used + cost <= budget) {
      selected.push(chunk)
      used += cost
    }
  }

  if (selected.length === 0) {
    const fallback = allChunks.slice(0, Math.min(3, allChunks.length))
    const fbNoteIds = [...new Set(fallback.map(c => c.noteId))]
    return { chunks: fallback, noteIds: fbNoteIds }
  }

  return {
    chunks: selected,
    noteIds: [...new Set(selected.map(c => c.noteId))],
  }
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
  history: AiChatMessage[] = [],
  memories: AiMemory[] = []
): Promise<AiChatResult> {
  const { chunks, noteIds } = selectContextChunks(allNotes, question, config.maxContextTokens)
  const context = buildChunkContext(chunks)

  const relevantMemories = scoreMemories(question, memories)
  const memoriesBlock = relevantMemories.length > 0
    ? `\n\n已知长期记忆：\n${relevantMemories.map(m => `- ${m.content}`).join('\n')}`
    : ''

  const systemPrompt = `你是 Test Space 笔记助手。根据下方「参考笔记片段」和已知长期记忆回答用户问题。
规则：
1. 仅基于参考片段和长期记忆作答；若无相关信息，明确说明。
2. 引用笔记时在正文中使用格式：[笔记标题](note:笔记ID)，可多处引用。
3. 不要在回答末尾单独列出「参考笔记」清单。
4. 回答简洁准确，使用与用户相同的语言。${memoriesBlock}`

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
    memoryCount: relevantMemories.length,
    usage,
  }
}

/**
 * Lightweight AI call to extract consolidated, meaningful facts from a Q&A pair.
 * Returns extracted fact strings (empty array if nothing to remember).
 */
export async function extractMemories(
  config: AiConfig,
  question: string,
  answer: string,
  existingMemories: string[] = []
): Promise<string[]> {
  const existingBlock = existingMemories.length > 0
    ? `\n已有记忆：\n${existingMemories.map(m => `- ${m}`).join('\n')}\n注意：不要重复提取与已有记忆表达相同或高度相似的内容。`
    : ''
  const systemPrompt =
    '你是一个记忆提取助手。从以下问答中提取值得长期记住的关键知识点，要求：\n' +
    '1. 只提取有长期价值的事实性知识（如用户偏好、项目信息、技术决策、约定等）\n' +
    '2. 忽略一次性的、临时的、无长期价值的对话内容\n' +
    '3. 将密切相关的多条信息合并为一条综合记忆，避免碎片化\n' +
    '4. 每条记忆应简洁准确，用一句话概括\n' +
    '5. 如果没有值得长期记忆的内容，直接返回空\n' +
    '6. 严禁提取与已有记忆内容相同或高度相似的记忆' +
    existingBlock +
    '\n格式：每行一条，不要加序号。'
  const userContent = `问：${question}\n答：${answer}`

  const messages: AiChatMessage[] = [
    { role: 'system', content: systemPrompt },
    { role: 'user', content: userContent },
  ]

  const json = await callChatApi(config, messages)
  const content: string = json.choices?.[0]?.message?.content || json.choices?.[0]?.text || ''
  const lines: string[] = content.split('\n')
    .map(l => l.trim().replace(/^[-*\d.、\s]+/, ''))
    .filter(l => l.length >= 4)
  return [...new Set(lines)]
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
