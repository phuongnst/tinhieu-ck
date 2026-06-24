"""
Volatility indicators: Bollinger Bands, ATR, Keltner Channels, Donchian, Chaikin Vol.
"""

import numpy as np
import pandas as pd


def _atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    tr = pd.concat([
        df['high'] - df['low'],
        (df['high'] - df['close'].shift()).abs(),
        (df['low'] - df['close'].shift()).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(span=period, adjust=False).mean()


def add_volatility_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add volatility indicators to OHLCV DataFrame."""
    c = df['close']

    # Bollinger Bands
    bb_mid = c.rolling(20).mean()
    bb_std = c.rolling(20).std()
    df['BB_upper'] = bb_mid + 2 * bb_std
    df['BB_middle'] = bb_mid
    df['BB_lower'] = bb_mid - 2 * bb_std
    bb_range = (df['BB_upper'] - df['BB_lower']).replace(0, np.nan)
    df['BB_width'] = bb_range / bb_mid.replace(0, np.nan)
    df['BB_pct'] = (c - df['BB_lower']) / bb_range

    # ATR
    df['ATR_14'] = _atr(df, 14)

    # Keltner Channels
    ema20 = c.ewm(span=20, adjust=False).mean()
    df['KC_upper'] = ema20 + 2 * df['ATR_14']
    df['KC_lower'] = ema20 - 2 * df['ATR_14']

    # Donchian Channels
    df['DC_upper'] = df['high'].rolling(20).max()
    df['DC_lower'] = df['low'].rolling(20).min()
    df['DC_mid'] = (df['DC_upper'] + df['DC_lower']) / 2

    # Chaikin Volatility
    hl_ema = (df['high'] - df['low']).ewm(span=10, adjust=False).mean()
    df['Chaikin_Vol'] = 100 * (hl_ema - hl_ema.shift(10)) / hl_ema.shift(10).replace(0, np.nan)

    # Historical Volatility (20-day annualized)
    df['HV_20'] = c.pct_change().rolling(20).std() * np.sqrt(252) * 100

    return df
