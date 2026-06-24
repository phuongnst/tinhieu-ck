"""
Feature engineering: convert OHLCV + indicators into ML-ready feature matrix.
"""

import numpy as np
import pandas as pd


def create_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create ML feature matrix from indicator-enriched OHLCV DataFrame.
    Returns cleaned feature DataFrame (no NaN rows, no inf).
    """
    feat = pd.DataFrame(index=df.index)
    c = df['close']

    # Price distance from moving averages (normalized)
    for ma in ['SMA_20', 'SMA_50', 'SMA_200', 'EMA_9', 'EMA_21', 'EMA_55', 'VWAP', 'VWAP_20']:
        if ma in df.columns:
            feat[f'dist_{ma}'] = (c - df[ma]) / df[ma].replace(0, np.nan)

    # Raw indicator values
    for col in [
        'RSI_14', 'RSI_7', 'Stoch_K', 'Stoch_D',
        'MACD', 'MACD_signal', 'MACD_hist',
        'CCI_20', 'Williams_R', 'ROC_10', 'MFI_14', 'Ultimate_Osc', 'Awesome_Osc',
        'BB_pct', 'BB_width', 'ATR_14', 'HV_20',
        'ADX', 'DI_plus', 'DI_minus', 'SuperTrend_dir',
        'CMF_20', 'VROC_14', 'Vol_ratio', 'OBV', 'Force_Index_13', 'EMV_14',
    ]:
        if col in df.columns:
            feat[col] = df[col]

    # Candlestick patterns (0/1)
    for col in [c for c in df.columns if c.startswith('Pat_')]:
        feat[col] = df[col]

    # Lagged returns
    for lag in [1, 2, 3, 5, 10, 20]:
        feat[f'ret_{lag}d'] = c.pct_change(lag)

    # Volume features
    if 'Vol_ratio' in df.columns:
        feat['vol_surge'] = (df['Vol_ratio'] > 2).astype(int)
        feat['vol_dry'] = (df['Vol_ratio'] < 0.5).astype(int)

    # Price position within recent ranges
    feat['pos_20d'] = (c - df['low'].rolling(20).min()) / (
        df['high'].rolling(20).max() - df['low'].rolling(20).min()).replace(0, np.nan)
    feat['pos_52w'] = (c - df['low'].rolling(252).min()) / (
        df['high'].rolling(252).max() - df['low'].rolling(252).min()).replace(0, np.nan)

    # Consecutive up/down days
    daily_ret = c.pct_change()
    up = (daily_ret > 0).astype(int)
    grp_up = (up != up.shift()).cumsum()
    feat['consec_up'] = up * up.groupby(grp_up).cumcount().add(1)
    grp_dn = ((1 - up) != (1 - up).shift()).cumsum()
    feat['consec_down'] = (1 - up) * (1 - up).groupby(grp_dn).cumcount().add(1)

    # Ichimoku features
    if 'ICH_tenkan' in df.columns:
        feat['ich_tk_diff'] = (df['ICH_tenkan'] - df['ICH_kijun']) / c.replace(0, np.nan)
        feat['ich_above_cloud'] = ((c > df['ICH_senkou_a']) & (c > df['ICH_senkou_b'])).astype(int)
        feat['ich_below_cloud'] = ((c < df['ICH_senkou_a']) & (c < df['ICH_senkou_b'])).astype(int)

    # MACD momentum
    if 'MACD_hist' in df.columns:
        feat['macd_increasing'] = (df['MACD_hist'] > df['MACD_hist'].shift(1)).astype(int)
        feat['macd_cross_up'] = ((df['MACD_hist'] > 0) & (df['MACD_hist'].shift(1) <= 0)).astype(int)
        feat['macd_cross_dn'] = ((df['MACD_hist'] < 0) & (df['MACD_hist'].shift(1) >= 0)).astype(int)

    # RSI divergence proxy
    if 'RSI_14' in df.columns:
        pr = (c > c.shift(5)).astype(int)
        rr = (df['RSI_14'] > df['RSI_14'].shift(5)).astype(int)
        feat['rsi_bull_div'] = ((pr == 0) & (rr == 1)).astype(int)
        feat['rsi_bear_div'] = ((pr == 1) & (rr == 0)).astype(int)

    # MA cross signals
    if 'SMA_50' in df.columns and 'SMA_200' in df.columns:
        feat['golden_cross'] = ((df['SMA_50'] > df['SMA_200']) & (df['SMA_50'].shift(1) <= df['SMA_200'].shift(1))).astype(int)
        feat['death_cross'] = ((df['SMA_50'] < df['SMA_200']) & (df['SMA_50'].shift(1) >= df['SMA_200'].shift(1))).astype(int)
        feat['above_sma200'] = (c > df['SMA_200']).astype(int)

    # Normalized ATR (volatility context)
    if 'ATR_14' in df.columns:
        feat['atr_pct'] = df['ATR_14'] / c.replace(0, np.nan)

    # Bollinger squeeze (narrow bands)
    if 'BB_width' in df.columns:
        feat['bb_squeeze'] = (df['BB_width'] < df['BB_width'].rolling(20).quantile(0.2)).astype(int)

    feat = feat.replace([np.inf, -np.inf], np.nan).dropna()
    return feat


def create_labels(df: pd.DataFrame, horizon: int = 5, gain_pct: float = 0.02) -> pd.Series:
    """
    Binary label: 1 if close rises >= gain_pct% in `horizon` trading days, else 0.
    """
    future_ret = df['close'].shift(-horizon) / df['close'] - 1
    return (future_ret >= gain_pct).astype(int).rename('label')
