"""
Telegram notification bot for VN stock buy/sell signals.
"""

import asyncio
import logging
from datetime import datetime
from typing import List

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Send formatted signal alerts to a Telegram chat."""

    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = str(chat_id)
        self._bot = None

    def _get_bot(self):
        if not self._bot:
            try:
                from telegram import Bot
                self._bot = Bot(token=self.token)
            except ImportError:
                logger.error("python-telegram-bot not installed")
        return self._bot

    def _format(self, signals: dict) -> str:
        now = datetime.now().strftime('%d/%m/%Y %H:%M')
        lines = [f"📈 *TÍN HIỆU CHỨNG KHOÁN VN* — {now}", ""]

        buys = signals.get('buy', [])
        if buys:
            lines.append("🟢 *MUA MẠNH:*")
            for sig in buys:
                d = sig.to_dict() if hasattr(sig, 'to_dict') else sig
                price = f"{d['price']:,.0f}đ" if d.get('price') else "N/A"
                rsi = f"RSI={d['rsi']:.0f}" if d.get('rsi') else ""
                vol = f"Vol×{d['volume_ratio']:.1f}" if d.get('volume_ratio') else ""
                pats = ", ".join(d.get('patterns', [])[:2])
                parts = [p for p in [price, f"Score={d['final_score']:.2f}", rsi, vol, pats] if p]
                lines.append(f"  • *{d['ticker']}* | {' | '.join(parts)}")
            lines.append("")

        sells = signals.get('sell', [])
        if sells:
            lines.append("🔴 *BÁN / TRÁNH:*")
            for sig in sells:
                d = sig.to_dict() if hasattr(sig, 'to_dict') else sig
                price = f"{d['price']:,.0f}đ" if d.get('price') else "N/A"
                rsi = f"RSI={d['rsi']:.0f}" if d.get('rsi') else ""
                parts = [p for p in [price, f"Score={d['final_score']:.2f}", rsi] if p]
                lines.append(f"  • *{d['ticker']}* | {' | '.join(parts)}")
            lines.append("")

        if not buys and not sells:
            lines.append("_Không có tín hiệu rõ ràng trong phiên này._")

        lines.append("⚠️ _Tín hiệu tham khảo, không phải khuyến nghị đầu tư._")
        return "\n".join(lines)

    async def _send_async(self, text: str):
        bot = self._get_bot()
        if bot is None:
            print(text)
            return
        try:
            await bot.send_message(chat_id=self.chat_id, text=text, parse_mode='Markdown')
            logger.info("Telegram message sent")
        except Exception as e:
            logger.error(f"Telegram send error: {e}")
            print(text)

    def _run(self, coro):
        try:
            asyncio.run(coro)
        except RuntimeError:
            asyncio.get_event_loop().run_until_complete(coro)

    def send_signals(self, signals: dict):
        """Format and send buy/sell signal notification."""
        if not self.token or not self.chat_id:
            print(self._format(signals))
            return
        self._run(self._send_async(self._format(signals)))

    def send_text(self, text: str):
        """Send plain text message."""
        if not self.token or not self.chat_id:
            print(text)
            return
        self._run(self._send_async(text))

    def send_backtest(self, result) -> None:
        """Send backtesting summary."""
        msg = (
            "📊 *KẾT QUẢ BACKTEST*\n"
            f"Lợi nhuận: `{result.total_return_pct:+.2f}%`\n"
            f"Win Rate: `{result.win_rate:.1f}%`\n"
            f"Sharpe: `{result.sharpe_ratio:.2f}`\n"
            f"Max Drawdown: `{result.max_drawdown_pct:.2f}%`\n"
            f"Số giao dịch: `{result.n_trades}`\n"
            f"Giữ trung bình: `{result.avg_hold_days:.1f} ngày`"
        )
        self.send_text(msg)
