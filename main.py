"""
VN Stock Signal System — Main entry point.

Usage:
  python main.py              # Scan & notify via Telegram
  python main.py --demo       # Demo with synthetic data (no API needed)
  python main.py --backtest   # Run backtesting
  python main.py --schedule   # Run on market-hours schedule
  python main.py --demo --no-notify  # Demo without Telegram
"""

import argparse
import logging
import sys
from datetime import datetime

import config
from data.fetcher import DataFetcher
from indicators import add_all_indicators
from signals.aggregator import SignalAggregator
from signals.ml_signal import MLSignalGenerator
from notifications.telegram_bot import TelegramNotifier
from backtest.engine import Backtest

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(config.LOG_FILE, encoding='utf-8'),
    ],
)
logger = logging.getLogger(__name__)


def load_ticker_data(fetcher: DataFetcher) -> dict:
    """Fetch and compute indicators for all tickers."""
    tickers = fetcher.get_stock_list()
    logger.info(f"Processing {len(tickers)} tickers...")
    result = {}
    for i, ticker in enumerate(tickers):
        try:
            df = fetcher.get_ohlcv(ticker)
            if df is None or len(df) < 50:
                continue
            df = add_all_indicators(df)
            result[ticker] = df
            if (i + 1) % 50 == 0:
                logger.info(f"  {i+1}/{len(tickers)} done")
        except Exception as e:
            logger.warning(f"Failed {ticker}: {e}")
    logger.info(f"Loaded {len(result)} tickers with indicators")
    return result


def run_scan(demo: bool = False, notify: bool = True) -> dict:
    """Run full signal scan and optionally send Telegram notification."""
    logger.info(f"=== Signal scan started [demo={demo}] ===")
    fetcher = DataFetcher(demo=demo)
    ml_gen = MLSignalGenerator()

    if not ml_gen.load():
        logger.info("No saved model found, will train on available data")

    ticker_dfs = load_ticker_data(fetcher)
    if not ticker_dfs:
        logger.error("No ticker data available")
        return {}

    if not ml_gen.model.is_trained:
        logger.info("Training ML ensemble (this may take a few minutes)...")
        metrics = ml_gen.train_on_all(ticker_dfs)
        if metrics:
            logger.info(f"Training complete: AUC={metrics.get('auc', 0):.4f}")
            ml_gen.save()

    aggregator = SignalAggregator(
        rule_weight=config.RULE_WEIGHT,
        ml_weight=config.ML_WEIGHT,
        buy_threshold=config.BUY_THRESHOLD,
        sell_threshold=config.SELL_THRESHOLD,
        ml_generator=ml_gen,
    )
    signals = aggregator.rank_signals(
        ticker_dfs,
        top_buy=config.TOP_N_BUY_SIGNALS,
        top_sell=config.TOP_N_SELL_SIGNALS,
    )

    # Print to console
    print()
    print("=" * 65)
    print(f"  TÍN HIỆU CHỨNG KHOÁN — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("=" * 65)
    print(f"\n🟢 TOP {config.TOP_N_BUY_SIGNALS} MUA MẠNH:")
    for sig in signals['buy']:
        d = sig.to_dict()
        print(f"  {d['ticker']:6s} | Score={d['final_score']:.3f} | RSI={d['rsi']:.1f} | "
              f"Vol×{d['volume_ratio']:.1f} | {d['price']:>12,.0f}đ")

    print(f"\n🔴 TOP {config.TOP_N_SELL_SIGNALS} BÁN:")
    for sig in signals['sell']:
        d = sig.to_dict()
        print(f"  {d['ticker']:6s} | Score={d['final_score']:.3f} | RSI={d['rsi']:.1f} | "
              f"{d['price']:>12,.0f}đ")
    print("=" * 65)

    # Telegram
    if notify:
        notifier = TelegramNotifier(config.TELEGRAM_TOKEN, config.TELEGRAM_CHAT_ID)
        notifier.send_signals(signals)

    return signals


def run_backtest(demo: bool = True) -> None:
    """Backtest rule-based signal strategy on historical data."""
    logger.info("=== Backtest started ===")
    fetcher = DataFetcher(demo=demo)
    ticker_dfs = load_ticker_data(fetcher)
    if not ticker_dfs:
        logger.error("No data for backtest")
        return

    from signals.rule_based import RuleBasedScorer
    scorer = RuleBasedScorer()

    def signal_fn(ticker, df_slice):
        s = scorer.score_normalized(df_slice)
        if s >= config.BUY_THRESHOLD:
            return 'BUY'
        if s <= config.SELL_THRESHOLD:
            return 'SELL'
        return 'HOLD'

    engine = Backtest(
        initial_capital=config.INITIAL_CAPITAL,
        take_profit_pct=config.TAKE_PROFIT_PCT,
        stop_loss_pct=config.STOP_LOSS_PCT,
    )
    result = engine.run(ticker_dfs, signal_fn)

    print()
    print("=" * 65)
    print("  KẾT QUẢ BACKTEST")
    print("=" * 65)
    print(result.summary())
    print("=" * 65)

    if config.TELEGRAM_TOKEN:
        notifier = TelegramNotifier(config.TELEGRAM_TOKEN, config.TELEGRAM_CHAT_ID)
        notifier.send_backtest(result)


def run_scheduler(demo: bool = False) -> None:
    """Run signal scans on a schedule during Vietnamese market hours."""
    try:
        from apscheduler.schedulers.blocking import BlockingScheduler
        from apscheduler.triggers.cron import CronTrigger
    except ImportError:
        logger.error("apscheduler not installed: pip install apscheduler")
        sys.exit(1)

    scheduler = BlockingScheduler(timezone=config.TIMEZONE)
    for t in config.SCHEDULE_TIMES:
        h, m = map(int, t.split(':'))
        scheduler.add_job(
            run_scan,
            CronTrigger(hour=h, minute=m, day_of_week='mon-fri', timezone=config.TIMEZONE),
            kwargs={'demo': demo, 'notify': True},
            id=f'scan_{t}',
        )
        logger.info(f"Scheduled: {t} VN time (Mon-Fri)")

    logger.info("Scheduler running. Ctrl+C to stop.")
    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Stopped.")


def main():
    parser = argparse.ArgumentParser(description='VN Stock Signal System')
    parser.add_argument('--demo', action='store_true', help='Use synthetic demo data')
    parser.add_argument('--backtest', action='store_true', help='Run backtesting mode')
    parser.add_argument('--schedule', action='store_true', help='Run on schedule')
    parser.add_argument('--no-notify', action='store_true', help='Skip Telegram')
    args = parser.parse_args()

    if args.backtest:
        run_backtest(demo=args.demo)
    elif args.schedule:
        run_scheduler(demo=args.demo)
    else:
        run_scan(demo=args.demo, notify=not args.no_notify)


if __name__ == '__main__':
    main()
