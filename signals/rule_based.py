"""
Rule-based scoring engine: 25+ classical technical analysis rules.
Returns score in [-100, 100]. Positive = bullish, negative = bearish.
"""

import numpy as np
import pandas as pd


def _safe(val, default=np.nan):
    try:
        v = float(val)
        return v if np.isfinite(v) else default
    except Exception:
        return default


class RuleBasedScorer:
    """Score latest bar of a DataFrame using technical rules."""

    def score(self, df: pd.DataFrame) -> float:
        if df is None or len(df) < 30:
            return 0.0
        r = df.iloc[-1]
        p = df.iloc[-2] if len(df) > 1 else r
        s = 0.0
        close = _safe(r.get('close'))
        open_ = _safe(r.get('open'))

        # RSI
        rsi = _safe(r.get('RSI_14'))
        if not np.isnan(rsi):
            if rsi < 25: s += 15
            elif rsi < 35: s += 8
            elif rsi > 75: s -= 15
            elif rsi > 65: s -= 8

        rsi7 = _safe(r.get('RSI_7'))
        if not np.isnan(rsi7):
            if rsi7 < 20: s += 8
            elif rsi7 > 80: s -= 8

        # MACD crossover
        macd = _safe(r.get('MACD'))
        msig = _safe(r.get('MACD_signal'))
        mhist = _safe(r.get('MACD_hist'))
        p_macd = _safe(p.get('MACD'))
        p_msig = _safe(p.get('MACD_signal'))
        p_hist = _safe(p.get('MACD_hist'))
        if not (np.isnan(macd) or np.isnan(msig)):
            if macd > msig and not np.isnan(p_macd) and p_macd <= p_msig:
                s += 18  # bullish crossover
            elif macd < msig and not np.isnan(p_macd) and p_macd >= p_msig:
                s -= 18  # bearish crossover
            elif macd > msig:
                s += 5
            else:
                s -= 5
        if not (np.isnan(mhist) or np.isnan(p_hist)):
            if mhist > 0 and mhist > p_hist: s += 5
            elif mhist < 0 and mhist < p_hist: s -= 5

        # Moving Averages
        sma20 = _safe(r.get('SMA_20'))
        sma50 = _safe(r.get('SMA_50'))
        sma200 = _safe(r.get('SMA_200'))
        if not (np.isnan(close) or np.isnan(sma200)):
            s += 6 if close > sma200 else -6
        if not (np.isnan(sma20) or np.isnan(sma50)):
            s += 4 if sma20 > sma50 else -4

        # Golden/Death cross
        p_sma50 = _safe(p.get('SMA_50'))
        p_sma200 = _safe(p.get('SMA_200'))
        if not any(np.isnan(x) for x in [sma50, sma200, p_sma50, p_sma200]):
            if sma50 > sma200 and p_sma50 <= p_sma200: s += 22
            elif sma50 < sma200 and p_sma50 >= p_sma200: s -= 22

        # Bollinger Bands
        bb_pct = _safe(r.get('BB_pct'))
        bb_w = _safe(r.get('BB_width'))
        p_bb_w = _safe(p.get('BB_width'))
        if not np.isnan(bb_pct):
            if bb_pct < 0.05: s += 10
            elif bb_pct > 0.95: s -= 10
        if not (np.isnan(bb_w) or np.isnan(p_bb_w)) and p_bb_w > 0:
            if bb_w > p_bb_w * 1.2 and not np.isnan(bb_pct) and bb_pct > 0.5:
                s += 8  # upward breakout from squeeze

        # ADX trend strength
        adx = _safe(r.get('ADX'))
        di_plus = _safe(r.get('DI_plus'))
        di_minus = _safe(r.get('DI_minus'))
        if not any(np.isnan(x) for x in [adx, di_plus, di_minus]):
            if adx > 25:
                s += 12 if di_plus > di_minus else -12
            elif adx < 20:
                s -= 3

        # SuperTrend
        st_dir = _safe(r.get('SuperTrend_dir'))
        if not np.isnan(st_dir):
            s += 10 if st_dir == 1 else -10

        # Parabolic SAR
        psar = _safe(r.get('PSAR'))
        if not (np.isnan(psar) or np.isnan(close)):
            s += 5 if close > psar else -5

        # Ichimoku
        ich_a = _safe(r.get('ICH_senkou_a'))
        ich_b = _safe(r.get('ICH_senkou_b'))
        ich_tk = _safe(r.get('ICH_tenkan'))
        ich_kj = _safe(r.get('ICH_kijun'))
        if not any(np.isnan(x) for x in [ich_a, ich_b, close]):
            cloud_top, cloud_bot = max(ich_a, ich_b), min(ich_a, ich_b)
            if close > cloud_top: s += 10
            elif close < cloud_bot: s -= 10
        if not (np.isnan(ich_tk) or np.isnan(ich_kj)):
            s += 4 if ich_tk > ich_kj else -4

        # Volume surge on candle direction
        vol_ratio = _safe(r.get('Vol_ratio'))
        if not (np.isnan(vol_ratio) or np.isnan(close) or np.isnan(open_)):
            if vol_ratio > 2:
                s += 10 if close > open_ else -10
            elif vol_ratio > 1.5:
                s += 4 if close > open_ else -4

        # CMF
        cmf = _safe(r.get('CMF_20'))
        if not np.isnan(cmf):
            if cmf > 0.15: s += 6
            elif cmf < -0.15: s -= 6

        # MFI
        mfi = _safe(r.get('MFI_14'))
        if not np.isnan(mfi):
            if mfi < 20: s += 8
            elif mfi > 80: s -= 8

        # Stochastic
        sk = _safe(r.get('Stoch_K'))
        sd = _safe(r.get('Stoch_D'))
        p_sk = _safe(p.get('Stoch_K'))
        p_sd = _safe(p.get('Stoch_D'))
        if not (np.isnan(sk) or np.isnan(sd)):
            if sk < 20 and sd < 20: s += 8
            elif sk > 80 and sd > 80: s -= 8
            if not (np.isnan(p_sk) or np.isnan(p_sd)):
                if sk > sd and p_sk <= p_sd: s += 6
                elif sk < sd and p_sk >= p_sd: s -= 6

        # CCI
        cci = _safe(r.get('CCI_20'))
        if not np.isnan(cci):
            if cci < -150: s += 8
            elif cci < -100: s += 4
            elif cci > 150: s -= 8
            elif cci > 100: s -= 4

        # OBV trend
        obv = _safe(r.get('OBV'))
        p_obv = _safe(p.get('OBV'))
        if not (np.isnan(obv) or np.isnan(p_obv)):
            s += 4 if obv > p_obv else -4

        # Candlestick patterns
        bull_pats = ['Pat_Hammer', 'Pat_Inverted_Hammer', 'Pat_Bull_Engulfing',
                     'Pat_Morning_Star', 'Pat_Three_White_Soldiers', 'Pat_Pin_Bar', 'Pat_Marubozu_Bull']
        bear_pats = ['Pat_Hanging_Man', 'Pat_Shooting_Star', 'Pat_Bear_Engulfing',
                     'Pat_Evening_Star', 'Pat_Three_Black_Crows', 'Pat_Marubozu_Bear']
        for pat in bull_pats:
            if _safe(r.get(pat), 0) == 1: s += 8
        for pat in bear_pats:
            if _safe(r.get(pat), 0) == 1: s -= 8

        return float(np.clip(s, -100, 100))

    def score_normalized(self, df: pd.DataFrame) -> float:
        """Return score normalized to [0, 1]."""
        return (self.score(df) + 100) / 200
