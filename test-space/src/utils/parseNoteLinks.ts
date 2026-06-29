export interface AnswerSegment {
  type: 'text' | 'link'
  content: string
  noteId?: string
}

/** Parse inline note references: [title](note:uuid) */
export function parseAnswerNoteLinks(text: string): AnswerSegment[] {
  const regex = /\[([^\]]+)\]\(note:([a-f0-9-]{36})\)/gi
  const segments: AnswerSegment[] = []
  let lastIndex = 0
  let match: RegExpExecArray | null

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      segments.push({ type: 'text', content: text.slice(lastIndex, match.index) })
    }
    segments.push({ type: 'link', content: match[1], noteId: match[2] })
    lastIndex = regex.lastIndex
  }

  if (lastIndex < text.length) {
    segments.push({ type: 'text', content: text.slice(lastIndex) })
  }

  return segments.length > 0 ? segments : [{ type: 'text', content: text }]
}
