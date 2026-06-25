'use client'
import { useState, useEffect } from 'react'
import { Send, CheckCircle, XCircle, Clock, Bell, BellOff, Play, Loader2 } from 'lucide-react'
import { api, type SchedulerStatus, type SchedulerConfig } from '@/lib/api'

export default function SettingsPage() {
  // Telegram test
  const [token, setToken] = useState('')
  const [chatId, setChatId] = useState('')
  const [testStatus, setTestStatus] = useState<'idle' | 'ok' | 'err'>('idle')
  const [testMsg, setTestMsg] = useState('')
  const [testLoading, setTestLoading] = useState(false)

  // Scheduler
  const [sched, setSched] = useState<SchedulerStatus | null>(null)
  const [schedLoading, setSchedLoading] = useState(true)
  const [saveLoading, setSaveLoading] = useState(false)
  const [runLoading, setRunLoading] = useState(false)
  const [schedMsg, setSchedMsg] = useState('')
  const [schedErr, setSchedErr] = useState('')

  // Form state
  const [enabled, setEnabled] = useState(false)
  const [intervalMin, setIntervalMin] = useState(30)
  const [marketOnly, setMarketOnly] = useState(true)
  const [marketOpen, setMarketOpen] = useState('09:15')
  const [marketClose, setMarketClose] = useState('15:00')
  const [minSignals, setMinSignals] = useState(1)
  const [schedToken, setSchedToken] = useState('')
  const [schedChatId, setSchedChatId] = useState('')

  useEffect(() => {
    api.getScheduler()
      .then(s => {
        setSched(s)
        setEnabled(s.enabled)
        setIntervalMin(s.interval_minutes)
        setMarketOnly(s.market_only)
        setMarketOpen(s.market_open)
        setMarketClose(s.market_close)
        setMinSignals(s.min_signals)
      })
      .catch(() => {})
      .finally(() => setSchedLoading(false))
  }, [])

  const testTelegram = async () => {
    setTestLoading(true); setTestStatus('idle')
    try {
      const res = await api.testTelegram(token, chatId)
      if (res.success) { setTestStatus('ok'); setTestMsg('Gửi thành công! Kiểm tra Telegram.') }
      else { setTestStatus('err'); setTestMsg(res.detail || 'Lỗi không xác định') }
    } catch (e: any) { setTestStatus('err'); setTestMsg(e.message) }
    finally { setTestLoading(false) }
  }

  const saveScheduler = async () => {
    setSaveLoading(true); setSchedMsg(''); setSchedErr('')
    try {
      const cfg: SchedulerConfig = {
        enabled, interval_minutes: intervalMin, market_only: marketOnly,
        market_open: marketOpen, market_close: marketClose,
        min_signals: minSignals, telegram_token: schedToken, telegram_chat_id: schedChatId,
      }
      const s = await api.updateScheduler(cfg)
      setSched(s)
      setSchedMsg(enabled ? `Đã bật — quét mỗi ${intervalMin} phút` : 'Đã tắt lịch tự động')
    } catch (e: any) { setSchedErr(e.message) }
    finally { setSaveLoading(false) }
  }

  const runNow = async () => {
    setRunLoading(true); setSchedMsg(''); setSchedErr('')
    try {
      const res = await api.runNow()
      setSchedMsg(res.detail)
    } catch (e: any) { setSchedErr(e.message) }
    finally { setRunLoading(false) }
  }

  const INTERVALS = [
    { value: 5, label: '5 phút' }, { value: 15, label: '15 phút' },
    { value: 30, label: '30 phút' }, { value: 60, label: '1 giờ' },
    { value: 120, label: '2 giờ' }, { value: 240, label: '4 giờ' },
  ]

  return (
    <div className="max-w-lg space-y-6">
      <h1 className="text-2xl font-bold">Cài đặt</h1>

      {/* Scheduler */}
      <section className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-5">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Clock size={18} className="text-green-400" />
              Quét tín hiệu tự động
            </h2>
            <p className="text-xs text-gray-500 mt-0.5">Tự động quét và gửi Telegram khi có tín hiệu mua/bán</p>
          </div>
          {sched && (
            <span className={`text-xs px-2 py-1 rounded-full font-medium ${sched.enabled ? 'bg-green-500/15 text-green-400' : 'bg-gray-700 text-gray-400'}`}>
              {sched.enabled ? 'Đang bật' : 'Đang tắt'}
            </span>
          )}
        </div>

        {schedLoading ? (
          <div className="flex items-center gap-2 text-gray-500 text-sm"><Loader2 size={14} className="animate-spin" /> Đang tải...</div>
        ) : (
          <>
            {sched && (
              <div className="grid grid-cols-2 gap-2 text-xs bg-gray-800/50 rounded-lg p-3">
                <div className="text-gray-500">Lần quét gần nhất: <span className="text-gray-300">{sched.last_scan || '—'}</span></div>
                <div className="text-gray-500">Lần tiếp theo: <span className="text-gray-300">{sched.next_run || '—'}</span></div>
                <div className="text-gray-500 col-span-2">Telegram: <span className={sched.telegram_configured ? 'text-green-400' : 'text-yellow-400'}>{sched.telegram_configured ? 'Đã cấu hình (Railway env)' : 'Chưa cấu hình'}</span></div>
              </div>
            )}

            {/* Enable toggle */}
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Bật lịch tự động</span>
              <button
                onClick={() => setEnabled(!enabled)}
                className={`relative w-11 h-6 rounded-full transition-colors ${enabled ? 'bg-green-500' : 'bg-gray-600'}`}
              >
                <span className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform ${enabled ? 'translate-x-5' : ''}`} />
              </button>
            </div>

            {/* Interval */}
            <div>
              <label className="text-xs text-gray-500 block mb-2">Tần suất quét</label>
              <div className="grid grid-cols-3 gap-2">
                {INTERVALS.map(i => (
                  <button key={i.value} onClick={() => setIntervalMin(i.value)}
                    className={`py-2 text-xs rounded-lg border transition-colors ${intervalMin === i.value ? 'border-green-500 bg-green-500/10 text-green-400' : 'border-gray-700 text-gray-400 hover:border-gray-500'}`}>
                    {i.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Market hours */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs text-gray-500">Chỉ quét trong giờ giao dịch</label>
                <button onClick={() => setMarketOnly(!marketOnly)}
                  className={`relative w-9 h-5 rounded-full transition-colors ${marketOnly ? 'bg-green-500' : 'bg-gray-600'}`}>
                  <span className={`absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full transition-transform ${marketOnly ? 'translate-x-4' : ''}`} />
                </button>
              </div>
              {marketOnly && (
                <div className="flex gap-3 items-center">
                  <div className="flex-1">
                    <label className="text-xs text-gray-600 block mb-1">Mở cửa</label>
                    <input type="time" value={marketOpen} onChange={e => setMarketOpen(e.target.value)}
                      className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-green-500" />
                  </div>
                  <span className="text-gray-600 mt-5">—</span>
                  <div className="flex-1">
                    <label className="text-xs text-gray-600 block mb-1">Đóng cửa</label>
                    <input type="time" value={marketClose} onChange={e => setMarketClose(e.target.value)}
                      className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-green-500" />
                  </div>
                </div>
              )}
            </div>

            {/* Min signals */}
            <div>
              <label className="text-xs text-gray-500 block mb-2">
                Gửi Telegram khi có ít nhất <span className="text-white font-medium">{minSignals}</span> tín hiệu mua/bán
              </label>
              <input type="range" min={1} max={10} value={minSignals}
                onChange={e => setMinSignals(Number(e.target.value))}
                className="w-full accent-green-500" />
              <div className="flex justify-between text-xs text-gray-600 mt-1">
                <span>1 (mọi lúc)</span><span>5</span><span>10</span>
              </div>
            </div>

            {/* Telegram override */}
            <div className="border-t border-gray-800 pt-4 space-y-3">
              <p className="text-xs text-gray-500">
                Telegram Bot cho thông báo tự động<br/>
                <span className="text-gray-600">(Để trống nếu đã đặt TELEGRAM_TOKEN / TELEGRAM_CHAT_ID trong Railway)</span>
              </p>
              <div>
                <label className="text-xs text-gray-500 block mb-1">Bot Token</label>
                <input value={schedToken} onChange={e => setSchedToken(e.target.value)}
                  placeholder="Để trống nếu đã cấu hình Railway env"
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-green-500 font-mono" />
              </div>
              <div>
                <label className="text-xs text-gray-500 block mb-1">Chat ID</label>
                <input value={schedChatId} onChange={e => setSchedChatId(e.target.value)}
                  placeholder="Để trống nếu đã cấu hình Railway env"
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-green-500 font-mono" />
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-3 pt-1">
              <button onClick={saveScheduler} disabled={saveLoading}
                className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-green-600 hover:bg-green-500 disabled:opacity-50 rounded-lg text-sm font-semibold transition-colors">
                {saveLoading
                  ? <><Loader2 size={14} className="animate-spin" /> Đang lưu...</>
                  : <>{enabled ? <Bell size={14} /> : <BellOff size={14} />} Lưu cài đặt</>}
              </button>
              <button onClick={runNow} disabled={runLoading} title="Quét ngay và gửi Telegram"
                className="flex items-center gap-2 px-4 py-2.5 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 rounded-lg text-sm font-medium transition-colors">
                {runLoading ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
                Quét ngay
              </button>
            </div>

            {schedMsg && <p className="text-green-400 text-sm flex items-center gap-1.5"><CheckCircle size={14} />{schedMsg}</p>}
            {schedErr && <p className="text-red-400 text-sm flex items-center gap-1.5"><XCircle size={14} />{schedErr}</p>}
          </>
        )}
      </section>

      {/* Telegram test */}
      <section className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <Send size={18} className="text-blue-400" />
          Kiểm tra kết nối Telegram
        </h2>
        <p className="text-sm text-gray-400">Gửi tin nhắn thử để xác nhận Bot Token và Chat ID hoạt động.</p>
        <div className="space-y-3">
          <div>
            <label className="text-xs text-gray-500 block mb-1">Bot Token</label>
            <input value={token} onChange={e => setToken(e.target.value)} placeholder="1234567890:ABCdef..."
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-blue-500 font-mono" />
            <p className="text-xs text-gray-600 mt-1">Lấy từ @BotFather → /newbot</p>
          </div>
          <div>
            <label className="text-xs text-gray-500 block mb-1">Chat ID</label>
            <input value={chatId} onChange={e => setChatId(e.target.value)} placeholder="987654321"
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-blue-500 font-mono" />
            <p className="text-xs text-gray-600 mt-1">Lấy từ @userinfobot → /start</p>
          </div>
        </div>
        <button onClick={testTelegram} disabled={!token || !chatId || testLoading}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded-lg text-sm font-medium transition-colors">
          <Send size={14} />
          {testLoading ? 'Đang gửi...' : 'Kiểm tra kết nối'}
        </button>
        {testStatus === 'ok' && <div className="flex items-center gap-2 text-green-400 text-sm"><CheckCircle size={16} />{testMsg}</div>}
        {testStatus === 'err' && <div className="flex items-center gap-2 text-red-400 text-sm"><XCircle size={16} />{testMsg}</div>}
      </section>
    </div>
  )
}
