import pandas as pd

from .technical_indicators import (
    calculate_sma,
    calculate_ema,
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands,
    calculate_adx,
    calculate_stochastic,
    calculate_atr,
    calculate_obv,
    calculate_volume_sma,
)


def calculate_all_indicators(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate all technical indicators using historical OHLCV data.

    Required columns:
    high, low, close, volume
    """

    required_columns = ["high", "low", "close", "volume"]

    missing_columns = [
        column for column in required_columns
        if column not in prices.columns
    ]

    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    # Convert Decimal/object values into float
    prices = prices.copy()

    for column in required_columns:
        prices[column] = pd.to_numeric(
            prices[column],
            errors="raise"
        ).astype(float)

    high = prices["high"]
    low = prices["low"]
    close = prices["close"]
    volume = prices["volume"]

    indicators = pd.concat(
        [
            calculate_sma(close),
            calculate_ema(close),
            calculate_rsi(close),
            calculate_macd(close),
            calculate_bollinger_bands(close),
            calculate_adx(high, low, close),
            calculate_stochastic(high, low, close),
            calculate_atr(high, low, close),
            calculate_obv(close, volume),
            calculate_volume_sma(volume),
        ],
        axis=1,
    )

    return indicators