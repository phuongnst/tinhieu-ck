"""
Sentiment analyzer for Vietnamese financial news.
Uses keyword-based scoring + optional transformer model (PhoBERT/multilingual).
Falls back gracefully if transformers not installed.
"""

import logging
import re
from typing import Dict, List

logger = logging.getLogger(__name__)

# Vietnamese financial sentiment keywords
BULLISH_KEYWORDS = [
    # Vietnamese
    'tăng', 'mua', 'tăng trưởng', 'lợi nhuận tăng', 'vượt kế hoạch', 'kết quả tích cực',
    'đột phá', 'hồi phục', 'tiềm năng', 'cơ hội', 'lạc quan', 'khởi sắc', 'bứt phá',
    'kỷ lục', 'ổn định', 'bền vững', 'triển vọng tích cực', 'tăng vốn', 'chia cổ tức',
    'mở rộng', 'hợp đồng lớn', 'xuất khẩu tăng', 'doanh thu tăng', 'thị phần tăng',
    # English (may appear in reports)
    'growth', 'profit', 'beat', 'upgrade', 'buy', 'outperform', 'bullish', 'rally',
]

BEARISH_KEYWORDS = [
    # Vietnamese
    'giảm', 'bán', 'lỗ', 'thua lỗ', 'sụt giảm', 'khó khăn', 'rủi ro', 'bi quan',
    'lo ngại', 'áp lực', 'nợ xấu', 'phá sản', 'đình trệ', 'suy giảm', 'cắt giảm',
    'vi phạm', 'điều tra', 'phạt', 'thoái vốn', 'thu hẹp', 'đình chỉ', 'kiện tụng',
    'lãi suất tăng', 'lạm phát', 'tỷ giá', 'đáo hạn nợ', 'margin call',
    # English
    'loss', 'decline', 'downgrade', 'sell', 'underperform', 'bearish', 'crash', 'fraud',
]

NEUTRAL_INTENSIFIERS = ['mạnh', 'mạnh mẽ', 'đáng kể', 'significantly', 'sharply', 'strongly']


def _keyword_score(text: str) -> float:
    """Simple keyword-based sentiment score in [-1, 1]."""
    text_lower = text.lower()
    bull = sum(1 for kw in BULLISH_KEYWORDS if kw in text_lower)
    bear = sum(1 for kw in BEARISH_KEYWORDS if kw in text_lower)
    total = bull + bear
    if total == 0:
        return 0.0
    return (bull - bear) / total


class SentimentAnalyzer:
    """
    Multi-layer sentiment analyzer for Vietnamese financial text.
    Layer 1: Fast keyword scoring (always available).
    Layer 2: Optional multilingual transformer (if transformers installed).
    """

    def __init__(self, use_transformer: bool = False):
        self.use_transformer = use_transformer
        self._pipe = None
        if use_transformer:
            self._load_transformer()

    def _load_transformer(self):
        try:
            from transformers import pipeline
            # Use multilingual sentiment model as default; can swap for PhoBERT
            self._pipe = pipeline(
                'text-classification',
                model='nlptown/bert-base-multilingual-uncased-sentiment',
                truncation=True,
                max_length=512,
            )
            logger.info("Loaded transformer sentiment model")
        except ImportError:
            logger.warning("transformers not installed, falling back to keyword scoring")
            self._pipe = None
        except Exception as e:
            logger.warning(f"Failed to load transformer: {e}")
            self._pipe = None

    def _transformer_score(self, text: str) -> float:
        """Return [-1, 1] sentiment from transformer (1-5 star → -1 to 1)."""
        try:
            result = self._pipe(text[:512])[0]
            label = result['label']  # e.g., '4 stars'
            stars = int(re.search(r'\d', label).group())
            return (stars - 3) / 2  # 1→-1, 3→0, 5→1
        except Exception:
            return 0.0

    def score_text(self, text: str) -> float:
        """Score a single text, return [-1, 1]."""
        kw = _keyword_score(text)
        if self._pipe is not None:
            tf = self._transformer_score(text)
            return 0.4 * kw + 0.6 * tf
        return kw

    def score_articles(self, articles: List[Dict]) -> float:
        """
        Score a list of news articles for a ticker.
        Returns aggregate sentiment [-1, 1].
        """
        if not articles:
            return 0.0
        scores = [self.score_text(a.get('title', '') + ' ' + a.get('content', '')) for a in articles]
        # Recency-weighted (more recent = higher weight)
        weights = [1.0 + 0.1 * i for i in range(len(scores) - 1, -1, -1)]
        total_w = sum(weights)
        return sum(s * w for s, w in zip(scores, weights)) / total_w

    def get_ticker_sentiment(self, ticker: str, news_fn=None) -> dict:
        """
        Get sentiment score for a ticker.
        news_fn: callable returning list of article dicts (optional override).
        """
        if news_fn is None:
            try:
                from sentiment.scraper import get_news_for_ticker
                news_fn = get_news_for_ticker
            except Exception:
                return {'ticker': ticker, 'score': 0.0, 'n_articles': 0, 'label': 'neutral'}

        try:
            articles = news_fn(ticker)
        except Exception as e:
            logger.warning(f"News fetch failed for {ticker}: {e}")
            articles = []

        score = self.score_articles(articles)
        label = 'bullish' if score > 0.15 else ('bearish' if score < -0.15 else 'neutral')
        return {
            'ticker': ticker,
            'score': round(score, 4),
            'n_articles': len(articles),
            'label': label,
        }
