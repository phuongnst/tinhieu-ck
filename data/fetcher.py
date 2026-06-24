"""
Data fetcher for Vietnamese stock market (HOSE, HNX, UPCOM).
Primary: vnstock library
Fallback: manual HTTPS requests to public APIs
"""

import logging
import time
from datetime import datetime, timedelta
from typing import List, Optional

import numpy as np
import pandas as pd
import requests

logger = logging.getLogger(__name__)


def _make_demo_ohlcv(ticker: str, days: int = 365) -> pd.DataFrame:
    """Generate synthetic OHLCV data for demo/testing purposes."""
    np.random.seed(hash(ticker) % (2**31))
    dates = pd.date_range(end=datetime.now(), periods=days, freq='B')
    price = 50_000 + np.random.randn() * 20_000
    prices = [price]
    for _ in range(len(dates) - 1):
        change = np.random.randn() * 0.02
        price = prices[-1] * (1 + change)
        price = max(price, 1000)
        prices.append(price)

    prices = np.array(prices)
    highs = prices * (1 + np.abs(np.random.randn(len(prices)) * 0.01))
    lows = prices * (1 - np.abs(np.random.randn(len(prices)) * 0.01))
    opens = prices * (1 + np.random.randn(len(prices)) * 0.005)
    volumes = np.abs(np.random.randn(len(prices)) * 500_000 + 1_000_000).astype(int)

    df = pd.DataFrame({
        'open': opens,
        'high': highs,
        'low': lows,
        'close': prices,
        'volume': volumes,
    }, index=dates)
    df.index.name = 'date'
    return df


def _fetch_cafef_ohlcv(ticker: str, start: str, end: str) -> Optional[pd.DataFrame]:
    """Fallback: scrape from CafeF API."""
    try:
        start_dt = datetime.strptime(start, '%Y-%m-%d')
        end_dt = datetime.strptime(end, '%Y-%m-%d')
        # CafeF uses Unix timestamps
        url = (
            f"https://s.cafef.vn/ajax/HistoryData.aspx"
            f"?Symbol={ticker}&StartDate={start_dt.strftime('%d/%m/%Y')}"
            f"&EndDate={end_dt.strftime('%d/%m/%Y')}&PageIndex=1&PageSize=500"
        )
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://cafef.vn',
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        rows = data.get('Data', {}).get('Data', [])
        if not rows:
            return None
        records = []
        for r in rows:
            records.append({
                'date': pd.to_datetime(r.get('Ngay', ''), dayfirst=True),
                'open': float(r.get('GiaMoCua', 0) or 0) * 1000,
                'high': float(r.get('GiaCaoNhat', 0) or 0) * 1000,
                'low': float(r.get('GiaThapNhat', 0) or 0) * 1000,
                'close': float(r.get('GiaDongCua', 0) or 0) * 1000,
                'volume': int(r.get('KhoiLuong', 0) or 0),
            })
        df = pd.DataFrame(records).set_index('date').sort_index()
        df = df[(df.index >= start_dt) & (df.index <= end_dt)]
        return df if not df.empty else None
    except Exception as e:
        logger.warning(f"CafeF fallback failed for {ticker}: {e}")
        return None


def _fetch_vnstock_ohlcv(ticker: str, start: str, end: str) -> Optional[pd.DataFrame]:
    """Primary: use vnstock library."""
    try:
        from vnstock import stock_historical_data
        df = stock_historical_data(
            symbol=ticker,
            start_date=start,
            end_date=end,
            resolution='1D',
            type='stock',
        )
        if df is None or df.empty:
            return None
        # Normalize column names
        col_map = {
            'open': 'open', 'high': 'high', 'low': 'low',
            'close': 'close', 'volume': 'volume',
            'Open': 'open', 'High': 'high', 'Low': 'low',
            'Close': 'close', 'Volume': 'volume',
        }
        df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
        if 'time' in df.columns:
            df['date'] = pd.to_datetime(df['time'])
            df = df.set_index('date')
        elif df.index.name != 'date':
            df.index = pd.to_datetime(df.index)
            df.index.name = 'date'
        needed = ['open', 'high', 'low', 'close', 'volume']
        for col in needed:
            if col not in df.columns:
                return None
        return df[needed].sort_index()
    except ImportError:
        logger.warning("vnstock not installed")
        return None
    except Exception as e:
        logger.warning(f"vnstock failed for {ticker}: {e}")
        return None


