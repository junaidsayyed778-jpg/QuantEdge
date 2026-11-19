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
        min_periods=20,
    ).mean()

    ema["ema_50"] = close.ewm(
        span=50,
        adjust=False,
        min_periods=50,
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
        adjust=False,
    ).mean()

    avg_loss = loss.ewm(
        alpha=1 / period,
        min_periods=period,
        adjust=False,
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
        min_periods=12,
    ).mean()

    ema_26 = close.ewm(
        span=26,
        adjust=False,
        min_periods=26,
    ).mean()

    macd_line = ema_12 - ema_26

    signal_line = macd_line.ewm(
        span=9,
        adjust=False,
        min_periods=9,
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
    std_dev: float = 2.0,
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


def calculate_adx(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
) -> pd.DataFrame:
    """
    Calculate Average Directional Index (ADX).

    ADX measures trend strength, not trend direction.
    """

    plus_dm = high.diff()
    minus_dm = -low.diff()

    plus_dm = plus_dm.where(
        (plus_dm > minus_dm) & (plus_dm > 0),
        0.0,
    )

    minus_dm = minus_dm.where(
        (minus_dm > plus_dm) & (minus_dm > 0),
        0.0,
    )

    previous_close = close.shift(1)

    tr = pd.concat(
        [
            high - low,
            (high - previous_close).abs(),
            (low - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    atr = tr.ewm(
        alpha=1 / period,
        min_periods=period,
        adjust=False,
    ).mean()

    smoothed_plus_dm = plus_dm.ewm(
        alpha=1 / period,
        min_periods=period,
        adjust=False,
    ).mean()

    smoothed_minus_dm = minus_dm.ewm(
        alpha=1 / period,
        min_periods=period,
        adjust=False,
    ).mean()

    plus_di = 100 * smoothed_plus_dm / atr
    minus_di = 100 * smoothed_minus_dm / atr

    denominator = plus_di + minus_di

    dx = (
        100 * (plus_di - minus_di).abs() / denominator
    ).where(denominator != 0, 0.0)

    adx = dx.ewm(
        alpha=1 / period,
        min_periods=period,
        adjust=False,
    ).mean()

    return pd.DataFrame({
        "plus_di": plus_di,
        "minus_di": minus_di,
        "adx": adx,
    })


def calculate_stochastic(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    k_period: int = 14,
    d_period: int = 3,
) -> pd.DataFrame:
    """
    Calculate Stochastic Oscillator.

    %k measures the closing price position
    within the recent high-low range

    $D is the moving average of $K.
    """

    # Highest high over the k period.
    highest_high = high.rolling(
        window=k_period,
    ).max()

    # Lowest low over the k period.
    lowest_low = low.rolling(
        window=k_period,
    ).min()

    # Calculate %k.
    denominator = highest_high - lowest_low

    stoch_k = (
        100 * (close - lowest_low) / denominator
    ).where(denominator != 0)

    # Calculate %D.
    stoch_d = stoch_k.rolling(
        window=d_period,
    ).mean()

    return pd.DataFrame({
        "stoch_k": stoch_k,
        "stoch_d": stoch_d,
    })


def calculate_atr(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
) -> pd.Series:
    previous_close = close.shift(1)

    true_range = pd.concat(
        [
            high - low,
            (high - previous_close).abs(),
            (low - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    atr = true_range.ewm(
        alpha=1 / period,
        min_periods=period,
        adjust=False,
    ).mean()

    return atr.rename(f"atr_{period}")


def calculate_obv(
    close: pd.Series,
    volume: pd.Series,
) -> pd.Series:

    price_change = close.diff()

    direction = price_change.apply(
        lambda change: 1 if change > 0
        else -1 if change < 0
        else 0
    )

    obv = (direction * volume).cumsum()

    return obv.rename("obv")
    price_change = close.diff()

    direction = price_change.apply(
        lambda change: (
            1 if change > 0
            else -1 if change < 0
            else 0
        )
    )

    obv = (direction * volume).cumsum()

    return obv.rename("obv")


def calculate_volume_sma(
    volume: pd.Series,
    period: int = 20,
) -> pd.Series:
    
    volume_sma = volume.rolling(
        window=period
    ).mean()
    
    return volume_sma.rename(f"volume_sma{period}")