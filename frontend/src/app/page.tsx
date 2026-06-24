'use client'
import { useState } from 'react'
import useSWR from 'swr'
import { RefreshCw, Bell, Activity } from 'lucide-react'
import { api, type ScanResult } from '@/lib/api'
import SignalCard from '@/components/SignalCard'
import clsx from 'clsx'

export default function Dashboard() {
  const [demo, setDemo] = useState(true)
  const { data, error, isLoading, mutate } = useSWR<ScanResult>(
    ['signals', demo],
    () => api.signals(demo),
    { refreshInterval: 5 * 60 * 1000 }
  )

  const handleNotify = async () => {
    await api.notify(demo)
    alert('Đã gửi tín hiệu lên Telegram!')
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">📈 Tín Hiệu Chứng Khoán VN</h1>
          {data && (
            <p className="text-sm text-gray-500 mt-1">
              Cập nhật: {data.scan_time} · Phân tích {data.total_analyzed} mã
            </p>
          )}
        </div>
        <div className="flex items-center gap-2">
          {/* Demo toggle */}
          <label className="flex items-center gap-2 text-sm text-gray-400 cursor-pointer">
            <div
              onClick={() => setDemo(!demo)}
              className={clsx(
                'w-10 h-5 rounded-full transition-colors relative cursor-pointer',
                demo ? 'bg-blue-600' : 'bg-green-600'
              )}
            >
              <div className={clsx('w-4 h-4 bg-white rounded-full absolute top-0.5 transition-transform',
                demo ? 'left-0.5' : 'left-5.5')} />
            </div>
            {demo ? 'Demo' : 'Thật'}
          </label>
          <button
            onClick={() => mutate()}
            className="flex items-center gap-2 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm transition-colors"
          >
            <RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} />
            Làm mới
          </button>
          <button
            onClick={handleNotify}
            className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm transition-colors"
          >
            <Bell size={14} />
            Gửi Telegram
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-red-400 text-sm">
          Không thể kết nối backend. Kiểm tra <code className="bg-gray-900 px-1 rounded">NEXT_PUBLIC_API_URL</code> trong Vercel.
        </div>
      )}

      {/* Loading */}
      {isLoading && (
        <div className="flex items-center justify-center py-20 gap-3 text-gray-500">
          <Activity size={20} className="animate-pulse" />
          Đang phân tích {demo ? '20 mã demo' : 'toàn bộ thị trường'}...
        </div>
      )}

      {data && (
        <>
          {/* Stats row */}
          <div className="grid grid-cols-3 gap-4">
            <StatBox label="Tín hiệu MUA" value={data.buy.length} color="text-green-400" />
            <StatBox label="Tín hiệu BÁN" value={data.sell.length} color="text-red-400" />
            <StatBox label="Mã phân tích" value={data.total_analyzed} color="text-blue-400" />
          </div>

          {/* Buy signals */}
          {data.buy.length > 0 && (
            <section>
              <h2 className="text-lg font-semibold text-green-400 mb-3">🟢 Top MUA Mạnh</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {data.buy.map((sig, i) => (
                  <SignalCard key={sig.ticker} sig={sig} rank={i + 1} />
                ))}
              </div>
            </section>
          )}

          {/* Sell signals */}
          {data.sell.length > 0 && (
            <section>
              <h2 className="text-lg font-semibold text-red-400 mb-3">🔴 Cần Chú Ý / BÁN</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {data.sell.map((sig, i) => (
                  <SignalCard key={sig.ticker} sig={sig} rank={i + 1} />
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </div>
  )
}

function StatBox({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 text-center">
      <div className={clsx('text-3xl font-bold', color)}>{value}</div>
      <div className="text-xs text-gray-500 mt-1">{label}</div>
    </div>
  )
}