def _fetch_vnstock_v3_ohlcv(ticker: str, start: str, end: str) -> Optional[pd.DataFrame]:
    """Try vnstock v3 API style."""
    try:
        from vnstock import Vnstock
        stock = Vnstock().stock(symbol=ticker, source='VCI')
        df = stock.quote.history(start=start, end=end, interval='1D')
        if df is None or df.empty:
            return None
        col_map = {
            'open': 'open', 'high': 'high', 'low': 'low',
            'close': 'close', 'volume': 'volume',
            'Open': 'open', 'High': 'high', 'Low': 'low',
            'Close': 'close', 'Volume': 'volume',
        }
        df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
        if 'time' in df.columns:
            df.index = pd.to_datetime(df['time'])
            df.index.name = 'date'
        elif not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
            df.index.name = 'date'
        needed = ['open', 'high', 'low', 'close', 'volume']
        for col in needed:
            if col not in df.columns:
                return None
        return df[needed].sort_index()
    except Exception as e:
        logger.warning(f"vnstock v3 failed for {ticker}: {e}")
        return None


def get_ohlcv(
    ticker: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    resolution: str = '1D',
    demo: bool = False,
) -> pd.DataFrame:
    """
    Fetch OHLCV data for a Vietnamese stock ticker.

    Args:
        ticker: Stock symbol (e.g. 'VNM', 'VCB')
        start: Start date YYYY-MM-DD (default: 1 year ago)
        end: End date YYYY-MM-DD (default: today)
        resolution: Data interval ('1D', '1W')
        demo: If True, generate synthetic data

    Returns:
        DataFrame with columns [open, high, low, close, volume]
    """
    if end is None:
        end = datetime.now().strftime('%Y-%m-%d')
    if start is None:
        start = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

    if demo:
        logger.debug(f"Demo mode: generating synthetic data for {ticker}")
        return _make_demo_ohlcv(ticker)

    # Try vnstock v3 first
    df = _fetch_vnstock_v3_ohlcv(ticker, start, end)
    if df is not None and not df.empty:
        logger.info(f"Fetched {ticker} via vnstock v3: {len(df)} rows")
        return df

    # Try vnstock v2
    df = _fetch_vnstock_ohlcv(ticker, start, end)
    if df is not None and not df.empty:
        logger.info(f"Fetched {ticker} via vnstock: {len(df)} rows")
        return df

    # Fallback to CafeF
    df = _fetch_cafef_ohlcv(ticker, start, end)
    if df is not None and not df.empty:
        logger.info(f"Fetched {ticker} via CafeF: {len(df)} rows")
        return df

    # Last resort: demo data with a warning
    logger.warning(f"All sources failed for {ticker}, using synthetic demo data")
    return _make_demo_ohlcv(ticker)


