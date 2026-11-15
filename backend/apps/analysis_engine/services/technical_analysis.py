import pandas as pd

from .technical_indicators import (
    calculate_sma,
    calculate_ema,
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands,
)


def calculate_all_indicators(close: pd.Series) -> pd.DataFrame:
    """
    Calculate all currently implemented technical indicators
    and combine them into a single DataFrame.
    """

    indicators = pd.concat(
        [
            calculate_sma(close),
            calculate_ema(close),
            calculate_rsi(close),
            calculate_macd(close),
            calculate_bollinger_bands(close),
        ],
        axis=1,
    )

    return indicators