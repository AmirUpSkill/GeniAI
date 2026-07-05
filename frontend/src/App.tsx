import { AuthPage } from './features/auth/pages/auth-page'

function App() {
  const path = window.location.pathname

  if (path === '/' || path === '/auth') {
    return <AuthPage />
  }

  return <AuthPage />
}

export default App
