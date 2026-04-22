import { useEditor, EditorContent } from '@tiptap/react'
import { StarterKit } from '@tiptap/starter-kit'
import { Underline } from '@tiptap/extension-underline'
import { TextStyle } from '@tiptap/extension-text-style'
import { Color } from '@tiptap/extension-color'
import { Link } from '@tiptap/extension-link'
import { useState, useCallback, useEffect } from 'react'
import './DescriptionEditor.css'

// Бренд-цвета
const BRAND_COLORS = {
  accent: 'var(--accent)',       // #13c8b0
  accentLight: 'var(--accent-light)', // #b7ffb2
}

const BRAND_COLOR_MAP = {
  'var(--accent)': '#13c8b0',
  'var(--accent-light)': '#b7ffb2',
}

function DescriptionEditor({ value, onChange }) {
  const [linkUrl, setLinkUrl] = useState('')
  const [showLinkInput, setShowLinkInput] = useState(false)

  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        heading: {
          levels: [2, 3],
        },
      }),
      Underline,
      TextStyle,
      Color,
      Link.configure({
        openOnClick: false,
      }),
    ],
    content: value || '',
    onUpdate: ({ editor }) => {
      const html = editor.getHTML()
      // Заменяем hex-цвета обратно на CSS-переменные
      let cleaned = html
      Object.entries(BRAND_COLOR_MAP).forEach(([cssVar, hex]) => {
        cleaned = cleaned.replaceAll(`color: ${hex}`, `color: ${cssVar}`)
      })
      onChange(cleaned)
    },
  })

  // Синхронизация внешнего значения (при загрузке турнира для редактирования)
  useEffect(() => {
    if (editor && value !== editor.getHTML() && value !== undefined) {
      let processedValue = value || ''
      // При загрузке из БД CSS-переменные могли быть сохранены как есть — оставляем
      editor.commands.setContent(processedValue, false)
    }
  }, [value, editor])

  if (!editor) return null

  const setLink = useCallback(() => {
    if (showLinkInput) {
      if (linkUrl) {
        editor.chain().focus().extendMarkRange('link').setLink({ href: linkUrl }).run()
      }
      setLinkUrl('')
      setShowLinkInput(false)
    } else {
      setShowLinkInput(true)
    }
  }, [editor, linkUrl, showLinkInput])

  return (
    <div className="description-editor">
      {/* Панель инструментов */}
      <div className="description-editor-toolbar">
        <button
          type="button"
          onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
          className={`description-editor-btn ${editor.isActive('heading', { level: 2 }) ? 'active' : ''}`}
        >
          H2
        </button>
        <button
          type="button"
          onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
          className={`description-editor-btn ${editor.isActive('heading', { level: 3 }) ? 'active' : ''}`}
        >
          H3
        </button>
        <div className="description-editor-divider" />
        <button
          type="button"
          onClick={() => editor.chain().focus().toggleBold().run()}
          className={`description-editor-btn ${editor.isActive('bold') ? 'active' : ''}`}
        >
          <strong>B</strong>
        </button>
        <button
          type="button"
          onClick={() => editor.chain().focus().toggleItalic().run()}
          className={`description-editor-btn ${editor.isActive('italic') ? 'active' : ''}`}
        >
          <em>I</em>
        </button>
        <button
          type="button"
          onClick={() => editor.chain().focus().toggleUnderline().run()}
          className={`description-editor-btn ${editor.isActive('underline') ? 'active' : ''}`}
        >
          <u>U</u>
        </button>
        <div className="description-editor-divider" />
        <button
          type="button"
          onClick={() => editor.chain().focus().toggleBulletList().run()}
          className={`description-editor-btn ${editor.isActive('bulletList') ? 'active' : ''}`}
        >
          • —
        </button>
        <button
          type="button"
          onClick={() => editor.chain().focus().toggleOrderedList().run()}
          className={`description-editor-btn ${editor.isActive('orderedList') ? 'active' : ''}`}
        >
          1. —
        </button>
        <div className="description-editor-divider" />
        <button
          type="button"
          onClick={setLink}
          className={`description-editor-btn ${editor.isActive('link') ? 'active' : ''}`}
          title="Вставить ссылку"
        >
          🔗
        </button>
        <div className="description-editor-divider" />
        {/* Бренд-цвета */}
        <button
          type="button"
          onClick={() => editor.chain().focus().setColor(BRAND_COLORS.accent).run()}
          className="description-editor-btn description-editor-btn-color-accent"
          title="Цвет: Accent (#13c8b0)"
        >
          A
        </button>
        <button
          type="button"
          onClick={() => editor.chain().focus().setColor(BRAND_COLORS.accentLight).run()}
          className="description-editor-btn description-editor-btn-color-accent-light"
          title="Цвет: Accent Light (#b7ffb2)"
        >
          A
        </button>
        <button
          type="button"
          onClick={() => editor.chain().focus().unsetColor().run()}
          className="description-editor-btn"
          title="Сбросить цвет"
        >
          ✕
        </button>
      </div>

      {/* Инпут для ссылки */}
      {showLinkInput && (
        <div className="description-editor-link-input">
          <input
            type="url"
            placeholder="https://example.com"
            value={linkUrl}
            onChange={(e) => setLinkUrl(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && setLink()}
            autoFocus
          />
        </div>
      )}

      {/* Область редактирования */}
      <EditorContent editor={editor} className="description-editor-content" />
    </div>
  )
}

export default DescriptionEditor
