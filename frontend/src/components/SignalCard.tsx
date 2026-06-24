import clsx from 'clsx'
import type { Signal } from '@/lib/api'

const signalStyle = {
  BUY: 'bg-green-500/10 border-green-500/30 text-green-400',
  SELL: 'bg-red-500/10 border-red-500/30 text-red-400',
  HOLD: 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400',
}

const signalLabel = { BUY: '🟢 MUA', SELL: '🔴 BÁN', HOLD: '🟡 GIỮ' }

export default function SignalCard({ sig, rank }: { sig: Signal; rank: number }) {
  const scoreBar = Math.round(sig.final_score * 100)
  return (
    <div className={clsx('border rounded-xl p-4 flex flex-col gap-3', signalStyle[sig.signal])}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">#{rank}</span>
          <span className="font-bold text-xl tracking-wide">{sig.ticker}</span>
        </div>
        <span className={clsx('text-xs font-semibold px-2 py-0.5 rounded-full border', signalStyle[sig.signal])}>
          {signalLabel[sig.signal]}
        </span>
      </div>

      <div className="flex justify-between items-end">
        <div>
          <div className="text-2xl font-bold">{sig.price.toLocaleString('vi-VN')}đ</div>
          <div className="text-xs text-gray-500 mt-0.5">
            Vol ×{sig.volume_ratio?.toFixed(1) ?? '–'}
          </div>
        </div>
        <div className="text-right">
          <div className="text-xs text-gray-500">Score</div>
          <div className="text-2xl font-bold">{sig.final_score.toFixed(2)}</div>
        </div>
      </div>

      {/* Score bar */}
      <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
        <div
          className={clsx('h-full rounded-full', sig.signal === 'BUY' ? 'bg-green-500' : sig.signal === 'SELL' ? 'bg-red-500' : 'bg-yellow-500')}
          style={{ width: `${scoreBar}%` }}
        />
      </div>

      <div className="grid grid-cols-3 gap-2 text-xs">
        <Stat label="RSI" value={sig.rsi?.toFixed(0) ?? '–'} />
        <Stat label="ML" value={(sig.ml_prob * 100).toFixed(0) + '%'} />
        <Stat label="Rule" value={(sig.rule_score * 100).toFixed(0) + '%'} />
      </div>

      {sig.patterns.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {sig.patterns.map(p => (
            <span key={p} className="text-[10px] bg-gray-800 px-1.5 py-0.5 rounded text-gray-400">
              {p}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-gray-900/50 rounded p-1.5 text-center">
      <div className="text-gray-500">{label}</div>
      <div className="font-semibold text-gray-200">{value}</div>
    </div>
  )
}
