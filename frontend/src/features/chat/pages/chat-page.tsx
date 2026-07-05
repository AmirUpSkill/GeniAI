import {
  Check,
  CircleDashed,
  Edit3,
  Loader2,
  MessageCircle,
  MessageSquareText,
  MoreVertical,
  Pencil,
  Plus,
  Send,
  Trash2,
  UserRound,
  X,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { getCurrentUser } from '../../auth/api'
import type { AuthenticatedUser } from '../../auth/schemas'
import {
  createChatSession,
  createChatTurn,
  deleteChatSession,
  listChatMessages,
  listChatSessions,
  updateChatSessionTitle,
} from '../api'
import type { ChatMessage, ChatSession } from '../schemas'
import { paths } from '../../../lib/paths'

type ChatPageProps = {
  onNavigate: (path: string) => void
}

type LoadingState = 'idle' | 'loading' | 'saving'

export function ChatPage({ onNavigate }: ChatPageProps) {
  const [user, setUser] = useState<AuthenticatedUser | null>(null)
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [composerValue, setComposerValue] = useState('')
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null)
  const [editingTitle, setEditingTitle] = useState('')
  const [openMenuSessionId, setOpenMenuSessionId] = useState<string | null>(null)
  const [isHistoryOpen, setIsHistoryOpen] = useState(false)
  const [sessionsState, setSessionsState] = useState<LoadingState>('loading')
  const [messagesState, setMessagesState] = useState<LoadingState>('idle')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let isMounted = true

    async function loadInitialState() {
      try {
        const [currentUser, chatSessions] = await Promise.all([
          getCurrentUser(),
          listChatSessions(),
        ])

        if (!isMounted) {
          return
        }

        setUser(currentUser)
        setSessions(chatSessions)
        setActiveSessionId(chatSessions[0]?.id ?? null)
        setSessionsState('idle')
      } catch {
        onNavigate(paths.auth)
      }
    }

    void loadInitialState()

    return () => {
      isMounted = false
    }
  }, [onNavigate])

  useEffect(() => {
    let isMounted = true

    async function loadMessages(chatSessionId: string) {
      setMessagesState('loading')
      setError(null)

      try {
        const chatMessages = await listChatMessages(chatSessionId)

        if (isMounted) {
          setMessages(chatMessages)
          setMessagesState('idle')
        }
      } catch {
        if (isMounted) {
          setError('Unable to load this chat history.')
          setMessages([])
          setMessagesState('idle')
        }
      }
    }

    if (activeSessionId === null) {
      setMessages([])
      setMessagesState('idle')
      return
    }

    void loadMessages(activeSessionId)

    return () => {
      isMounted = false
    }
  }, [activeSessionId])

  async function handleCreateSession() {
    setSessionsState('saving')
    setError(null)

    try {
      const chatSession = await createChatSession('New chat')
      setSessions((currentSessions) => [chatSession, ...currentSessions])
      setActiveSessionId(chatSession.id)
      setMessages([])
    } catch {
      setError('Unable to create a new chat.')
    } finally {
      setSessionsState('idle')
    }
  }

  async function handleSendMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    const content = composerValue.trim()
    if (content.length === 0) {
      return
    }

    let chatSessionId = activeSessionId
    setMessagesState('saving')
    setError(null)

    try {
      if (chatSessionId === null) {
        const chatSession = await createChatSession(createTitleFromMessage(content))
        chatSessionId = chatSession.id
        setSessions((currentSessions) => [chatSession, ...currentSessions])
        setActiveSessionId(chatSession.id)
      }

      const turn = await createChatTurn(chatSessionId, content)
      setMessages((currentMessages) => [
        ...currentMessages,
        turn.userMessage,
        turn.assistantMessage,
      ])
      setComposerValue('')
      await refreshSessions(chatSessionId)
    } catch {
      setError('Unable to save this message.')
    } finally {
      setMessagesState('idle')
    }
  }

  function startEditing(session: ChatSession) {
    setEditingSessionId(session.id)
    setEditingTitle(session.title)
    setOpenMenuSessionId(null)
  }

  async function saveTitle(chatSessionId: string) {
    const title = editingTitle.trim()
    if (title.length === 0) {
      return
    }

    setSessionsState('saving')
    setError(null)

    try {
      const updatedSession = await updateChatSessionTitle(chatSessionId, title)
      setSessions((currentSessions) =>
        currentSessions.map((session) =>
          session.id === updatedSession.id ? updatedSession : session,
        ),
      )
      setEditingSessionId(null)
      setEditingTitle('')
    } catch {
      setError('Unable to rename this chat.')
    } finally {
      setSessionsState('idle')
    }
  }

  async function handleDeleteSession(chatSessionId: string) {
    setSessionsState('saving')
    setError(null)
    setOpenMenuSessionId(null)

    try {
      await deleteChatSession(chatSessionId)
      setSessions((currentSessions) => {
        const nextSessions = currentSessions.filter((session) => session.id !== chatSessionId)
        if (activeSessionId === chatSessionId) {
          setActiveSessionId(nextSessions[0]?.id ?? null)
        }
        return nextSessions
      })
    } catch {
      setError('Unable to delete this chat.')
    } finally {
      setSessionsState('idle')
    }
  }

  async function refreshSessions(preferredSessionId: string) {
    const chatSessions = await listChatSessions()
    setSessions(chatSessions)
    setActiveSessionId(preferredSessionId)
  }

  const isBusy = sessionsState === 'saving' || messagesState === 'saving'
  const hasMessages = messages.length > 0

  return (
    <main className={`chat-page${isHistoryOpen ? ' has-history-open' : ''}`}>
      <aside className="chat-rail" aria-label="Primary chat navigation">
        <div className="rail-top">
          <div className="rail-logo" aria-label="Geni">
            G
          </div>
          <button
            aria-label="New chat"
            className="rail-button"
            disabled={sessionsState === 'saving'}
            onClick={handleCreateSession}
            type="button"
          >
            <Edit3 aria-hidden="true" size={21} />
          </button>
          <button
            aria-label="Toggle chat history"
            className={`rail-button${isHistoryOpen ? ' is-active' : ''}`}
            onClick={() => setIsHistoryOpen((currentValue) => !currentValue)}
            type="button"
          >
            <MessageCircle aria-hidden="true" size={22} />
          </button>
        </div>

        <button
          aria-label="Open profile"
          className="rail-profile"
          onClick={() => onNavigate(paths.profile)}
          type="button"
        >
          {user?.avatarUrl ? <img src={user.avatarUrl} alt="" /> : <span>{getInitials(user)}</span>}
        </button>
      </aside>

      <aside className="history-drawer" aria-label="Chat history" aria-hidden={!isHistoryOpen}>
        <div className="history-drawer-header">
          <div>
            <p>Geni</p>
            <strong>Chat history</strong>
          </div>
          <button aria-label="Close history" onClick={() => setIsHistoryOpen(false)} type="button">
            <X aria-hidden="true" size={18} />
          </button>
        </div>

        <nav className="chat-history" aria-label="Chat history">
          <div className="chat-history-title">
            <MessageSquareText aria-hidden="true" size={16} />
            <span>History</span>
          </div>

          {sessionsState === 'loading' ? (
            <div className="history-status" role="status">
              <Loader2 aria-hidden="true" className="button-spinner" size={16} />
              <span>Loading chats</span>
            </div>
          ) : null}

          {sessionsState !== 'loading' && sessions.length === 0 ? (
            <div className="history-empty">
              <p>No chats yet.</p>
              <button onClick={handleCreateSession} type="button">
                Start first chat
              </button>
            </div>
          ) : null}

          <div className="history-list">
            {sessions.map((session) => (
              <div
                className={`history-item${session.id === activeSessionId ? ' is-active' : ''}`}
                key={session.id}
              >
                {editingSessionId === session.id ? (
                  <form
                    className="history-edit"
                    onSubmit={(event) => {
                      event.preventDefault()
                      void saveTitle(session.id)
                    }}
                  >
                    <input
                      aria-label="Chat title"
                      autoFocus
                      onChange={(event) => setEditingTitle(event.target.value)}
                      value={editingTitle}
                    />
                    <button aria-label="Save title" type="submit">
                      <Check aria-hidden="true" size={16} />
                    </button>
                    <button
                      aria-label="Cancel rename"
                      onClick={() => setEditingSessionId(null)}
                      type="button"
                    >
                      <X aria-hidden="true" size={16} />
                    </button>
                  </form>
                ) : (
                  <>
                    <button
                      className="history-select"
                      onClick={() => {
                        setActiveSessionId(session.id)
                        setOpenMenuSessionId(null)
                        setIsHistoryOpen(false)
                      }}
                      type="button"
                    >
                      <span>{session.title}</span>
                      <small>{formatDate(session.updatedAt)}</small>
                    </button>
                    <div className="history-menu">
                      <button
                        aria-label={`Open actions for ${session.title}`}
                        onClick={() =>
                          setOpenMenuSessionId((currentId) =>
                            currentId === session.id ? null : session.id,
                          )
                        }
                        type="button"
                      >
                        <MoreVertical aria-hidden="true" size={16} />
                      </button>
                      {openMenuSessionId === session.id ? (
                        <div className="history-menu-popover">
                          <button onClick={() => startEditing(session)} type="button">
                            <Pencil aria-hidden="true" size={15} />
                            <span>Rename</span>
                          </button>
                          <button onClick={() => void handleDeleteSession(session.id)} type="button">
                            <Trash2 aria-hidden="true" size={15} />
                            <span>Delete</span>
                          </button>
                        </div>
                      ) : null}
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>
        </nav>
      </aside>

      <section className={`chat-workspace${hasMessages ? ' has-messages' : ''}`} aria-labelledby="chat-title">
        <header className="chat-floating-status">
          <CircleDashed aria-hidden="true" size={22} />
        </header>

        {error ? <p className="chat-error">{error}</p> : null}

        <div className={`message-panel${hasMessages ? ' has-messages' : ''}`} aria-live="polite">
          {messagesState === 'loading' ? (
            <div className="message-loading" role="status">
              <Loader2 aria-hidden="true" className="button-spinner" size={18} />
              <span>Loading history</span>
            </div>
          ) : null}

          {messagesState !== 'loading' && messages.length === 0 ? (
            <div className="empty-chat" id="chat-title" />
          ) : null}

          {messages.length > 0 ? (
            <div className="message-list">
              {messages.map((message) => (
                <article className={`message-row is-${message.role}`} key={message.id}>
                  <div className="message-bubble">
                    <p>{message.content}</p>
                    <time dateTime={message.createdAt}>{formatTime(message.createdAt)}</time>
                  </div>
                </article>
              ))}
            </div>
          ) : null}
        </div>

        <form className="composer" onSubmit={handleSendMessage}>
          <button
            aria-label="Create a new chat"
            className="composer-tool"
            disabled={sessionsState === 'saving'}
            onClick={handleCreateSession}
            type="button"
          >
            <Plus aria-hidden="true" size={25} />
          </button>
          <textarea
            aria-label="Message"
            onChange={(event) => setComposerValue(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault()
                event.currentTarget.form?.requestSubmit()
              }
            }}
            placeholder="Ask Geni anything..."
            rows={1}
            value={composerValue}
          />
          <button
            aria-label="Send message"
            className="composer-submit"
            disabled={isBusy || composerValue.trim().length === 0}
            type="submit"
          >
            {messagesState === 'saving' ? (
              <Loader2 aria-hidden="true" className="button-spinner" size={18} />
            ) : (
              <Send aria-hidden="true" size={20} />
            )}
          </button>
        </form>
      </section>
    </main>
  )
}

function createTitleFromMessage(content: string) {
  return content.length > 48 ? `${content.slice(0, 45)}...` : content
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    month: 'short',
    day: 'numeric',
  }).format(new Date(value))
}

function formatTime(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    hour: 'numeric',
    minute: '2-digit',
  }).format(new Date(value))
}

function getInitials(user: AuthenticatedUser | null) {
  if (user === null) {
    return <UserRound aria-hidden="true" size={18} />
  }

  return user.fullName
    .split(' ')
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()
}
