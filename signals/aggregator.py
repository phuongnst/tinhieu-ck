"""
Signal aggregator: combine rule-based score + ML probability → ranked BUY/SELL lists.
final_score = rule_weight * rule_norm + ml_weight * ml_prob
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import pandas as pd

from signals.rule_based import RuleBasedScorer
from signals.ml_signal import MLSignalGenerator

logger = logging.getLogger(__name__)


@dataclass
class StockSignal:
    ticker: str
    rule_score: float       # normalized [0,1]
    ml_prob: float          # [0,1]
    final_score: float      # [0,1]
    signal: str             # 'BUY' | 'SELL' | 'HOLD'
    price: float
    rsi: float
    macd_hist: float
    volume_ratio: float
    top_patterns: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'ticker': self.ticker,
            'signal': self.signal,
            'final_score': round(self.final_score, 4),
            'rule_score': round(self.rule_score, 4),
            'ml_prob': round(self.ml_prob, 4),
            'price': self.price,
            'rsi': round(self.rsi, 1) if self.rsi else None,
            'macd_hist': round(self.macd_hist, 4) if self.macd_hist else None,
            'volume_ratio': round(self.volume_ratio, 2) if self.volume_ratio else None,
            'patterns': self.top_patterns,
        }


class SignalAggregator:
    """Aggregate rule + ML signals into ranked BUY/SELL/HOLD classifications."""

    def __init__(
        self,
        rule_weight: float = 0.4,
        ml_weight: float = 0.6,
        buy_threshold: float = 0.65,
        sell_threshold: float = 0.35,
        ml_generator: Optional[MLSignalGenerator] = None,
    ):
        self.rule_weight = rule_weight
        self.ml_weight = ml_weight
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold
        self.scorer = RuleBasedScorer()
        self.ml_gen = ml_generator or MLSignalGenerator()

    def analyze(self, ticker: str, df: pd.DataFrame) -> Optional[StockSignal]:
        try:
            rule_norm = self.scorer.score_normalized(df)
            ml_prob = self.ml_gen.predict(df)
            final = self.rule_weight * rule_norm + self.ml_weight * ml_prob
            signal = 'BUY' if final >= self.buy_threshold else ('SELL' if final <= self.sell_threshold else 'HOLD')
            last = df.iloc[-1]
            patterns = [c.replace('Pat_', '') for c in df.columns if c.startswith('Pat_') and last.get(c, 0) == 1]
            return StockSignal(
                ticker=ticker,
                rule_score=rule_norm,
                ml_prob=ml_prob,
                final_score=final,
                signal=signal,
                price=float(last.get('close', 0)),
                rsi=float(last.get('RSI_14', 0) or 0),
                macd_hist=float(last.get('MACD_hist', 0) or 0),
                volume_ratio=float(last.get('Vol_ratio', 1) or 1),
                top_patterns=patterns[:3],
            )
        except Exception as e:
            logger.warning(f"Error analyzing {ticker}: {e}")
            return None

    def rank_signals(
        self,
        ticker_dfs: Dict[str, pd.DataFrame],
        top_buy: int = 10,
        top_sell: int = 5,
    ) -> dict:
        """Analyze all tickers and return ranked BUY/SELL lists."""
        all_sigs = [s for t, df in ticker_dfs.items() if (s := self.analyze(t, df)) is not None]
        buy = sorted([s for s in all_sigs if s.signal == 'BUY'], key=lambda x: x.final_score, reverse=True)[:top_buy]
        sell = sorted([s for s in all_sigs if s.signal == 'SELL'], key=lambda x: x.final_score)[:top_sell]
        logger.info(f"Ranked signals: {len(buy)} BUY, {len(sell)} SELL / {len(all_sigs)} total")
        return {'buy': buy, 'sell': sell, 'all': all_sigs}
