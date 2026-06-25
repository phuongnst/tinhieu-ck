import { getToken } from './auth'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const headers = (): HeadersInit => {
  const token = getToken()
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }
}

export interface Signal {
  ticker: string
  signal: 'BUY' | 'SELL' | 'HOLD'
  final_score: number
  rule_score: number
  ml_prob: number
  price: number
  rsi: number | null
  macd_hist: number | null
  volume_ratio: number | null
  patterns: string[]
}

export interface ScanResult {
  buy: Signal[]
  sell: Signal[]
  total_analyzed: number
  scan_time: string
}

export interface StockBar {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  rsi: number | null
  macd: number | null
  macd_signal: number | null
  bb_upper: number | null
  bb_lower: number | null
}

export interface BacktestResult {
  total_return_pct: number
  win_rate: number
  sharpe_ratio: number
  max_drawdown_pct: number
  n_trades: number
  avg_hold_days: number
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    next: { revalidate: 0 },
    headers: headers(),
  })
  if (res.status === 401) {
    if (typeof window !== 'undefined') window.location.href = '/login'
    throw new Error('Phiên đăng nhập hết hạn')
  }
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`)
  return res.json()
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    method: 'POST',
    headers: headers(),
    body: body ? JSON.stringify(body) : undefined,
  })
  if (res.status === 401) {
    if (typeof window !== 'undefined') window.location.href = '/login'
    throw new Error('Phiên đăng nhập hết hạn')
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `API error ${res.status}`)
  }
  return res.json()
}

export interface SchedulerStatus {
  enabled: boolean
  interval_minutes: number
  market_only: boolean
  market_open: string
  market_close: string
  min_signals: number
  next_run: string | null
  last_scan: string | null
  telegram_configured: boolean
}

export interface SchedulerConfig {
  enabled: boolean
  interval_minutes: number
  market_only: boolean
  market_open: string
  market_close: string
  min_signals: number
  telegram_token: string
  telegram_chat_id: string
}

export const api = {
  signals: (demo = true) => get<ScanResult>(`/api/signals?demo=${demo}&top_buy=10&top_sell=5`),
  stocks: (demo = true) => get<string[]>(`/api/stocks?demo=${demo}`),
  stockData: (ticker: string, days = 180, demo = true) =>
    get<StockBar[]>(`/api/stocks/${ticker}?days=${days}&demo=${demo}`),
  backtest: (demo = true) => get<BacktestResult>(`/api/backtest?demo=${demo}`),
  testTelegram: (token: string, chatId: string) =>
    post<{ success: boolean; detail?: string }>('/api/telegram/test', { token, chat_id: chatId }),
  notify: (demo = true) =>
    post<{ success: boolean }>(`/api/notify?demo=${demo}`),
  getScheduler: () => get<SchedulerStatus>('/api/scheduler'),
  updateScheduler: (cfg: SchedulerConfig) => post<SchedulerStatus>('/api/scheduler', cfg),
  runNow: () => post<{ detail: string }>('/api/scheduler/run-now'),
}
