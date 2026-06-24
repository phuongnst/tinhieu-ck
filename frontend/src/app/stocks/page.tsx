'use client'
import { useState } from 'react'
import useSWR from 'swr'
import { useRouter } from 'next/navigation'
import { Search } from 'lucide-react'
import { api } from '@/lib/api'

export default function StocksPage() {
  const [demo] = useState(true)
  const [q, setQ] = useState('')
  const router = useRouter()
  const { data: tickers } = useSWR(['stocks', demo], () => api.stocks(demo))

  const filtered = (tickers ?? []).filter(t => t.toUpperCase().includes(q.toUpperCase()))

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Danh sách cổ phiếu</h1>
      <div className="relative max-w-sm">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
        <input
          value={q}
          onChange={e => setQ(e.target.value)}
          placeholder="Tìm mã CK..."
          className="w-full pl-9 pr-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-blue-500"
        />
      </div>
      <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-2">
        {filtered.map(t => (
          <button
            key={t}
            onClick={() => router.push(`/stocks/${t}`)}
            className="py-2 px-3 bg-gray-900 border border-gray-800 hover:border-green-500 hover:text-green-400 rounded-lg text-sm font-medium transition-colors"
          >
            {t}
          </button>
        ))}
      </div>
    </div>
  )
}
