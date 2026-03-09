import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from 'react'
import { tokenStore } from '@/api/client'
import { authApi } from '@/api/auth'
import type { FreelancerMe } from '@/types/auth'

interface AuthContextValue {
  user: FreelancerMe | null
  isLoading: boolean        // true while the initial session check is in-flight
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  register: (payload: {
    email: string
    password: string
    first_name: string
    last_name: string
    username: string
  }) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<FreelancerMe | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const hasMounted = useRef(false)

  // ── Restore session on mount ───────────────────────────────────────────────
  useEffect(() => {
    if (hasMounted.current) return
    hasMounted.current = true

    const storedRefresh = localStorage.getItem('refresh_token')
    if (!storedRefresh) {
      setIsLoading(false)
      return
    }

    // Silently refresh to get a fresh access token
    fetch('/api/v1/auth/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: storedRefresh }),
    })
      .then(async res => {
        if (!res.ok) throw new Error('expired')
        const data = await res.json() as { access_token: string; refresh_token: string }
        tokenStore.set(data.access_token)
        localStorage.setItem('refresh_token', data.refresh_token)
        return authApi.getMe()
      })
      .then(me => setUser(me))
      .catch(() => {
        localStorage.removeItem('refresh_token')
        tokenStore.clear()
      })
      .finally(() => setIsLoading(false))
  }, [])

  // ── Login ──────────────────────────────────────────────────────────────────
  const login = useCallback(async (email: string, password: string) => {
    const tokens = await authApi.login({ email, password })
    tokenStore.set(tokens.access_token)
    localStorage.setItem('refresh_token', tokens.refresh_token)
    const me = await authApi.getMe()
    setUser(me)
  }, [])

  // ── Register ───────────────────────────────────────────────────────────────
  const register = useCallback(async (payload: {
    email: string
    password: string
    first_name: string
    last_name: string
    username: string
  }) => {
    const tokens = await authApi.register(payload)
    tokenStore.set(tokens.access_token)
    localStorage.setItem('refresh_token', tokens.refresh_token)
    const me = await authApi.getMe()
    setUser(me)
  }, [])

  // ── Refresh user ───────────────────────────────────────────────────────────
  const refreshUser = useCallback(async () => {
    const me = await authApi.getMe()
    setUser(me)
  }, [])

  // ── Logout ─────────────────────────────────────────────────────────────────
  const logout = useCallback(async () => {
    const rt = localStorage.getItem('refresh_token')
    if (rt) {
      try { await authApi.logout(rt) } catch { /* ignore */ }
    }
    localStorage.removeItem('refresh_token')
    tokenStore.clear()
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: user !== null,
        login,
        register,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
