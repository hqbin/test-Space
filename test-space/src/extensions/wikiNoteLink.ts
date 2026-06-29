import { Extension, markInputRule } from '@tiptap/core'
import Link from '@tiptap/extension-link'

export const NOTE_LINK_PREFIX = 'note:'

export interface WikiNoteLinkOptions {
  resolveNoteId: (title: string) => string | null
}

export const WikiNoteLink = Extension.create<WikiNoteLinkOptions>({
  name: 'wikiNoteLink',

  addOptions() {
    return {
      resolveNoteId: () => null,
    }
  },

  addInputRules() {
    return [
      markInputRule({
        find: /\[\[([^\]]+)\]\]$/,
        type: this.editor.schema.marks.link,
        getAttributes: (match) => {
          const title = match[1]?.trim() || ''
          const noteId = this.options.resolveNoteId(title)
          if (!noteId) {
            return { href: `#unresolved:${encodeURIComponent(title)}`, target: null, rel: null, class: 'note-link note-link-unresolved' }
          }
          return { href: `${NOTE_LINK_PREFIX}${noteId}`, target: null, rel: null, class: 'note-link' }
        },
      }),
    ]
  },
})

export const NoteLinkExtension = Link.configure({
  openOnClick: false,
  autolink: true,
  linkOnPaste: true,
  protocols: ['note'],
  isAllowedUri: (href: string | undefined, ctx) =>
    !!href && (
      href.startsWith(NOTE_LINK_PREFIX) ||
      href.startsWith('#unresolved:') ||
      ctx.defaultValidate(href)
    ),
  validate: (href: string) =>
    href.startsWith(NOTE_LINK_PREFIX) ||
    href.startsWith('#unresolved:') ||
    /^https?:\/\//i.test(href),
  HTMLAttributes: {
    target: null,
    rel: null,
    class: 'note-link',
  },
})
