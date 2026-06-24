"""
FastAPI backend for VN Stock Signal System.
Deploy on Railway: railway up
"""

import logging
import os
import sys
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add parent dir to path so we can import existing modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from data.fetcher import DataFetcher
from indicators import add_all_indicators
from signals.aggregator import SignalAggregator
from signals.ml_signal import MLSignalGenerator
from backtest.engine import Backtest
from notifications.telegram_bot import TelegramNotifier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="VN Stock Signal API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Global state (cached) ---
_cache: dict = {}
_ml_gen: Optional[MLSignalGenerator] = None
_last_scan: Optional[datetime] = None


def get_ml_gen() -> MLSignalGenerator:
    global _ml_gen
    if _ml_gen is None:
        _ml_gen = MLSignalGenerator()
        _ml_gen.load()
    return _ml_gen


def get_ticker_dfs(demo: bool = False) -> dict:
    key = f"ticker_dfs_{demo}"
    if key in _cache:
        return _cache[key]
    fetcher = DataFetcher(demo=demo)
    tickers = fetcher.get_stock_list()
    result = {}
    for ticker in tickers:
        try:
            df = fetcher.get_ohlcv(ticker)
            if df is not None and len(df) >= 50:
                result[ticker] = add_all_indicators(df)
        except Exception as e:
            logger.warning(f"Skip {ticker}: {e}")
    _cache[key] = result
    return result


# --- Pydantic models ---
class SignalOut(BaseModel):
    ticker: str
    signal: str
    final_score: float
    rule_score: float
    ml_prob: float
    price: float
    rsi: Optional[float]
    macd_hist: Optional[float]
    volume_ratio: Optional[float]
    patterns: List[str]


class ScanResult(BaseModel):
    buy: List[SignalOut]
    sell: List[SignalOut]
    total_analyzed: int
    scan_time: str


class BacktestOut(BaseModel):
    total_return_pct: float
    win_rate: float
    sharpe_ratio: float
    max_drawdown_pct: float
    n_trades: int
    avg_hold_days: float


class StockBar(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_lower: Optional[float] = None


class TelegramConfig(BaseModel):
    token: str
    chat_id: str


# --- Endpoints ---

@app.get("/api/health")
def health():
    return {"status": "ok", "time": datetime.now().isoformat()}


@app.get("/api/signals", response_model=ScanResult)
def get_signals(demo: bool = True, top_buy: int = 10, top_sell: int = 5):
    """Run full signal scan and return ranked buy/sell list."""
    global _last_scan
    try:
        ticker_dfs = get_ticker_dfs(demo=demo)
        ml_gen = get_ml_gen()

        if not ml_gen.model.is_trained:
            ml_gen.train_on_all(ticker_dfs)
            ml_gen.save()

        aggregator = SignalAggregator(
            rule_weight=config.RULE_WEIGHT,
            ml_weight=config.ML_WEIGHT,
            buy_threshold=config.BUY_THRESHOLD,
            sell_threshold=config.SELL_THRESHOLD,
            ml_generator=ml_gen,
        )
        result = aggregator.rank_signals(ticker_dfs, top_buy=top_buy, top_sell=top_sell)
        _last_scan = datetime.now()

        def to_out(sig) -> SignalOut:
            d = sig.to_dict()
            return SignalOut(
                ticker=d['ticker'], signal=d['signal'],
                final_score=d['final_score'], rule_score=d['rule_score'],
                ml_prob=d['ml_prob'], price=d['price'],
                rsi=d.get('rsi'), macd_hist=d.get('macd_hist'),
                volume_ratio=d.get('volume_ratio'),
                patterns=d.get('patterns', []),
            )

        return ScanResult(
            buy=[to_out(s) for s in result['buy']],
            sell=[to_out(s) for s in result['sell']],
            total_analyzed=len(result['all']),
            scan_time=_last_scan.strftime('%d/%m/%Y %H:%M:%S'),
        )
    except Exception as e:
        logger.error(f"Signal scan error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stocks", response_model=List[str])
def get_stocks(demo: bool = True):
    """Return list of available stock tickers."""
    fetcher = DataFetcher(demo=demo)
    return fetcher.get_stock_list()


@app.get("/api/stocks/{ticker}", response_model=List[StockBar])
def get_stock_data(ticker: str, days: int = 180, demo: bool = True):
    """Return OHLCV + indicators for a single ticker."""
    try:
        fetcher = DataFetcher(demo=demo)
        df = fetcher.get_ohlcv(ticker.upper())
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail=f"No data for {ticker}")
        df = add_all_indicators(df)
        df = df.tail(days)
        bars = []
        for date, row in df.iterrows():
            bars.append(StockBar(
                date=str(date.date()),
                open=round(float(row['open']), 0),
                high=round(float(row['high']), 0),
                low=round(float(row['low']), 0),
                close=round(float(row['close']), 0),
                volume=float(row['volume']),
                rsi=round(float(row['RSI_14']), 1) if 'RSI_14' in row and row['RSI_14'] == row['RSI_14'] else None,
                macd=round(float(row['MACD']), 2) if 'MACD' in row and row['MACD'] == row['MACD'] else None,
                macd_signal=round(float(row['MACD_signal']), 2) if 'MACD_signal' in row and row['MACD_signal'] == row['MACD_signal'] else None,
                bb_upper=round(float(row['BB_upper']), 0) if 'BB_upper' in row and row['BB_upper'] == row['BB_upper'] else None,
                bb_lower=round(float(row['BB_lower']), 0) if 'BB_lower' in row and row['BB_lower'] == row['BB_lower'] else None,
            ))
        return bars
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/backtest", response_model=BacktestOut)
def run_backtest(demo: bool = True):
    """Run strategy backtest on historical data."""
    try:
        ticker_dfs = get_ticker_dfs(demo=demo)
        from signals.rule_based import RuleBasedScorer
        scorer = RuleBasedScorer()

        def signal_fn(ticker, df_slice):
            s = scorer.score_normalized(df_slice)
            if s >= config.BUY_THRESHOLD: return 'BUY'
            if s <= config.SELL_THRESHOLD: return 'SELL'
            return 'HOLD'

        engine = Backtest(
            initial_capital=config.INITIAL_CAPITAL,
            take_profit_pct=config.TAKE_PROFIT_PCT,
            stop_loss_pct=config.STOP_LOSS_PCT,
        )
        result = engine.run(ticker_dfs, signal_fn)
        return BacktestOut(**result.to_dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/telegram/test")
def test_telegram(cfg: TelegramConfig):
    """Send a test message to verify Telegram config."""
    try:
        notifier = TelegramNotifier(cfg.token, cfg.chat_id)
        notifier.send_text("✅ Kết nối Telegram thành công! Hệ thống tín hiệu cổ phiếu VN đã sẵn sàng.")
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/notify")
def send_notification(demo: bool = True):
    """Trigger immediate signal scan + Telegram notification."""
    if not config.TELEGRAM_TOKEN:
        raise HTTPException(status_code=400, detail="TELEGRAM_TOKEN not configured")
    try:
        ticker_dfs = get_ticker_dfs(demo=demo)
        ml_gen = get_ml_gen()
        aggregator = SignalAggregator(ml_generator=ml_gen)
        signals = aggregator.rank_signals(ticker_dfs)
        notifier = TelegramNotifier(config.TELEGRAM_TOKEN, config.TELEGRAM_CHAT_ID)
        notifier.send_signals(signals)
        return {"success": True, "buy": len(signals['buy']), "sell": len(signals['sell'])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("api:app", host="0.0.0.0", port=port, reload=False)
