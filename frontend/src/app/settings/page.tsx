'use client'
import { useState } from 'react'
import { Send, CheckCircle, XCircle } from 'lucide-react'
import { api } from '@/lib/api'

export default function SettingsPage() {
  const [token, setToken] = useState('')
  const [chatId, setChatId] = useState('')
  const [status, setStatus] = useState<'idle' | 'ok' | 'err'>('idle')
  const [msg, setMsg] = useState('')
  const [loading, setLoading] = useState(false)

  const testTelegram = async () => {
    setLoading(true)
    setStatus('idle')
    try {
      const res = await api.testTelegram(token, chatId)
      if (res.success) {
        setStatus('ok')
        setMsg('Gửi thành công! Kiểm tra Telegram của bạn.')
      } else {
        setStatus('err')
        setMsg(res.detail || 'Lỗi không xác định')
      }
    } catch (e: any) {
      setStatus('err')
      setMsg(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-lg space-y-8">
      <h1 className="text-2xl font-bold">⚙️ Cài đặt</h1>

      {/* Telegram */}
      <section className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
        <h2 className="text-lg font-semibold">🔔 Telegram Bot</h2>
        <p className="text-sm text-gray-400">
          Nhận thông báo tín hiệu mua/bán trực tiếp trên Telegram.
        </p>

        <div className="space-y-3">
          <div>
            <label className="text-xs text-gray-500 block mb-1">Bot Token</label>
            <input
              value={token}
              onChange={e => setToken(e.target.value)}
              placeholder="1234567890:ABCdef..."
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-blue-500 font-mono"
            />
            <p className="text-xs text-gray-600 mt-1">Lấy từ @BotFather → /newbot</p>
          </div>
          <div>
            <label className="text-xs text-gray-500 block mb-1">Chat ID</label>
            <input
              value={chatId}
              onChange={e => setChatId(e.target.value)}
              placeholder="987654321"
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-blue-500 font-mono"
            />
            <p className="text-xs text-gray-600 mt-1">Lấy từ @userinfobot → /start</p>
          </div>
        </div>

        <button
          onClick={testTelegram}
          disabled={!token || !chatId || loading}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded-lg text-sm font-medium transition-colors"
        >
          <Send size={14} />
          {loading ? 'Đang gửi...' : 'Kiểm tra kết nối'}
        </button>

        {status === 'ok' && (
          <div className="flex items-center gap-2 text-green-400 text-sm">
            <CheckCircle size={16} />
            {msg}
          </div>
        )}
        {status === 'err' && (
          <div className="flex items-center gap-2 text-red-400 text-sm">
            <XCircle size={16} />
            {msg}
          </div>
        )}
      </section>

      {/* Hướng dẫn deploy */}
      <section className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-3">
        <h2 className="text-lg font-semibold">🚀 Hướng dẫn Production</h2>
        <div className="text-sm text-gray-400 space-y-2">
          <p><b className="text-white">Backend (Railway):</b></p>
          <ol className="list-decimal list-inside space-y-1 ml-2">
            <li>Vào railway.app → New Project → Deploy from GitHub</li>
            <li>Chọn repo <code className="bg-gray-800 px-1 rounded">tinhieu-ck</code> → Root Directory: <code className="bg-gray-800 px-1 rounded">backend</code></li>
            <li>Thêm biến môi trường: <code className="bg-gray-800 px-1 rounded">TELEGRAM_TOKEN</code> và <code className="bg-gray-800 px-1 rounded">TELEGRAM_CHAT_ID</code></li>
            <li>Copy Railway URL (dạng <code className="bg-gray-800 px-1 rounded">*.railway.app</code>)</li>
          </ol>
          <p className="mt-3"><b className="text-white">Frontend (Vercel):</b></p>
          <ol className="list-decimal list-inside space-y-1 ml-2">
            <li>Vào vercel.com → New Project → Import từ GitHub</li>
            <li>Root Directory: <code className="bg-gray-800 px-1 rounded">frontend</code></li>
            <li>Thêm biến môi trường: <code className="bg-gray-800 px-1 rounded">NEXT_PUBLIC_API_URL</code> = Railway URL</li>
            <li>Deploy!</li>
          </ol>
        </div>
      </section>
    </div>
  )
}
