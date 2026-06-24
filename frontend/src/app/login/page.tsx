'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { TrendingUp, User, KeyRound, ArrowRight, Loader2 } from 'lucide-react'
import { loginWithPassword } from '@/lib/auth'

export default function LoginPage() {
  const router = useRouter()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await loginWithPassword(username, password)
      router.push('/')
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 bg-green-500/10 rounded-2xl mb-4">
            <TrendingUp size={28} className="text-green-400" />
          </div>
          <h1 className="text-2xl font-bold text-white">TínHiệuCK</h1>
          <p className="text-sm text-gray-500 mt-1">Hệ thống tín hiệu chứng khoán VN</p>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 shadow-xl">
          <h2 className="text-lg font-semibold mb-1">Đăng nhập</h2>
          <p className="text-sm text-gray-500 mb-5">Nhập tên đăng nhập và mật khẩu.</p>
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="text-xs text-gray-500 block mb-1.5">Tên đăng nhập</label>
              <div className="relative">
                <User size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                <input
                  type="text"
                  value={username}
                  onChange={e => setUsername(e.target.value)}
                  required
                  autoFocus
                  autoComplete="username"
                  className="w-full pl-9 pr-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-green-500 transition-colors"
                  placeholder="username"
                />
              </div>
            </div>
            <div>
              <label className="text-xs text-gray-500 block mb-1.5">Mật khẩu</label>
              <div className="relative">
                <KeyRound size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                <input
                  type="password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                  className="w-full pl-9 pr-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-green-500 transition-colors"
                  placeholder="••••••••"
                />
              </div>
            </div>
            {error && <p className="text-red-400 text-sm">{error}</p>}
            <button
              type="submit"
              disabled={loading || !username || !password}
              className="w-full flex items-center justify-center gap-2 py-2.5 bg-green-600 hover:bg-green-500 disabled:opacity-50 rounded-lg text-sm font-semibold transition-colors"
            >
              {loading
                ? <><Loader2 size={15} className="animate-spin" /> Đang đăng nhập...</>
                : <><ArrowRight size={15} /> Đăng nhập</>
              }
            </button>
          </form>
        </div>

        <p className="text-center text-xs text-gray-600 mt-6">
          Chỉ tài khoản được cấp quyền mới có thể đăng nhập.
        </p>
      </div>
    </div>
  )
}
