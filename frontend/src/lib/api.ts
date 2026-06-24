const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || ''

const headers = (): HeadersInit => ({
  'Content-Type': 'application/json',
  ...(API_KEY ? { 'X-API-Key': API_KEY } : {}),
})

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
    next: { revalidate: 300 },
    headers: headers(),
  })
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`)
  return res.json()
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    method: 'POST',
    headers: headers(),
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `API error ${res.status}`)
  }
  return res.json()
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
}
