function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function escapeHtmlAttr(text: string): string {
  return text.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

/** Convert basic Markdown text to HTML suitable for TipTap storage. */
export function mdToHtml(md: string): string {
  let html = md
    .replace(/\r\n/g, '\n')
    .replace(/\r/g, '\n')

  // Extract code blocks first (```...```) to protect them from inline processing
  const codeBlocks: string[] = []
  html = html.replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, code) => {
    const idx = codeBlocks.length
    codeBlocks.push(`<pre><code${lang ? ` class="language-${escapeHtmlAttr(lang)}"` : ''}>${escapeHtml(code.trim())}</code></pre>`)
    return `\x00CODEBLOCK${idx}\x00`
  })

  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>')

  // Headings
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>')
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>')
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>')

  // Blockquotes
  html = html.replace(/^> (.+)$/gm, '<blockquote><p>$1</p></blockquote>')

  // Horizontal rules
  html = html.replace(/^(?:---|\*\*\*|___)\s*$/gm, '<hr>')

  // Unordered lists
  html = html.replace(/^- (.+)$/gm, '<li>$1</li>')
  html = html.replace(/(<li>.*<\/li>\n?)+/g, match => `<ul>${match}</ul>`)

  // Ordered lists
  html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
  html = html.replace(/(<li>.*<\/li>\n?)+/g, (match, _, offset, str) => {
    const before = str[offset - 1]
    if (before === undefined || before === '\n' || before === '') {
      return `<ol>${match}</ol>`
    }
    return match
  })
  // Fix nested list detection — ordered list items wrapped in ol
  const olRegex = /(<li>.*?<\/li>\n?)+/g
  html = html.replace(olRegex, (match, _, offset, str) => {
    const context = str.slice(Math.max(0, offset - 20), offset)
    if (context.includes('<ol>') || context.includes('<ul>')) return match
    return `<ol>${match}</ol>`
  })

  // Bold, italic, strikethrough
  html = html.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>')
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>')
  html = html.replace(/~~(.+?)~~/g, '<s>$1</s>')

  // Images
  html = html.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1">')

  // Links
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>')

  // Restore code blocks
  html = html.replace(/\x00CODEBLOCK(\d+)\x00/g, (_, idx) => codeBlocks[parseInt(idx)] || '')

  // Wrap remaining text in paragraphs (double newlines separate paragraphs)
  const blocks = html.split(/\n\n+/).map(b => b.trim()).filter(Boolean)
  const wrapped = blocks.map(block => {
    if (block.startsWith('<h') || block.startsWith('<ul') || block.startsWith('<ol') ||
        block.startsWith('<pre') || block.startsWith('<blockquote') || block.startsWith('<hr') ||
        block.startsWith('<p')) {
      return block
    }
    return `<p>${block}</p>`
  }).join('\n')

  // Normalize line breaks within blocks
  return wrapped.replace(/\n(?!<)/g, '<br>')
}

/** Convert DOCX ArrayBuffer to HTML using mammoth. */
export async function docxToHtml(buffer: ArrayBuffer): Promise<string> {
  const mammoth = await import('mammoth')
  const result = await mammoth.convertToHtml({ arrayBuffer: buffer })
  return result.value
}
