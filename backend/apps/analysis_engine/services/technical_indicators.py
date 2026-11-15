import pandas as pd


def calculate_sma(close: pd.Series) -> pd.DataFrame:
    sma = pd.DataFrame(index=close.index)

    sma["sma_20"] = close.rolling(window=20).mean()
    sma["sma_50"] = close.rolling(window=50).mean()
    sma["sma_200"] = close.rolling(window=200).mean()

    return sma


def calculate_ema(close: pd.Series) -> pd.DataFrame:
    ema = pd.DataFrame(index=close.index)

    ema["ema_20"] = close.ewm(
        span=20,
        adjust=False,
        min_periods=20
    ).mean()

    ema["ema_50"] = close.ewm(
        span=50,
        adjust=False,
        min_periods=50
    ).mean()

    return ema

def calculate_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate Relative Strength Index using Wilder's smoothing.

    Args:
        close: Chronologically ordered closing prices.
        period: RSI calculation period.

    Returns:
        RSI series.
    """

    delta = close.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(
        alpha=1 / period,
        min_periods=period,
        adjust=False
    ).mean()

    avg_loss = loss.ewm(
        alpha=1 / period,
        min_periods=period,
        adjust=False
    ).mean()

    rs = avg_gain / avg_loss

    rsi = 100 - (100 / (1 + rs))

    rsi = rsi.mask((avg_loss == 0) & (avg_gain > 0), 100)
    rsi = rsi.mask((avg_gain == 0) & (avg_loss == 0), 50)

    return rsi.rename("rsi_14")

def calculate_macd(close: pd.Series) -> pd.DataFrame:
    """
    Calculate MACD using standard parameters (12, 26, 9).
    """

    ema_12 = close.ewm(
        span=12,
        adjust=False,
        min_periods=12
    ).mean()

    ema_26 = close.ewm(
        span=26,
        adjust=False,
        min_periods=26
    ).mean()

    macd_line = ema_12 - ema_26

    signal_line = macd_line.ewm(
        span=9,
        adjust=False,
        min_periods=9
    ).mean()

    histogram = macd_line - signal_line

    return pd.DataFrame({
        "macd": macd_line,
        "signal": signal_line,
        "histogram": histogram,
    })
    
def calculate_bollinger_bands(
    close: pd.Series,
    period: int = 20,
    std_dev: float = 2.0
) -> pd.DataFrame:

    middle_band = close.rolling(window=period).mean()

    rolling_std = close.rolling(window=period).std()

    upper_band = middle_band + (rolling_std * std_dev)

    lower_band = middle_band - (rolling_std * std_dev)

    return pd.DataFrame({
        "bb_middle": middle_band,
        "bb_upper": upper_band,
        "bb_lower": lower_band,
    })