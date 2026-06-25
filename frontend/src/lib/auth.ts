const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const TOKEN_KEY = 'tinhieu_token'
const USER_KEY = 'tinhieu_user'

export interface User {
  name: string
  username: string
}

const COOKIE_MAX_AGE = 60 * 60 * 24 // 24h

export function saveSession(token: string, user: User) {
  if (typeof window === 'undefined') return
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(USER_KEY, JSON.stringify(user))
  // Also save to cookie so middleware can read it server-side
  document.cookie = `${TOKEN_KEY}=${token}; path=/; max-age=${COOKIE_MAX_AGE}; SameSite=Lax`
}

export function getToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem(TOKEN_KEY)
}

export function getUser(): User | null {
  if (typeof window === 'undefined') return null
  try {
    const s = localStorage.getItem(USER_KEY)
    return s ? JSON.parse(s) : null
  } catch {
    return null
  }
}

export function clearSession() {
  if (typeof window === 'undefined') return
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
  document.cookie = `${TOKEN_KEY}=; path=/; max-age=0`
}

export function isLoggedIn(): boolean {
  return !!getToken()
}

export async function loginWithPassword(username: string, password: string): Promise<User> {
  const res = await fetch(`${API}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || 'Đăng nhập thất bại')
  const user: User = { name: data.name, username }
  saveSession(data.access_token, user)
  return user
}
