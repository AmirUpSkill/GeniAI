import { BookOpen, FileText, X } from 'lucide-react'
import { useEffect } from 'react'

import type { FileSearchCitation } from '../schemas'

type CitationDialogProps = {
  citation: FileSearchCitation | null
  onClose: () => void
}

export function CitationDialog({ citation, onClose }: CitationDialogProps) {
  useEffect(() => {
    if (citation === null) {
      return
    }
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        onClose()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [citation, onClose])

  if (citation === null) {
    return null
  }

  return (
    <div
      aria-labelledby="citation-dialog-title"
      aria-modal="true"
      className="citation-dialog-backdrop"
      onMouseDown={(event) => {
        if (event.currentTarget === event.target) {
          onClose()
        }
      }}
      role="dialog"
    >
      <section className="citation-dialog">
        <header>
          <span className="citation-dialog-icon">
            <BookOpen aria-hidden="true" size={20} />
          </span>
          <div>
            <p>Retrieved source</p>
            <h2 id="citation-dialog-title">{citation.fileName}</h2>
          </div>
          <button aria-label="Close citation" onClick={onClose} type="button">
            <X aria-hidden="true" size={20} />
          </button>
        </header>

        <div className="citation-dialog-meta">
          <FileText aria-hidden="true" size={16} />
          <span>
            {citation.pageNumber === null
              ? 'Page number unavailable'
              : `Page ${citation.pageNumber}`}
          </span>
        </div>

        <blockquote>{citation.sourceExcerpt}</blockquote>

        <aside>
          Geni does not retain the original uploaded PDF in this version. This dialog
          shows the exact passage and page reference returned by Gemini File Search.
        </aside>
      </section>
    </div>
  )
}
