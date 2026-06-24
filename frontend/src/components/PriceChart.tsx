'use client'
import {
  ComposedChart, Line, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid, ReferenceLine,
} from 'recharts'
import type { StockBar } from '@/lib/api'

interface Props {
  data: StockBar[]
  ticker: string
}

const fmt = (v: number) => v.toLocaleString('vi-VN')

export default function PriceChart({ data, ticker }: Props) {
  return (
    <div className="space-y-4">
      {/* Price + Bollinger */}
      <div>
        <h3 className="text-sm text-gray-400 mb-2">Giá & Bollinger Bands — {ticker}</h3>
        <ResponsiveContainer width="100%" height={280}>
          <ComposedChart data={data} margin={{ left: 10, right: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
            <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#6b7280' }} tickLine={false} interval="preserveStartEnd" />
            <YAxis tickFormatter={fmt} tick={{ fontSize: 10, fill: '#6b7280' }} tickLine={false} width={75} />
            <Tooltip
              contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 8 }}
              formatter={(v: number) => fmt(v) + 'đ'}
              labelStyle={{ color: '#9ca3af' }}
            />
            <Line dataKey="bb_upper" stroke="#374151" dot={false} strokeDasharray="4 2" strokeWidth={1} name="BB Upper" />
            <Line dataKey="bb_lower" stroke="#374151" dot={false} strokeDasharray="4 2" strokeWidth={1} name="BB Lower" />
            <Line dataKey="close" stroke="#22c55e" dot={false} strokeWidth={2} name="Giá đóng cửa" />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* RSI */}
      <div>
        <h3 className="text-sm text-gray-400 mb-2">RSI (14)</h3>
        <ResponsiveContainer width="100%" height={100}>
          <ComposedChart data={data} margin={{ left: 10, right: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
            <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#6b7280' }} tickLine={false} interval="preserveStartEnd" />
            <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: '#6b7280' }} tickLine={false} width={30} />
            <Tooltip contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 8 }} labelStyle={{ color: '#9ca3af' }} />
            <ReferenceLine y={70} stroke="#ef4444" strokeDasharray="4 2" strokeWidth={1} />
            <ReferenceLine y={30} stroke="#22c55e" strokeDasharray="4 2" strokeWidth={1} />
            <Line dataKey="rsi" stroke="#a78bfa" dot={false} strokeWidth={2} name="RSI" />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* MACD */}
      <div>
        <h3 className="text-sm text-gray-400 mb-2">MACD</h3>
        <ResponsiveContainer width="100%" height={100}>
          <ComposedChart data={data} margin={{ left: 10, right: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
            <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#6b7280' }} tickLine={false} interval="preserveStartEnd" />
            <YAxis tick={{ fontSize: 10, fill: '#6b7280' }} tickLine={false} width={50} />
            <Tooltip contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 8 }} labelStyle={{ color: '#9ca3af' }} />
            <ReferenceLine y={0} stroke="#4b5563" strokeWidth={1} />
            <Line dataKey="macd" stroke="#60a5fa" dot={false} strokeWidth={1.5} name="MACD" />
            <Line dataKey="macd_signal" stroke="#f97316" dot={false} strokeWidth={1.5} name="Signal" />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Volume */}
      <div>
        <h3 className="text-sm text-gray-400 mb-2">Khối lượng</h3>
        <ResponsiveContainer width="100%" height={80}>
          <ComposedChart data={data} margin={{ left: 10, right: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
            <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#6b7280' }} tickLine={false} interval="preserveStartEnd" />
            <YAxis tick={{ fontSize: 10, fill: '#6b7280' }} tickLine={false} width={50}
              tickFormatter={v => (v / 1e6).toFixed(0) + 'M'} />
            <Tooltip contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 8 }} labelStyle={{ color: '#9ca3af' }}
              formatter={(v: number) => (v / 1e6).toFixed(2) + 'M'} />
            <Bar dataKey="volume" fill="#3b82f6" opacity={0.6} name="KL" />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
