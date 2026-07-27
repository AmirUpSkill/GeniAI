import { Check, Copy } from 'lucide-react'
import {
  isValidElement,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import ReactMarkdown, { type Components } from 'react-markdown'
import rehypeSanitize from 'rehype-sanitize'
import remarkGfm from 'remark-gfm'

type AssistantMarkdownProps = {
  content: string
  isStreaming?: boolean
}

const markdownComponents: Components = {
  a({ children, node: _node, ...props }) {
    return (
      <a {...props} rel="noopener noreferrer nofollow" target="_blank">
        {children}
      </a>
    )
  },
  code({ children, node: _node, ...props }) {
    return <code {...props}>{children}</code>
  },
  img({ alt }) {
    return <span className="markdown-image-omitted">Image omitted: {alt || 'untitled'}</span>
  },
  pre({ children }) {
    const codeElement = isValidElement<{
      children?: ReactNode
      className?: string
    }>(children)
      ? children
      : null
    const code = getNodeText(codeElement?.props.children).replace(/\n$/, '')
    const language =
      codeElement?.props.className?.match(/(?:^|\s)language-([^\s]+)/)?.[1] ?? null

    return <CodeBlock code={code} language={language} />
  },
  table({ children, node: _node, ...props }) {
    return (
      <div className="markdown-table-scroll">
        <table {...props}>{children}</table>
      </div>
    )
  },
}

export function AssistantMarkdown({
  content,
  isStreaming = false,
}: AssistantMarkdownProps) {
  return (
    <div className="assistant-markdown">
      <ReactMarkdown
        components={markdownComponents}
        rehypePlugins={[rehypeSanitize]}
        remarkPlugins={[remarkGfm]}
        skipHtml
      >
        {content}
      </ReactMarkdown>
      {isStreaming ? <span aria-label="Generating" className="streaming-cursor" /> : null}
    </div>
  )
}

function CodeBlock({
  code,
  language,
}: {
  code: string
  language: string | null
}) {
  const [copied, setCopied] = useState(false)
  const resetTimerRef = useRef<number | null>(null)

  useEffect(() => {
    return () => {
      if (resetTimerRef.current !== null) {
        window.clearTimeout(resetTimerRef.current)
      }
    }
  }, [])

  async function copyCode() {
    try {
      await navigator.clipboard.writeText(code)
      setCopied(true)
      if (resetTimerRef.current !== null) {
        window.clearTimeout(resetTimerRef.current)
      }
      resetTimerRef.current = window.setTimeout(() => setCopied(false), 1600)
    } catch {
      setCopied(false)
    }
  }

  return (
    <div className="markdown-code-block">
      <div className="markdown-code-header">
        <span>{language ?? 'code'}</span>
        <button
          aria-label={copied ? 'Code copied' : 'Copy code'}
          onClick={() => void copyCode()}
          type="button"
        >
          {copied ? <Check aria-hidden="true" size={14} /> : <Copy aria-hidden="true" size={14} />}
          <span>{copied ? 'Copied' : 'Copy'}</span>
        </button>
      </div>
      <pre>
        <code className={language === null ? undefined : `language-${language}`}>
          {code}
        </code>
      </pre>
    </div>
  )
}

function getNodeText(node: ReactNode): string {
  if (
    typeof node === 'string' ||
    typeof node === 'number' ||
    typeof node === 'bigint'
  ) {
    return String(node)
  }
  if (Array.isArray(node)) {
    return node.map(getNodeText).join('')
  }
  if (isValidElement<{ children?: ReactNode }>(node)) {
    return getNodeText(node.props.children)
  }
  return ''
}
