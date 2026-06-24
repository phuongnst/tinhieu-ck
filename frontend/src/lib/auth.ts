const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const TOKEN_KEY = 'tinhieu_token'
const USER_KEY = 'tinhieu_user'

export interface User {
  name: string
  email: string
}

export function saveSession(token: string, user: User) {
  if (typeof window === 'undefined') return
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(USER_KEY, JSON.stringify(user))
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
}

export function isLoggedIn(): boolean {
  return !!getToken()
}

export async function requestOTP(email: string): Promise<string> {
  const res = await fetch(`${API}/auth/request-otp`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || 'Lỗi gửi OTP')
  return data.detail
}

export async function verifyOTP(email: string, otp: string): Promise<User> {
  const res = await fetch(`${API}/auth/verify-otp`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, otp }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || 'OTP không hợp lệ')
  const user: User = { name: data.name, email: data.email }
  saveSession(data.access_token, user)
  return user
}
