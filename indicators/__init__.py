"""Technical indicators package."""
from .trend import add_trend_indicators
from .momentum import add_momentum_indicators
from .volatility import add_volatility_indicators
from .volume import add_volume_indicators
from .patterns import detect_candlestick_patterns


def add_all_indicators(df):
    """Apply all technical indicator groups to DataFrame."""
    df = add_trend_indicators(df)
    df = add_momentum_indicators(df)
    df = add_volatility_indicators(df)
    df = add_volume_indicators(df)
    df = detect_candlestick_patterns(df)
    return df


__all__ = [
    'add_trend_indicators',
    'add_momentum_indicators',
    'add_volatility_indicators',
    'add_volume_indicators',
    'detect_candlestick_patterns',
    'add_all_indicators',
]
