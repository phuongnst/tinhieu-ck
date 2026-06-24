"""
Configuration and environment variables for the VN Stock Signal System.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

# Market hours (Vietnam time, UTC+7)
MARKET_OPEN = '09:15'
MARKET_CLOSE = '15:00'
TIMEZONE = 'Asia/Ho_Chi_Minh'

# Signal schedule times
SCHEDULE_TIMES = ['09:30', '11:00', '13:00', '14:30']

# Signal thresholds
TOP_N_BUY_SIGNALS = 10
TOP_N_SELL_SIGNALS = 5
BUY_THRESHOLD = 0.65
SELL_THRESHOLD = 0.35

# Rule-based vs ML weighting
RULE_WEIGHT = 0.4
ML_WEIGHT = 0.6

# Data settings
DEFAULT_LOOKBACK_DAYS = 365
RESOLUTION = '1D'  # Daily data

# ML settings
ML_RETRAIN_DAYS = 7
LABEL_HORIZON = 5       # Predict 5 days ahead
LABEL_GAIN_PCT = 0.02   # 2% gain threshold for BUY label

# Backtest settings
TAKE_PROFIT_PCT = 0.05   # 5% take profit
STOP_LOSS_PCT = 0.03     # 3% stop loss
INITIAL_CAPITAL = 100_000_000  # 100M VND

# Exchange lists
EXCHANGES = ['HOSE', 'HNX', 'UPCOM']

# Demo mode tickers
DEMO_TICKERS = [
    'VNM', 'VCB', 'BID', 'VIC', 'GAS', 'SAB', 'CTG', 'HPG', 'MBB', 'TCB',
    'VPB', 'ACB', 'MSN', 'POW', 'PLX', 'PNJ', 'FPT', 'MWG', 'HDB', 'STB'
]

# Logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'vn_stock_signals.log')
