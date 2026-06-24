"""
FastAPI backend for VN Stock Signal System.
Deploy on Railway: railway up
"""

import logging
import os
import re
import sys
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.security.api_key import APIKeyHeader
from jose import JWTError
from pydantic import BaseModel, EmailStr, field_validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request

# Add project root to path (works both locally and on Railway)
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root not in sys.path:
    sys.path.insert(0, root)

import config
import auth as auth_module
from data.fetcher import DataFetcher
from indicators import add_all_indicators
from signals.aggregator import SignalAggregator
from signals.ml_signal import MLSignalGenerator
from backtest.engine import Backtest
from notifications.telegram_bot import TelegramNotifier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Rate limiter ---
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="VN Stock Signal API", version="1.0.0", docs_url=None, redoc_url=None)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- CORS ---
_ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",")]
_wildcard = "*" in _ALLOWED_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if _wildcard else _ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key", "Authorization"],
    allow_credentials=not _wildcard,  # credentials không dùng được khi origin=*
)

# --- JWT auth ---
_oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/verify-otp", auto_error=False)


def get_current_user(token: Optional[str] = Depends(_oauth2)) -> dict:
    if not token:
        raise HTTPException(status_code=401, detail="Chưa đăng nhập")
    try:
        return auth_module.decode_token(token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Token không hợp lệ hoặc đã hết hạn")


# --- Legacy API Key (vẫn giữ cho backward compat) ---
_API_KEY = os.getenv("API_KEY", "")
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(key: Optional[str] = Security(_api_key_header)):
    if not _API_KEY:
        return
    if key != _API_KEY:
        raise HTTPException(status_code=403, detail="Invalid or missing API key")


# --- Ticker validation ---
_TICKER_RE = re.compile(r'^[A-Z0-9]{2,10}$')


def validate_ticker(ticker: str) -> str:
    t = ticker.upper().strip()
    if not _TICKER_RE.match(t):
        raise HTTPException(status_code=400, detail="Mã cổ phiếu không hợp lệ")
    return t

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

    @field_validator('token')
    @classmethod
    def token_format(cls, v: str) -> str:
        if not re.match(r'^\d+:[A-Za-z0-9_-]{35,}$', v):
            raise ValueError('Token Telegram không đúng định dạng')
        return v

    @field_validator('chat_id')
    @classmethod
    def chat_id_format(cls, v: str) -> str:
        if not re.match(r'^-?\d+$', v):
            raise ValueError('Chat ID phải là số nguyên')
        return v


# --- Endpoints ---

# --- Auth models ---
class OTPRequest(BaseModel):
    email: EmailStr

class OTPVerify(BaseModel):
    email: EmailStr
    otp: str

    @field_validator('otp')
    @classmethod
    def otp_digits(cls, v: str) -> str:
        if not re.match(r'^\d{6}$', v):
            raise ValueError('OTP phải là 6 chữ số')
        return v

class TokenOut(BaseModel):
    access_token: str
    token_type: str
    name: str
    email: str

class UserOut(BaseModel):
    name: str
    email: str


# --- Auth endpoints ---
@app.post("/auth/request-otp")
@limiter.limit("5/minute")
def request_otp(request: Request, body: OTPRequest):
    """Send OTP to registered email."""
    try:
        ok = auth_module.request_otp(body.email)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Không thể gửi email: {e}")
    if not ok:
        # Trả 200 để tránh email enumeration
        return {"detail": "Nếu email hợp lệ, mã OTP đã được gửi."}
    return {"detail": "Mã OTP đã được gửi. Kiểm tra hộp thư của bạn."}


@app.post("/auth/verify-otp", response_model=TokenOut)
@limiter.limit("10/minute")
def verify_otp(request: Request, body: OTPVerify):
    """Verify OTP and return JWT token."""
    try:
        token = auth_module.verify_otp(body.email, body.otp)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return TokenOut(
        access_token=token,
        token_type="bearer",
        name=auth_module.ADMIN_NAME,
        email=body.email,
    )


@app.get("/auth/me", response_model=UserOut)
def me(user: dict = Depends(get_current_user)):
    """Return current logged-in user info."""
    return UserOut(name=user.get("name", ""), email=user.get("sub", ""))


# --- Health (public) ---
@app.get("/api/health")
def health():
    return {"status": "ok", "time": datetime.now().isoformat()}


@app.get("/api/signals", response_model=ScanResult, dependencies=[Depends(get_current_user)])
@limiter.limit("10/minute")
def get_signals(request: Request, demo: bool = True, top_buy: int = 10, top_sell: int = 5):
    top_buy = min(max(top_buy, 1), 20)
    top_sell = min(max(top_sell, 1), 10)
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


@app.get("/api/stocks", response_model=List[str], dependencies=[Depends(get_current_user)])
@limiter.limit("20/minute")
def get_stocks(request: Request, demo: bool = True):
    """Return list of available stock tickers."""
    fetcher = DataFetcher(demo=demo)
    return fetcher.get_stock_list()


@app.get("/api/stocks/{ticker}", response_model=List[StockBar], dependencies=[Depends(get_current_user)])
@limiter.limit("30/minute")
def get_stock_data(request: Request, ticker: str, days: int = 180, demo: bool = True):
    ticker = validate_ticker(ticker)
    days = min(max(days, 10), 365)
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


@app.get("/api/backtest", response_model=BacktestOut, dependencies=[Depends(get_current_user)])
@limiter.limit("3/minute")
def run_backtest(request: Request, demo: bool = True):
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


@app.post("/api/telegram/test", dependencies=[Depends(get_current_user)])
@limiter.limit("5/minute")
def test_telegram(request: Request, cfg: TelegramConfig):
    """Send a test message to verify Telegram config."""
    try:
        notifier = TelegramNotifier(cfg.token, cfg.chat_id)
        notifier.send_text("✅ Kết nối Telegram thành công! Hệ thống tín hiệu cổ phiếu VN đã sẵn sàng.")
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/notify", dependencies=[Depends(get_current_user)])
@limiter.limit("5/minute")
def send_notification(request: Request, demo: bool = True):
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
