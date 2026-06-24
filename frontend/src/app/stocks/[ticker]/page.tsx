'use client'
import { useState } from 'react'
import useSWR from 'swr'
import { useParams, useRouter } from 'next/navigation'
import { ArrowLeft } from 'lucide-react'
import { api } from '@/lib/api'
import PriceChart from '@/components/PriceChart'

const PERIODS = [
  { label: '1T', days: 30 },
  { label: '3T', days: 90 },
  { label: '6T', days: 180 },
  { label: '1N', days: 365 },
]

export default function StockDetailPage() {
  const { ticker } = useParams<{ ticker: string }>()
  const router = useRouter()
  const [days, setDays] = useState(180)
  const { data, isLoading } = useSWR(['stock', ticker, days], () => api.stockData(ticker, days))

  const last = data?.[data.length - 1]
  const first = data?.[0]
  const chg = last && first ? ((last.close - first.close) / first.close * 100) : null

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <button onClick={() => router.back()} className="p-2 hover:bg-gray-800 rounded-lg transition-colors">
          <ArrowLeft size={18} />
        </button>
        <div>
          <h1 className="text-2xl font-bold">{ticker.toUpperCase()}</h1>
          {last && (
            <div className="flex items-center gap-3 mt-1">
              <span className="text-xl font-semibold">{last.close.toLocaleString('vi-VN')}đ</span>
              {chg !== null && (
                <span className={`text-sm font-medium ${chg >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {chg >= 0 ? '+' : ''}{chg.toFixed(2)}%
                </span>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Period selector */}
      <div className="flex gap-2">
        {PERIODS.map(p => (
          <button
            key={p.days}
            onClick={() => setDays(p.days)}
            className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
              days === p.days ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:text-white'
            }`}
          >
            {p.label}
          </button>
        ))}
      </div>

      {/* Stats */}
      {last && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <StatBox label="RSI (14)" value={last.rsi?.toFixed(1) ?? '–'} />
          <StatBox label="MACD" value={last.macd?.toFixed(2) ?? '–'} />
          <StatBox label="BB Upper" value={last.bb_upper?.toLocaleString('vi-VN') ?? '–'} />
          <StatBox label="BB Lower" value={last.bb_lower?.toLocaleString('vi-VN') ?? '–'} />
        </div>
      )}

      {isLoading && <div className="text-gray-500 text-sm">Đang tải dữ liệu...</div>}
      {data && data.length > 0 && <PriceChart data={data} ticker={ticker.toUpperCase()} />}
    </div>
  )
}

function StatBox({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-3">
      <div className="text-xs text-gray-500">{label}</div>
      <div className="text-lg font-semibold mt-0.5">{value}</div>
    </div>
  )
}
