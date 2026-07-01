export interface AnswerSegment {
  type: 'text' | 'link'
  content: string
  noteId?: string
  /** Optional heading anchor to scroll to within the note (decoded text of the heading) */
  headingAnchor?: string
}

/**
 * Parse inline note references.
 * Supports both:
 *   [title](note:uuid)
 *   [title](note:uuid#heading text)
 */
export function parseAnswerNoteLinks(text: string): AnswerSegment[] {
  // Capture optional #anchor after the uuid
  const regex = /\[([^\]]+)\]\(note:([a-f0-9-]{36})(?:#([^)]*))?\)/gi
  const segments: AnswerSegment[] = []
  let lastIndex = 0
  let match: RegExpExecArray | null

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      segments.push({ type: 'text', content: text.slice(lastIndex, match.index) })
    }
    const anchor = match[3] ? match[3].trim() : undefined
    segments.push({ type: 'link', content: match[1], noteId: match[2], headingAnchor: anchor })
    lastIndex = regex.lastIndex
  }

  if (lastIndex < text.length) {
    segments.push({ type: 'text', content: text.slice(lastIndex) })
  }

  return segments.length > 0 ? segments : [{ type: 'text', content: text }]
}
