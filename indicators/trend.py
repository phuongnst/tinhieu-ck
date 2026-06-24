"""
Trend indicators: SMA, EMA, HMA, WMA, VWAP, Ichimoku, SuperTrend, ADX, Parabolic SAR.
"""

import numpy as np
import pandas as pd


def _ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def _wma(series: pd.Series, period: int) -> pd.Series:
    weights = np.arange(1, period + 1, dtype=float)
    return series.rolling(period).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)


def _hma(series: pd.Series, period: int) -> pd.Series:
    half = max(int(period / 2), 1)
    sqrt_p = max(int(np.sqrt(period)), 1)
    raw = 2 * _wma(series, half) - _wma(series, period)
    return _wma(raw, sqrt_p)


def _vwap(df: pd.DataFrame) -> pd.Series:
    typical = (df['high'] + df['low'] + df['close']) / 3
    cum_vol = df['volume'].cumsum()
    return (typical * df['volume']).cumsum() / cum_vol.replace(0, np.nan)


def _ichimoku(df: pd.DataFrame):
    h, l = df['high'], df['low']
    tenkan = (h.rolling(9).max() + l.rolling(9).min()) / 2
    kijun = (h.rolling(26).max() + l.rolling(26).min()) / 2
    senkou_a = ((tenkan + kijun) / 2).shift(26)
    senkou_b = ((h.rolling(52).max() + l.rolling(52).min()) / 2).shift(26)
    chikou = df['close'].shift(-26)
    return tenkan, kijun, senkou_a, senkou_b, chikou


def _parabolic_sar(df: pd.DataFrame, af_start: float = 0.02, af_max: float = 0.2) -> pd.Series:
    high, low = df['high'].values, df['low'].values
    n = len(high)
    sar = np.zeros(n)
    trend, ep, af = 1, low[0], af_start
    sar[0] = high[0]
    for i in range(1, n):
        if trend == 1:
            sar[i] = min(sar[i-1] + af * (ep - sar[i-1]), low[i-1], low[max(i-2, 0)])
            if low[i] < sar[i]:
                trend, sar[i], ep, af = -1, ep, low[i], af_start
            elif high[i] > ep:
                ep, af = high[i], min(af + af_start, af_max)
        else:
            sar[i] = max(sar[i-1] + af * (ep - sar[i-1]), high[i-1], high[max(i-2, 0)])
            if high[i] > sar[i]:
                trend, sar[i], ep, af = 1, ep, high[i], af_start
            elif low[i] < ep:
                ep, af = low[i], min(af + af_start, af_max)
    return pd.Series(sar, index=df.index)


def _adx(df: pd.DataFrame, period: int = 14):
    h, l, c = df['high'], df['low'], df['close']
    plus_dm = h.diff().clip(lower=0)
    minus_dm = (-l.diff()).clip(lower=0)
    plus_dm[plus_dm < minus_dm] = 0
    minus_dm[minus_dm <= plus_dm] = 0
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(span=period, adjust=False).mean()
    plus_di = 100 * plus_dm.ewm(span=period, adjust=False).mean() / atr.replace(0, np.nan)
    minus_di = 100 * minus_dm.ewm(span=period, adjust=False).mean() / atr.replace(0, np.nan)
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    return dx.ewm(span=period, adjust=False).mean(), plus_di, minus_di


def _supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0):
    hl2 = (df['high'] + df['low']) / 2
    tr = pd.concat([
        df['high'] - df['low'],
        (df['high'] - df['close'].shift()).abs(),
        (df['low'] - df['close'].shift()).abs(),
    ], axis=1).max(axis=1)
    atr = tr.ewm(span=period, adjust=False).mean()
    upper = hl2 + multiplier * atr
    lower = hl2 - multiplier * atr
    close = df['close'].values
    st = np.zeros(len(close))
    direction = np.zeros(len(close), dtype=int)
    for i in range(len(close)):
        if i == 0:
            st[i] = upper.iloc[i]
            direction[i] = -1
            continue
        ub, lb = upper.iloc[i], lower.iloc[i]
        if direction[i-1] == 1:
            st[i] = max(lb, st[i-1]) if close[i-1] > st[i-1] else lb
            direction[i] = 1 if close[i] > st[i] else -1
            if direction[i] == -1:
                st[i] = ub
        else:
            st[i] = min(ub, st[i-1]) if close[i-1] < st[i-1] else ub
            direction[i] = -1 if close[i] < st[i] else 1
            if direction[i] == 1:
                st[i] = lb
    return pd.Series(st, index=df.index), pd.Series(direction, index=df.index)


def add_trend_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add all trend indicators to OHLCV DataFrame."""
    c = df['close']
    df['SMA_20'] = c.rolling(20).mean()
    df['SMA_50'] = c.rolling(50).mean()
    df['SMA_200'] = c.rolling(200).mean()
    df['EMA_9'] = _ema(c, 9)
    df['EMA_21'] = _ema(c, 21)
    df['EMA_55'] = _ema(c, 55)
    df['WMA_20'] = _wma(c, 20)
    df['HMA_20'] = _hma(c, 20)
    df['VWAP'] = _vwap(df)
    tenkan, kijun, sa, sb, chikou = _ichimoku(df)
    df['ICH_tenkan'] = tenkan
    df['ICH_kijun'] = kijun
    df['ICH_senkou_a'] = sa
    df['ICH_senkou_b'] = sb
    df['ICH_chikou'] = chikou
    df['PSAR'] = _parabolic_sar(df)
    adx, di_plus, di_minus = _adx(df)
    df['ADX'] = adx
    df['DI_plus'] = di_plus
    df['DI_minus'] = di_minus
    st, st_dir = _supertrend(df)
    df['SuperTrend'] = st
    df['SuperTrend_dir'] = st_dir
    return df
