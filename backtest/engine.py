"""
Event-driven backtesting engine.
Simulates: buy on BUY signal, exit on take-profit / stop-loss / SELL signal.
Accounts for commission. Supports multi-ticker portfolio.
"""

import logging
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class Trade:
    ticker: str
    entry_date: pd.Timestamp
    entry_price: float
    exit_date: Optional[pd.Timestamp] = None
    exit_price: Optional[float] = None
    exit_reason: str = ''
    pnl_pct: float = 0.0
    is_open: bool = True

    def close(self, date, price, reason):
        self.exit_date = date
        self.exit_price = price
        self.exit_reason = reason
        self.pnl_pct = (price - self.entry_price) / self.entry_price
        self.is_open = False


@dataclass
class BacktestResult:
    total_return_pct: float
    win_rate: float
    sharpe_ratio: float
    max_drawdown_pct: float
    n_trades: int
    avg_hold_days: float
    trades: List[Trade] = field(default_factory=list)
    equity_curve: pd.Series = field(default_factory=pd.Series)

    def summary(self) -> str:
        return (
            f"Lợi nhuận: {self.total_return_pct:+.2f}%  |  "
            f"Win Rate: {self.win_rate:.1f}%  |  "
            f"Sharpe: {self.sharpe_ratio:.2f}  |  "
            f"Max DD: {self.max_drawdown_pct:.2f}%  |  "
            f"Trades: {self.n_trades}  |  "
            f"Avg Hold: {self.avg_hold_days:.1f}d"
        )

    def to_dict(self) -> dict:
        return {
            'total_return_pct': round(self.total_return_pct, 2),
            'win_rate': round(self.win_rate, 2),
            'sharpe_ratio': round(self.sharpe_ratio, 3),
            'max_drawdown_pct': round(self.max_drawdown_pct, 2),
            'n_trades': self.n_trades,
            'avg_hold_days': round(self.avg_hold_days, 1),
        }


class Backtest:
    """Portfolio backtester with TP/SL and configurable signal function."""

    def __init__(
        self,
        initial_capital: float = 100_000_000,
        take_profit_pct: float = 0.05,
        stop_loss_pct: float = 0.03,
        commission_pct: float = 0.0015,
        max_positions: int = 5,
    ):
        self.initial_capital = initial_capital
        self.tp = take_profit_pct
        self.sl = stop_loss_pct
        self.commission = commission_pct
        self.max_pos = max_positions

    def run(
        self,
        ticker_dfs: Dict[str, pd.DataFrame],
        signal_fn: Callable[[str, pd.DataFrame], str],
    ) -> BacktestResult:
        """
        Args:
            ticker_dfs: {ticker: df_with_all_indicators}
            signal_fn: (ticker, df_up_to_date) -> 'BUY' | 'SELL' | 'HOLD'
        """
        capital = self.initial_capital
        positions: Dict[str, Trade] = {}
        all_trades: List[Trade] = []
        equity: Dict[pd.Timestamp, float] = {}
        pos_size = self.initial_capital / self.max_pos

        all_dates = sorted({d for df in ticker_dfs.values() for d in df.index})

        for date in all_dates:
            # --- Manage open positions ---
            for ticker in list(positions.keys()):
                trade = positions[ticker]
                df = ticker_dfs.get(ticker)
                if df is None or date not in df.index:
                    continue
                price = float(df.loc[date, 'close'])

                if price >= trade.entry_price * (1 + self.tp):
                    sell_price = price * (1 - self.commission)
                    trade.close(date, sell_price, 'take_profit')
                    capital += pos_size * (1 + trade.pnl_pct)
                    all_trades.append(trade)
                    del positions[ticker]
                elif price <= trade.entry_price * (1 - self.sl):
                    sell_price = price * (1 - self.commission)
                    trade.close(date, sell_price, 'stop_loss')
                    capital += pos_size * (1 + trade.pnl_pct)
                    all_trades.append(trade)
                    del positions[ticker]
                else:
                    df_slice = df[df.index <= date]
                    try:
                        sig = signal_fn(ticker, df_slice)
                    except Exception:
                        sig = 'HOLD'
                    if sig == 'SELL':
                        sell_price = price * (1 - self.commission)
                        trade.close(date, sell_price, 'signal')
                        capital += pos_size * (1 + trade.pnl_pct)
                        all_trades.append(trade)
                        del positions[ticker]

            # --- Open new positions ---
            if len(positions) < self.max_pos:
                for ticker, df in ticker_dfs.items():
                    if ticker in positions or date not in df.index:
                        continue
                    df_slice = df[df.index <= date]
                    if len(df_slice) < 30:
                        continue
                    try:
                        sig = signal_fn(ticker, df_slice)
                    except Exception:
                        sig = 'HOLD'
                    if sig == 'BUY':
                        price = float(df.loc[date, 'close'])
                        entry = price * (1 + self.commission)
                        if capital >= pos_size:
                            capital -= pos_size
                            positions[ticker] = Trade(ticker=ticker, entry_date=date, entry_price=entry)
                    if len(positions) >= self.max_pos:
                        break

            equity[date] = capital + sum(
                pos_size for _ in positions  # approximate open position value
            )

        # Close remaining at last price
        for ticker, trade in positions.items():
            df = ticker_dfs.get(ticker)
            if df is not None and not df.empty:
                lp = float(df.iloc[-1]['close']) * (1 - self.commission)
                trade.close(df.index[-1], lp, 'end_of_data')
            all_trades.append(trade)

        eq = pd.Series(equity)
        final_cap = eq.iloc[-1] if len(eq) > 0 else self.initial_capital
        total_ret = (final_cap - self.initial_capital) / self.initial_capital * 100

        closed = [t for t in all_trades if not t.is_open]
        win_rate = (sum(1 for t in closed if t.pnl_pct > 0) / max(len(closed), 1)) * 100

        if len(eq) > 1:
            dr = eq.pct_change().dropna()
            sharpe = (dr.mean() / dr.std() * np.sqrt(252)) if dr.std() > 0 else 0.0
        else:
            sharpe = 0.0

        if len(eq) > 0:
            roll_max = eq.cummax()
            max_dd = float(((eq - roll_max) / roll_max.replace(0, np.nan) * 100).min())
        else:
            max_dd = 0.0

        hold_days = [(t.exit_date - t.entry_date).days for t in closed if t.exit_date and t.entry_date]
        avg_hold = float(np.mean(hold_days)) if hold_days else 0.0

        return BacktestResult(
            total_return_pct=total_ret,
            win_rate=win_rate,
            sharpe_ratio=sharpe,
            max_drawdown_pct=max_dd,
            n_trades=len(closed),
            avg_hold_days=avg_hold,
            trades=all_trades,
            equity_curve=eq,
        )
