# Tín Hiệu Chứng Khoán Việt Nam

Hệ thống tự động phân tích và thông báo tín hiệu mua/bán cổ phiếu Việt Nam với độ chính xác cao, kết hợp phân tích kỹ thuật truyền thống + AI/ML ensemble + phân tích cảm xúc tin tức.

## Tính năng

- **55+ chỉ báo kỹ thuật**: MA, EMA, HMA, WMA, VWAP, Ichimoku, SuperTrend, ADX, Parabolic SAR, RSI, MACD, Stochastic, Bollinger Bands, ATR, OBV, CMF...
- **15+ mẫu nến**: Hammer, Doji, Engulfing, Morning/Evening Star, Three Soldiers/Crows...
- **AI Ensemble**: XGBoost + LightGBM + Random Forest → LogisticRegression stacking (AUC-optimized)
- **Sentiment Analysis**: Phân tích tin tức CafeF/VNExpress với keyword scoring + optional transformer
- **Tín hiệu cuối**: `40% rule-based + 60% ML probability`
- **Thông báo Telegram**: Top 10 BUY + Top 5 SELL mỗi phiên
- **Backtesting**: Win rate, Sharpe ratio, Max drawdown, Equity curve
- **Scheduler**: Tự động chạy 09:30, 11:00, 13:00, 14:30 (giờ VN)

## Cài đặt

```bash
pip install -r requirements.txt
cp .env.example .env
# Điền TELEGRAM_TOKEN và TELEGRAM_CHAT_ID vào .env
```

## Sử dụng

```bash
# Quét tín hiệu ngay (dữ liệu thật từ vnstock)
python main.py

# Demo với dữ liệu giả — không cần API, không cần internet
python main.py --demo

# Backtest chiến lược trên dữ liệu lịch sử
python main.py --backtest --demo

# Chạy tự động theo lịch (09:30, 11:00, 13:00, 14:30 giờ VN, Mon-Fri)
python main.py --schedule

# Quét + không gửi Telegram
python main.py --demo --no-notify
```

## Kiến trúc

```
tinhieu-ck/
├── main.py                      # Entry point
├── config.py                    # Cấu hình hệ thống
├── data/
│   └── fetcher.py               # vnstock v3/v2 + CafeF + synthetic fallback
├── indicators/
│   ├── trend.py                 # SMA/EMA/HMA/VWAP/Ichimoku/SuperTrend/ADX/PSAR
│   ├── momentum.py              # RSI/MACD/Stochastic/CCI/MFI/Williams%R/AO
│   ├── volatility.py            # Bollinger/ATR/Keltner/Donchian/HV
│   ├── volume.py                # OBV/CMF/AD Line/Force Index/VROC/EMV
│   └── patterns.py              # 15+ mẫu nến (pure pandas)
├── models/
│   ├── ensemble.py              # XGBoost + LightGBM + RF → LogReg stacking
│   └── feature_engineering.py  # 50+ features từ indicators
├── signals/
│   ├── rule_based.py            # 25+ quy tắc kỹ thuật → score [-100, 100]
│   ├── ml_signal.py             # ML prediction wrapper
│   └── aggregator.py           # 40% rule + 60% ML → BUY/SELL/HOLD
├── backtest/
│   └── engine.py               # Portfolio backtest với TP/SL, commission
├── sentiment/
│   ├── scraper.py              # Crawl tin CafeF/VNExpress
│   └── analyzer.py            # Keyword + transformer sentiment scoring
└── notifications/
    └── telegram_bot.py         # Gửi tín hiệu qua Telegram
```

## Bảng tín hiệu

| Score cuối | Tín hiệu |
|-----------|----------|
| > 0.65 | 🟢 MUA |
| 0.35 – 0.65 | 🟡 GIỮ |
| < 0.35 | 🔴 BÁN |

Score cuối = **40% điểm kỹ thuật** + **60% xác suất ML**

## Cài đặt Telegram

1. Chat với [@BotFather](https://t.me/BotFather) → `/newbot` → lấy token
2. Chat với [@userinfobot](https://t.me/userinfobot) → lấy chat ID
3. Điền vào `.env`

## Nguồn dữ liệu

| Nguồn | Ưu tiên | Ghi chú |
|-------|---------|---------|
| vnstock v3 (VCI) | 1 | API chính thức, miễn phí |
| vnstock v2 | 2 | Fallback |
| CafeF API | 3 | Fallback |
| Synthetic | 4 | Demo/testing only |

## Lưu ý quan trọng

> ⚠️ Tín hiệu chỉ mang tính **tham khảo**, không phải khuyến nghị đầu tư.
> Luôn quản lý rủi ro: stop loss 3%, take profit 5%.
> Backtest trên dữ liệu quá khứ không đảm bảo kết quả tương lai.
