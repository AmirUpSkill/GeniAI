import { useCallback, useEffect, useState } from 'react'
import { ChatPage } from './features/chat/pages/chat-page'
import { AuthPage } from './features/auth/pages/auth-page'
import { ProfilePage } from './features/profile/pages/profile-page'
import { paths } from './lib/paths'

function App() {
  const [path, setPath] = useState(() => window.location.pathname)

  useEffect(() => {
    function handlePopState() {
      setPath(window.location.pathname)
    }

    window.addEventListener('popstate', handlePopState)

    return () => {
      window.removeEventListener('popstate', handlePopState)
    }
  }, [])

  const navigate = useCallback((nextPath: string) => {
    window.history.pushState(null, '', nextPath)
    setPath(nextPath)
  }, [])

  if (path === '/' || path === '/auth') {
    return <AuthPage />
  }

  if (path === paths.profile) {
    return <ProfilePage onNavigate={navigate} />
  }

  if (path === paths.chat) {
    return <ChatPage onNavigate={navigate} />
  }

  return <AuthPage />
}

export default App
