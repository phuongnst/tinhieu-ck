"""
Volume indicators: OBV, VWAP, CMF, A/D Line, Force Index, VROC, Volume Profile.
"""

import numpy as np
import pandas as pd


def add_volume_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add volume-based indicators to OHLCV DataFrame."""
    c, h, l, v = df['close'], df['high'], df['low'], df['volume']

    # On-Balance Volume
    sign = np.sign(c.diff()).fillna(0)
    df['OBV'] = (sign * v).cumsum()

    # Rolling VWAP (20-day)
    tp = (h + l + c) / 3
    df['VWAP_20'] = (tp * v).rolling(20).sum() / v.rolling(20).sum().replace(0, np.nan)

    # Chaikin Money Flow
    mf_mult = ((c - l) - (h - c)) / (h - l).replace(0, np.nan)
    df['CMF_20'] = (mf_mult * v).rolling(20).sum() / v.rolling(20).sum().replace(0, np.nan)

    # Accumulation/Distribution Line
    df['AD_Line'] = (mf_mult * v).cumsum()

    # Force Index
    df['Force_Index'] = c.diff() * v
    df['Force_Index_13'] = df['Force_Index'].ewm(span=13, adjust=False).mean()

    # Volume Rate of Change
    df['VROC_14'] = 100 * (v - v.shift(14)) / v.shift(14).replace(0, np.nan)

    # Volume Moving Average & ratio
    df['Vol_MA_20'] = v.rolling(20).mean()
    df['Vol_ratio'] = v / df['Vol_MA_20'].replace(0, np.nan)

    # Ease of Movement
    dm = ((h + l) / 2) - ((h.shift() + l.shift()) / 2)
    br = v / (h - l).replace(0, np.nan)
    df['EMV_14'] = (dm / br.replace(0, np.nan)).rolling(14).mean()

    return df