def get_stock_list(exchange: str = 'all', demo: bool = False) -> List[str]:
    """
    Return list of all stock tickers on Vietnamese exchanges.

    Args:
        exchange: 'HOSE', 'HNX', 'UPCOM', or 'all'
        demo: If True, return a small demo list

    Returns:
        List of ticker strings
    """
    from config import DEMO_TICKERS

    if demo:
        return DEMO_TICKERS

    # Try vnstock v3
    try:
        from vnstock import Vnstock
        vn = Vnstock()
        all_symbols = vn.stock(symbol='ACB', source='VCI').listing.symbols_by_exchange()
        if all_symbols is not None and not all_symbols.empty:
            col = 'symbol' if 'symbol' in all_symbols.columns else all_symbols.columns[0]
            exch_col = None
            for c in ['exchange', 'comGroupCode', 'floor']:
                if c in all_symbols.columns:
                    exch_col = c
                    break
            if exchange != 'all' and exch_col:
                all_symbols = all_symbols[
                    all_symbols[exch_col].str.upper() == exchange.upper()
                ]
            return all_symbols[col].tolist()
    except Exception as e:
        logger.warning(f"vnstock v3 stock list failed: {e}")

    # Try vnstock v2
    try:
        from vnstock import listing_companies
        df = listing_companies()
        if df is not None and not df.empty:
            col = 'ticker' if 'ticker' in df.columns else df.columns[0]
            return df[col].tolist()
    except Exception as e:
        logger.warning(f"vnstock v2 stock list failed: {e}")

    # Fallback to hardcoded popular tickers
    logger.warning("Could not fetch stock list, using demo tickers")
    return DEMO_TICKERS


def get_top_movers(n: int = 10, demo: bool = False) -> dict:
    """
    Return top gainers and losers for the current session.

    Args:
        n: Number of top/bottom stocks to return
        demo: If True, generate synthetic movers

    Returns:
        dict with keys 'gainers' and 'losers', each a list of dicts
    """
    if demo:
        import random
        from config import DEMO_TICKERS
        random.seed(42)
        tickers = DEMO_TICKERS.copy()
        random.shuffle(tickers)
        gainers = [
            {'ticker': t, 'change_pct': round(random.uniform(2, 7), 2), 'price': random.randint(10000, 100000)}
            for t in tickers[:n]
        ]
        losers = [
            {'ticker': t, 'change_pct': round(random.uniform(-7, -2), 2), 'price': random.randint(10000, 100000)}
            for t in tickers[n:n*2]
        ]
        return {'gainers': gainers, 'losers': losers}

    try:
        from vnstock import Vnstock
        vn = Vnstock()
        df = vn.stock(symbol='ACB', source='VCI').trading.price_board(
            symbols_list=get_stock_list()[:100]
        )
        if df is not None and not df.empty:
            # Normalize
            for change_col in ['change_pct', 'changePct', 'pct_change', 'change']:
                if change_col in df.columns:
                    df = df.rename(columns={change_col: 'change_pct'})
                    break
            df = df.sort_values('change_pct', ascending=False)
            gainers = df.head(n)[['ticker', 'change_pct']].to_dict('records')
            losers = df.tail(n)[['ticker', 'change_pct']].to_dict('records')
            return {'gainers': gainers, 'losers': losers}
    except Exception as e:
        logger.warning(f"get_top_movers failed: {e}")

    return {'gainers': [], 'losers': []}


class DataFetcher:
    """Convenience class wrapping fetch functions with caching."""

    def __init__(self, demo: bool = False, cache_ttl_seconds: int = 300):
        self.demo = demo
        self.cache_ttl = cache_ttl_seconds
        self._cache: dict = {}

    def _cache_key(self, ticker: str, start: str, end: str) -> str:
        return f"{ticker}_{start}_{end}"

    def _is_cache_valid(self, key: str) -> bool:
        if key not in self._cache:
            return False
        ts, _ = self._cache[key]
        return (time.time() - ts) < self.cache_ttl

    def get_ohlcv(self, ticker: str, start: Optional[str] = None, end: Optional[str] = None) -> pd.DataFrame:
        if end is None:
            end = datetime.now().strftime('%Y-%m-%d')
        if start is None:
            start = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        key = self._cache_key(ticker, start, end)
        if self._is_cache_valid(key):
            return self._cache[key][1].copy()
        df = get_ohlcv(ticker, start, end, demo=self.demo)
        self._cache[key] = (time.time(), df)
        return df.copy()

    def get_stock_list(self, exchange: str = 'all') -> List[str]:
        return get_stock_list(exchange=exchange, demo=self.demo)

    def get_top_movers(self, n: int = 10) -> dict:
        return get_top_movers(n=n, demo=self.demo)
