import pandas as pd

from apps.market_data.models import Stock, HistoricalPrice

from .technical_analysis import calculate_all_indicators

from .support_resistance import (
    calculate_swing_points,
    cluster_price_levels,
    calculate_relative_volume,
    calculate_zone_volume_confirmation,
    calculate_zone_reactions,
    calculate_zone_strength,
)

from .signal_generator import (
    calculate_trend_score,
    calculate_momentum_score,
    calculate_volume_score,
    calculate_volatility_score,
    calculate_support_resistance_score,
    calculate_final_signal,
)


def analyze_stock(symbol: str):
    # 1. Retrieve stock
    try:
        stock = Stock.objects.get(
            symbol=symbol.upper(),
            is_active=True,
        )
    except Stock.DoesNotExist:
        raise ValueError(f"Active stock {symbol} not found.")

    # 2. Retrieve historical prices in chronological order
    records = HistoricalPrice.objects.filter(
        stock=stock
    ).order_by("trading_date")

    prices = pd.DataFrame(
        list(
            records.values(
                "trading_date",
                "open",
                "high",
                "low",
                "close",
                "volume",
            )
        ),
        columns=[
            "trading_date",
            "open",
            "high",
            "low",
            "close",
            "volume",
        ],
    )
    
    # Convert database Decimal values into numeric floats
    for column in ["open", "high", "low", "close", "volume"]:
        prices[column] = pd.to_numeric(
            prices[column],
            errors="raise",
        ).astype(float)

    if len(prices) < 200:
        raise ValueError(
            "At least 200 historical records are required."
        )

    # 3. Calculate technical indicators
    indicators = calculate_all_indicators(prices)

    df = pd.concat(
        [prices.reset_index(drop=True), indicators.reset_index(drop=True)],
        axis=1,
    )

    # 4. Calculate support and resistance
    swing_points = calculate_swing_points(
        df["high"],
        df["low"],
    )

    df = pd.concat([df, swing_points], axis=1)

    df["relative_volume"] = calculate_relative_volume(
        df["volume"]
    )

    support_levels = cluster_price_levels(df["swing_low"])
    resistance_levels = cluster_price_levels(df["swing_high"])

    right_bars = 5

    df["swing_low_rvol"] = (
        df["relative_volume"]
        .shift(right_bars)
        .where(df["swing_low"].notna())
    )

    df["swing_high_rvol"] = (
        df["relative_volume"]
        .shift(right_bars)
        .where(df["swing_high"].notna())
    )

    support_volume = calculate_zone_volume_confirmation(
        support_levels,
        df["swing_low"],
        df["swing_low_rvol"],
    )

    resistance_volume = calculate_zone_volume_confirmation(
        resistance_levels,
        df["swing_high"],
        df["swing_high_rvol"],
    )

    support_reactions = calculate_zone_reactions(
        support_levels,
        df,
        df["swing_low"],
        zone_type="support",
    )

    resistance_reactions = calculate_zone_reactions(
        resistance_levels,
        df,
        df["swing_high"],
        zone_type="resistance",
    )

    support_zones = calculate_zone_strength(
        support_reactions,
        support_volume,
    )

    resistance_zones = calculate_zone_strength(
        resistance_reactions,
        resistance_volume,
    )

    # 5. Get latest valid indicator values
    latest = df.dropna(
        subset=[
            "sma_20",
            "sma_50",
            "ema_20",
            "ema_50",
            "rsi_14",
            "macd",
            "signal",
            "stoch_k",
            "stoch_d",
            "adx",
            "plus_di",
            "minus_di",
            "bb_upper",
            "bb_lower",
            "bb_middle",
            "relative_volume",
        ]
    ).iloc[-1]

    # 6. Calculate category scores
    trend_score = calculate_trend_score(
        latest["sma_20"],
        latest["sma_50"],
        latest["ema_20"],
        latest["ema_50"],
        latest["adx"],
        latest["plus_di"],
        latest["minus_di"],
    )

    momentum_score = calculate_momentum_score(
        latest["rsi_14"],
        latest["macd"],
        latest["signal"],
        latest["stoch_k"],
        latest["stoch_d"],
    )

    price_change_pct = (
        (latest["close"] - latest["open"])
        / latest["open"]
    ) * 100

    volume_score = calculate_volume_score(
        latest["relative_volume"],
        price_change_pct,
    )

    volatility_score = calculate_volatility_score(
        latest["close"],
        latest["bb_upper"],
        latest["bb_lower"],
        latest["bb_middle"],
    )

    support_resistance_score = calculate_support_resistance_score(
        latest["close"],
        support_zones,
        resistance_zones,
    )

    # 7. Generate final signal
    final_signal = calculate_final_signal(
        trend_score,
        momentum_score,
        volume_score,
        volatility_score,
        support_resistance_score,
    )

    return {
        "stock": {
            "symbol": stock.symbol,
            "company_name": stock.company_name,
            "exchange": stock.exchange,
        },
        "analysis_date": str(latest["trading_date"]),
        "latest_price": float(latest["close"]),
        "scores": final_signal,
        "support_zones": support_zones,
        "resistance_zones": resistance_zones,
    }