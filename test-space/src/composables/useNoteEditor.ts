// 笔记富文本编辑器统一配置
// 主窗口（NotesSpacePage）与桌面便签（StickyNote）共用同一份 TipTap 配置，
// 保证两个窗口的编辑体验与链接行为完全一致。
import { useEditor, type Extension } from "@tiptap/vue-3";
import StarterKit from "@tiptap/starter-kit";
import Underline from "@tiptap/extension-underline";
import Image from "@tiptap/extension-image";
import Placeholder from "@tiptap/extension-placeholder";
import Typography from "@tiptap/extension-typography";
import Color from "@tiptap/extension-color";
import TextStyle from "@tiptap/extension-text-style";
import { WikiNoteLink, NoteLinkExtension, NOTE_LINK_PREFIX } from "@/extensions/wikiNoteLink";

export interface UseNoteEditorOptions {
  /** 按标题解析笔记 ID（[[]] 双向链接输入规则用）；缺省则不解析链接 */
  resolveNoteId?: (title: string) => string | null
  /** 点击内部笔记链接（note:xxx）时回调，缺省则阻止默认行为但不跳转 */
  onOpenNoteLink?: (href: string) => void
  /** 编辑器内容变化（含格式化操作）时回调，收到最新 HTML */
  onUpdate?: (html: string) => void
  /** 页面级自定义扩展（如搜索高亮），追加到统一配置之后 */
  extraExtensions?: Extension[]
  /** 编辑器根元素 class，缺省为主窗口尺寸（min-h-300px） */
  editorClass?: string
}

export function useNoteEditor(opts: UseNoteEditorOptions = {}) {
  const editor = useEditor({
    content: "",
    extensions: [
      StarterKit.configure({
        heading: { levels: [1, 2, 3] },
      }),
      Underline,
      NoteLinkExtension,
      WikiNoteLink.configure({
        resolveNoteId: opts.resolveNoteId,
      }),
      Image.configure({ inline: true, allowBase64: true }),
      Placeholder.configure({ placeholder: "Start writing..." }),
      Typography,
      TextStyle,
      Color,
      ...(opts.extraExtensions ?? []),
    ],
    onUpdate: () => {
      const html = editor.value?.getHTML() ?? ""
      opts.onUpdate?.(html)
    },
    editorProps: {
      attributes: {
        class: opts.editorClass ?? "outline-none min-h-[300px]",
      },
      handleClick: (_view, _pos, event) => {
        const target = event.target as HTMLElement
        const anchor = target.closest('a')
        if (anchor) {
          const href = anchor.getAttribute('href') || ''
          if (href.startsWith(NOTE_LINK_PREFIX)) {
            event.preventDefault()
            opts.onOpenNoteLink?.(href)
            return true
          }
        }
        return false
      },
      clipboardTextSerializer: (slice) => {
        // Avoid extra blank lines when copying multi-line content out of the editor.
        let text = slice.content.textBetween(0, slice.content.size, "\n", "\n")
        // Normalize problematic invisible whitespace that breaks SQL/scripts when pasted elsewhere.
        text = text
          .replace(/\r\n/g, "\n")
          .replace(/[   ]/g, " ")
          .replace(/[​-‍﻿]/g, "")
        return text
      },
      handlePaste: (_view, event) => {
        const items = event.clipboardData?.items
        if (!items) return false
        for (const item of items) {
          if (item.type.startsWith('image/')) {
            const file = item.getAsFile()
            if (file) {
              const reader = new FileReader()
              reader.onload = () => {
                if (typeof reader.result === 'string') {
                  editor.value?.chain().focus().setImage({ src: reader.result }).run()
                }
              }
              reader.readAsDataURL(file)
              return true
            }
          }
        }
        return false
      },
    },
  })

  return { editor }
}
