'use client'
import { useState } from 'react'
import useSWR from 'swr'
import { BarChart2 } from 'lucide-react'
import { api, type BacktestResult } from '@/lib/api'
import clsx from 'clsx'

export default function BacktestPage() {
  const [demo, setDemo] = useState(true)
  const [run, setRun] = useState(false)
  const { data, isLoading } = useSWR<BacktestResult>(
    run ? ['backtest', demo] : null,
    () => api.backtest(demo)
  )

  return (
    <div className="space-y-6 max-w-2xl">
      <h1 className="text-2xl font-bold">📊 Backtest Chiến lược</h1>
      <p className="text-sm text-gray-400">
        Mô phỏng chiến lược mua/bán trên dữ liệu lịch sử để đánh giá hiệu quả.<br />
        Vốn ban đầu: <b>100,000,000đ</b> · Take profit: <b>5%</b> · Stop loss: <b>3%</b>
      </p>

      <div className="flex items-center gap-3">
        <label className="flex items-center gap-2 text-sm text-gray-400">
          <input type="checkbox" checked={demo} onChange={e => setDemo(e.target.checked)}
            className="rounded" />
          Chế độ Demo (nhanh hơn)
        </label>
        <button
          onClick={() => setRun(true)}
          disabled={isLoading}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
        >
          <BarChart2 size={16} />
          {isLoading ? 'Đang chạy...' : 'Chạy Backtest'}
        </button>
      </div>

      {data && (
        <div className="grid grid-cols-2 gap-4">
          <ResultCard
            label="Lợi nhuận"
            value={`${data.total_return_pct > 0 ? '+' : ''}${data.total_return_pct.toFixed(2)}%`}
            color={data.total_return_pct >= 0 ? 'text-green-400' : 'text-red-400'}
          />
          <ResultCard label="Win Rate" value={`${data.win_rate.toFixed(1)}%`}
            color={data.win_rate >= 50 ? 'text-green-400' : 'text-red-400'} />
          <ResultCard label="Sharpe Ratio" value={data.sharpe_ratio.toFixed(3)}
            color={data.sharpe_ratio >= 1 ? 'text-green-400' : data.sharpe_ratio >= 0 ? 'text-yellow-400' : 'text-red-400'} />
          <ResultCard label="Max Drawdown" value={`${data.max_drawdown_pct.toFixed(2)}%`}
            color="text-red-400" />
          <ResultCard label="Số giao dịch" value={String(data.n_trades)} color="text-blue-400" />
          <ResultCard label="Giữ trung bình" value={`${data.avg_hold_days.toFixed(1)} ngày`}
            color="text-blue-400" />
        </div>
      )}

      {data && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 text-sm text-gray-400">
          ⚠️ Kết quả backtest dựa trên dữ liệu quá khứ và không đảm bảo lợi nhuận tương lai.
          Luôn quản lý rủi ro khi giao dịch thực tế.
        </div>
      )}
    </div>
  )
}

function ResultCard({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <div className="text-xs text-gray-500 mb-1">{label}</div>
      <div className={clsx('text-3xl font-bold', color)}>{value}</div>
    </div>
  )
}
