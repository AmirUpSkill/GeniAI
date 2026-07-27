import { AlertCircle, Check, FileText, Loader2, Paperclip, Trash2 } from 'lucide-react'
import { useRef } from 'react'

import type { FileSearchDocument } from '../schemas'

type DocumentAttachmentButtonProps = {
  document: FileSearchDocument | null
  disabled?: boolean
  onSelect: (file: File) => void
}

export function DocumentAttachmentButton({
  document,
  disabled = false,
  onSelect,
}: DocumentAttachmentButtonProps) {
  const inputRef = useRef<HTMLInputElement>(null)

  return (
    <>
      <input
        ref={inputRef}
        accept="application/pdf,.pdf"
        className="file-search-input"
        disabled={disabled || document !== null}
        onChange={(event) => {
          const file = event.target.files?.[0]
          if (file !== undefined) {
            onSelect(file)
          }
          event.currentTarget.value = ''
        }}
        type="file"
      />

      <button
        aria-label={document === null ? 'Attach a PDF' : 'This chat already has a PDF'}
        className="composer-tool"
        disabled={disabled || document !== null}
        onClick={() => inputRef.current?.click()}
        title={document === null ? 'Attach one PDF' : 'One document is already attached'}
        type="button"
      >
        <Paperclip aria-hidden="true" size={22} />
      </button>
    </>
  )
}

type DocumentStatusCardProps = {
  document: FileSearchDocument | null
  error?: string | null
  isLoading?: boolean
  onRemove: () => void
}

export function DocumentStatusCard({
  document,
  error,
  isLoading = false,
  onRemove,
}: DocumentStatusCardProps) {
  const isProcessing =
    document?.status === 'pending' || document?.status === 'indexing' || isLoading

  return (
    <>
      {document !== null ? (
        <div className={`file-search-card is-${document.status}`}>
          <span className="file-search-icon">
            {document.status === 'failed' ? (
              <AlertCircle aria-hidden="true" size={18} />
            ) : document.status === 'ready' ? (
              <Check aria-hidden="true" size={18} />
            ) : (
              <Loader2 aria-hidden="true" className="button-spinner" size={18} />
            )}
          </span>
          <span className="file-search-card-copy">
            <strong>{document.originalName}</strong>
            <small>{getStatusLabel(document)}</small>
          </span>
          <span className="file-search-size">{formatFileSize(document.sizeBytes)}</span>
          <button
            aria-label={`Remove ${document.originalName}`}
            disabled={isProcessing}
            onClick={onRemove}
            title={isProcessing ? 'Wait for indexing to finish' : 'Remove document'}
            type="button"
          >
            <Trash2 aria-hidden="true" size={16} />
          </button>
        </div>
      ) : null}

      {document === null && error ? (
        <div className="file-search-inline-error" role="alert">
          <AlertCircle aria-hidden="true" size={15} />
          <span>{error}</span>
        </div>
      ) : null}
    </>
  )
}

function getStatusLabel(document: FileSearchDocument) {
  if (document.status === 'ready') {
    return 'Ready · answers will use this document'
  }
  if (document.status === 'failed') {
    return document.failureMessage ?? 'Indexing failed · remove and try again'
  }
  if (document.status === 'indexing') {
    return 'Gemini is indexing this document…'
  }
  return 'Upload received · preparing document…'
}

function formatFileSize(bytes: number) {
  if (bytes < 1024 * 1024) {
    return `${Math.max(1, Math.round(bytes / 1024))} KB`
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function FileSearchDropOverlay() {
  return (
    <div className="file-search-drop-overlay">
      <div>
        <FileText aria-hidden="true" size={28} />
        <strong>Drop one PDF here</strong>
        <span>Geni will index it for this chat</span>
      </div>
    </div>
  )
}
