"""
Configuration centralisée du bot
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

# Interactive Brokers
IBKR_HOST = os.getenv('IBKR_HOST', '127.0.0.1')
IBKR_PORT = int(os.getenv('IBKR_PORT', 7497))
IBKR_CLIENT_ID = int(os.getenv('IBKR_CLIENT_ID', 1))

# Benzinga
BENZINGA_API_KEY = os.getenv('BENZINGA_API_KEY', '')

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

# Trading Configuration
DRY_RUN_MODE = os.getenv('DRY_RUN_MODE', 'True').lower() == 'true'
PAPER_TRADING_MODE = os.getenv('PAPER_TRADING_MODE', 'True').lower() == 'true'
MAX_POSITIONS = int(os.getenv('MAX_POSITIONS', 5))
DAILY_LOSS_LIMIT = float(os.getenv('DAILY_LOSS_LIMIT', 0.02))
WEEKLY_LOSS_LIMIT = float(os.getenv('WEEKLY_LOSS_LIMIT', 0.06))
POSITION_SIZE_PCT = float(os.getenv('POSITION_SIZE_PCT', 0.20))

# Risk Management
STOP_LOSS_PCT = float(os.getenv('STOP_LOSS_PCT', 0.05))
TAKE_PROFIT_PCT = float(os.getenv('TAKE_PROFIT_PCT', 0.20))

# Timezone
TIMEZONE = os.getenv('TIMEZONE', 'America/New_York')

# Paths
DATA_DIR = BASE_DIR / 'data'
FILTERS_DIR = BASE_DIR / 'filters'
LOGS_DIR = BASE_DIR / 'logs'

# Files
WATCHLIST_CORE_FILE = DATA_DIR / 'watchlist_core.json'
WATCHLIST_SECONDARY_FILE = DATA_DIR / 'watchlist_secondary.json'
BLACKLIST_FILE = FILTERS_DIR / 'blacklist_sectors.json'
POSITIONS_FILE = DATA_DIR / 'positions.json'

# Trading Hours (US Eastern Time)
MARKET_OPEN = '09:30'
MARKET_CLOSE = '16:00'
EXCLUDED_START = '09:30'
EXCLUDED_END = '10:15'

# Sector ETFs
SECTOR_ETFS = {
    'technology': 'XLK',
    'consumer_discretionary': 'XLY',
    'energy': 'XLE',
    'financials': 'XLF',
    'healthcare': 'XLV',
    'industrials': 'XLI',
    'consumer_staples': 'XLP',
    'utilities': 'XLU',
    'materials': 'XLB',
    'real_estate': 'XLRE',
    'communication': 'XLC'
}

# Market Indices
MARKET_INDICES = ['SPY', 'QQQ', 'VIX']

# Candlestick Patterns (Steve Nison)
BULLISH_PATTERNS = [
    'HAMMER',
    'INVERTED_HAMMER',
    'BULLISH_ENGULFING',
    'PIERCING_LINE',
    'THREE_WHITE_SOLDIERS'
]

BEARISH_PATTERNS = [
    'SHOOTING_STAR',
    'HANGING_MAN',
    'DOJI',
    'BEARISH_ENGULFING',
    'EVENING_STAR'
]

# Filter Thresholds
MIN_VOLUME_MULTIPLIER = 1.2  # Volume must be 120% of avg
BREAKOUT_VOLUME_MULTIPLIER = 1.5  # Breakout requires 150% avg volume
VIX_MAX_LEVEL = 25
SPY_MIN_CHANGE = 0.003  # 0.3%
QQQ_MIN_CHANGE = 0.003
SECTOR_MIN_CHANGE = 0.005  # 0.5%
DOJI_BODY_PCT = 0.20  # Body < 20% of range = doji
HIGH_WICK_PCT = 0.50  # Upper shadow > 50% = high wick
SPREAD_MAX_PCT = 0.005  # 0.5%

# News Keywords (Negative)
NEGATIVE_KEYWORDS = [
    'downgrade',
    'lawsuit',
    'investigation',
    'recall',
    'fraud',
    'bankruptcy',
    'miss',
    'below expectations',
    'disappointing',
    'weak',
    'loss',
    'decline'
]

# Telegram Notification Cooldown
NOTIFICATION_COOLDOWN_SECONDS = 300  # 5 minutes

