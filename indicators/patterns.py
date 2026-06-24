"""
Candlestick pattern detection using pure pandas (no TA-Lib dependency).
"""

import numpy as np
import pandas as pd


def detect_candlestick_patterns(df: pd.DataFrame) -> pd.DataFrame:
    """Detect common candlestick patterns and add boolean (0/1) columns."""
    o, h, l, c = df['open'], df['high'], df['low'], df['close']
    body = (c - o).abs()
    upper_wick = h - pd.concat([o, c], axis=1).max(axis=1)
    lower_wick = pd.concat([o, c], axis=1).min(axis=1) - l
    full_range = (h - l).replace(0, np.nan)
    avg_body = body.rolling(10).mean().replace(0, np.nan)

    df['Pat_Doji'] = (body < 0.1 * full_range).astype(int)

    df['Pat_Hammer'] = (
        (lower_wick > 2 * body) & (upper_wick < 0.3 * body.replace(0, 0.001)) &
        (body > 0) & (c > o)
    ).astype(int)

    df['Pat_Hanging_Man'] = (
        (lower_wick > 2 * body) & (upper_wick < 0.3 * body.replace(0, 0.001)) &
        (body > 0) & (c < o)
    ).astype(int)

    df['Pat_Shooting_Star'] = (
        (upper_wick > 2 * body) & (lower_wick < 0.3 * body.replace(0, 0.001)) & (body > 0)
    ).astype(int)

    df['Pat_Inverted_Hammer'] = (
        (upper_wick > 2 * body) & (lower_wick < 0.3 * body.replace(0, 0.001)) &
        (body > 0) & (c > o)
    ).astype(int)

    df['Pat_Bull_Engulfing'] = (
        (o.shift(1) > c.shift(1)) & (c > o) &
        (o <= c.shift(1)) & (c >= o.shift(1))
    ).astype(int)

    df['Pat_Bear_Engulfing'] = (
        (c.shift(1) > o.shift(1)) & (o > c) &
        (o >= c.shift(1)) & (c <= o.shift(1))
    ).astype(int)

    df['Pat_Morning_Star'] = (
        (c.shift(2) < o.shift(2)) &
        (body.shift(1) < 0.3 * avg_body) &
        (c > o) &
        (c > (o.shift(2) + c.shift(2)) / 2)
    ).astype(int)

    df['Pat_Evening_Star'] = (
        (c.shift(2) > o.shift(2)) &
        (body.shift(1) < 0.3 * avg_body) &
        (c < o) &
        (c < (o.shift(2) + c.shift(2)) / 2)
    ).astype(int)

    df['Pat_Three_White_Soldiers'] = (
        (c > o) & (c.shift(1) > o.shift(1)) & (c.shift(2) > o.shift(2)) &
        (c > c.shift(1)) & (c.shift(1) > c.shift(2)) &
        (o > o.shift(1)) & (o.shift(1) > o.shift(2))
    ).astype(int)

    df['Pat_Three_Black_Crows'] = (
        (c < o) & (c.shift(1) < o.shift(1)) & (c.shift(2) < o.shift(2)) &
        (c < c.shift(1)) & (c.shift(1) < c.shift(2))
    ).astype(int)

    df['Pat_Pin_Bar'] = (
        ((lower_wick > 3 * body) | (upper_wick > 3 * body)) & (body > 0)
    ).astype(int)

    df['Pat_Marubozu_Bull'] = (
        (body > 0.9 * full_range) & (c > o)
    ).astype(int)

    df['Pat_Marubozu_Bear'] = (
        (body > 0.9 * full_range) & (c < o)
    ).astype(int)

    df['Pat_Spinning_Top'] = (
        (body < 0.3 * full_range) & (upper_wick > body) & (lower_wick > body)
    ).astype(int)

    return df
