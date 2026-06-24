"""
Vietnamese financial news scraper.
Sources: CafeF, VNExpress Kinh doanh, Vietstock.
"""

import logging
import re
from datetime import datetime, timedelta
from typing import List, dict as Dict
from typing import Dict

import requests

logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept-Language': 'vi-VN,vi;q=0.9',
}


def _clean_text(text: str) -> str:
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def scrape_cafef_news(ticker: str = '', limit: int = 20) -> List[Dict]:
    """Scrape news from CafeF for a specific ticker or general market news."""
    articles = []
    try:
        if ticker:
            url = f"https://cafef.vn/tim-kiem.chn?keywords={ticker}&type=2"
        else:
            url = "https://cafef.vn/thi-truong-chung-khoan.chn"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()

        # Simple regex-based extraction (avoid heavy HTML parsing dependency)
        titles = re.findall(r'<h3[^>]*class="[^"]*title[^"]*"[^>]*>(.*?)</h3>', resp.text, re.DOTALL)
        titles += re.findall(r'<a[^>]*class="[^"]*title[^"]*"[^>]*>(.*?)</a>', resp.text, re.DOTALL)

        for t in titles[:limit]:
            clean = _clean_text(t)
            if len(clean) > 10:
                articles.append({
                    'title': clean,
                    'source': 'cafef',
                    'ticker': ticker,
                    'date': datetime.now().strftime('%Y-%m-%d'),
                })
    except Exception as e:
        logger.warning(f"CafeF scrape failed for {ticker}: {e}")
    return articles


def scrape_vnexpress_finance(limit: int = 20) -> List[Dict]:
    """Scrape finance news from VNExpress."""
    articles = []
    try:
        url = "https://vnexpress.net/kinh-doanh/chung-khoan"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        titles = re.findall(r'<h3[^>]*class="[^"]*title-news[^"]*"[^>]*>(.*?)</h3>', resp.text, re.DOTALL)
        for t in titles[:limit]:
            clean = _clean_text(t)
            if len(clean) > 10:
                articles.append({
                    'title': clean,
                    'source': 'vnexpress',
                    'ticker': '',
                    'date': datetime.now().strftime('%Y-%m-%d'),
                })
    except Exception as e:
        logger.warning(f"VNExpress scrape failed: {e}")
    return articles


def get_news_for_ticker(ticker: str, limit: int = 10) -> List[Dict]:
    """Get relevant news for a specific stock ticker."""
    news = scrape_cafef_news(ticker=ticker, limit=limit)
    if len(news) < 5:
        # Try general market news and filter by ticker mention
        general = scrape_cafef_news(limit=30) + scrape_vnexpress_finance(limit=30)
        ticker_news = [a for a in general if ticker.upper() in a['title'].upper()]
        news.extend(ticker_news)
    return news[:limit]


def get_market_news(limit: int = 30) -> List[Dict]:
    """Get general Vietnamese stock market news."""
    news = scrape_cafef_news(limit=limit) + scrape_vnexpress_finance(limit=limit)
    return news[:limit]
