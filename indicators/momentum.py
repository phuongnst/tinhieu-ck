"""
Momentum indicators: RSI, MACD, Stochastic, CCI, Williams %R, ROC, MFI, etc.
"""

import numpy as np
import pandas as pd


def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(com=period - 1, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(com=period - 1, adjust=False).mean()
    return 100 - (100 / (1 + gain / loss.replace(0, np.nan)))


def _stochastic(df: pd.DataFrame, k: int = 14, d: int = 3):
    low_min = df['low'].rolling(k).min()
    high_max = df['high'].rolling(k).max()
    stoch_k = 100 * (df['close'] - low_min) / (high_max - low_min).replace(0, np.nan)
    return stoch_k, stoch_k.rolling(d).mean()


def _macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    line = close.ewm(span=fast, adjust=False).mean() - close.ewm(span=slow, adjust=False).mean()
    sig = line.ewm(span=signal, adjust=False).mean()
    return line, sig, line - sig


def _cci(df: pd.DataFrame, period: int = 20) -> pd.Series:
    tp = (df['high'] + df['low'] + df['close']) / 3
    ma = tp.rolling(period).mean()
    mad = tp.rolling(period).apply(lambda x: np.mean(np.abs(x - np.mean(x))), raw=True)
    return (tp - ma) / (0.015 * mad.replace(0, np.nan))


def _williams_r(df: pd.DataFrame, period: int = 14) -> pd.Series:
    hh = df['high'].rolling(period).max()
    ll = df['low'].rolling(period).min()
    return -100 * (hh - df['close']) / (hh - ll).replace(0, np.nan)


def _mfi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    tp = (df['high'] + df['low'] + df['close']) / 3
    raw = tp * df['volume']
    pos = raw.where(tp > tp.shift(1), 0)
    neg = raw.where(tp < tp.shift(1), 0)
    mfr = pos.rolling(period).sum() / neg.rolling(period).sum().replace(0, np.nan)
    return 100 - (100 / (1 + mfr))


def _ultimate_oscillator(df: pd.DataFrame) -> pd.Series:
    bp = df['close'] - pd.concat([df['low'], df['close'].shift()], axis=1).min(axis=1)
    tr = pd.concat([
        df['high'] - df['low'],
        (df['high'] - df['close'].shift()).abs(),
        (df['low'] - df['close'].shift()).abs(),
    ], axis=1).max(axis=1)
    avg = lambda p: bp.rolling(p).sum() / tr.rolling(p).sum().replace(0, np.nan)
    return 100 * (4 * avg(7) + 2 * avg(14) + avg(28)) / 7


def add_momentum_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add all momentum indicators to OHLCV DataFrame."""
    c = df['close']
    df['RSI_14'] = _rsi(c, 14)
    df['RSI_7'] = _rsi(c, 7)
    df['Stoch_K'], df['Stoch_D'] = _stochastic(df)
    df['MACD'], df['MACD_signal'], df['MACD_hist'] = _macd(c)
    df['CCI_20'] = _cci(df)
    df['Williams_R'] = _williams_r(df)
    df['ROC_10'] = 100 * (c - c.shift(10)) / c.shift(10).replace(0, np.nan)
    df['MFI_14'] = _mfi(df)
    df['Ultimate_Osc'] = _ultimate_oscillator(df)
    mid = (df['high'] + df['low']) / 2
    df['Awesome_Osc'] = mid.rolling(5).mean() - mid.rolling(34).mean()
    return df
