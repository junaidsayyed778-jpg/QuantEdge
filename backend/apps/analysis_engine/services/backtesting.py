from collections import Counter

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


class BacktestConfig:
    MINIMUM_CANDLES = 200
    HOLDING_PERIOD = 5

    # Total cost for entry + exit
    ROUND_TRIP_COST_PCT = 0.1

    SIGNAL_THRESHOLD = 20


def load_backtest_data(symbol: str) -> pd.DataFrame:
    try:
        stock = Stock.objects.get(
            symbol=symbol.upper(),
            exchange="NSE",
            is_active=True,
        )
    except Stock.DoesNotExist:
        raise ValueError(f"Active NSE stock {symbol} not found.")

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
        )
    )

    if len(prices) < BacktestConfig.MINIMUM_CANDLES:
        raise ValueError(
            f"At least {BacktestConfig.MINIMUM_CANDLES}"
            " historical candles are required."
        )

    for column in ["open", "high", "low", "close", "volume"]:
        prices[column] = pd.to_numeric(
            prices[column],
            errors="raise",
        ).astype(float)

    prices.reset_index(drop=True, inplace=True)

    return prices


def prepare_backtest_indicators(prices: pd.DataFrame) -> pd.DataFrame:
    indicators = calculate_all_indicators(prices)

    df = pd.concat(
        [
            prices.reset_index(drop=True),
            indicators.reset_index(drop=True),
        ],
        axis=1,
    )

    df["relative_volume"] = calculate_relative_volume(
        df["volume"]
    )

    return df


def calculate_historical_zones(prices: pd.DataFrame):
    df = prices.copy()

    swing_points = calculate_swing_points(
        df["high"],
        df["low"],
    )

    df = pd.concat([df, swing_points], axis=1)

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

    reaction_window = 5

    # Only use swing points with all 5 reaction candles available.
    completed_reaction_mask = (
        df.index + reaction_window < len(df)
    )

    confirmed_support_swings = df["swing_low"].where(
        completed_reaction_mask
    )

    confirmed_resistance_swings = df["swing_high"].where(
        completed_reaction_mask
    )

    support_reactions = calculate_zone_reactions(
        support_levels,
        df,
        confirmed_support_swings,
        reaction_window=reaction_window,
        zone_type="support",
    )

    resistance_reactions = calculate_zone_reactions(
        resistance_levels,
        df,
        confirmed_resistance_swings,
        reaction_window=reaction_window,
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

    return support_zones, resistance_zones


def generate_historical_signal(row, support_zones, resistance_zones):
    trend_score = calculate_trend_score(
        row["sma_20"],
        row["sma_50"],
        row["ema_20"],
        row["ema_50"],
        row["adx"],
        row["plus_di"],
        row["minus_di"],
    )

    momentum_score = calculate_momentum_score(
        row["rsi_14"],
        row["macd"],
        row["signal"],
        row["stoch_k"],
        row["stoch_d"],
    )

    price_change_pct = (
        (row["close"] - row["open"]) / row["open"]
    ) * 100

    volume_score = calculate_volume_score(
        row["relative_volume"],
        price_change_pct,
    )

    volatility_score = calculate_volatility_score(
        row["close"],
        row["bb_upper"],
        row["bb_lower"],
        row["bb_middle"],
    )

    support_resistance_score = calculate_support_resistance_score(
        row["close"],
        support_zones,
        resistance_zones,
    )

    return calculate_final_signal(
        trend_score,
        momentum_score,
        volume_score,
        volatility_score,
        support_resistance_score,
    )


def simulate_trade(
    signal_date,
    entry_row,
    exit_row,
    signal_results,
):
    signal = signal_results["signal"]

    entry_price = float(entry_row["open"])
    exit_price = float(exit_row["close"])

    if entry_price <= 0:
        raise ValueError("Entry price must be greater than zero.")

    if exit_price <= 0:
        raise ValueError("Exit price must be greater than zero.")

    if signal in ("bullish", "strong_bullish"):
        gross_return = (
            (exit_price - entry_price) / entry_price
        ) * 100

    elif signal in ("bearish", "strong_bearish"):
        gross_return = (
            (entry_price - exit_price) / entry_price
        ) * 100

    else:
        return None

    net_return = (
        gross_return - BacktestConfig.ROUND_TRIP_COST_PCT
    )

    return {
        "signal_date": str(signal_date),
        "entry_date": str(entry_row["trading_date"]),
        "exit_date": str(exit_row["trading_date"]),
        "signal": signal,
        "score": signal_results["overall_score"],
        "entry_price": entry_price,
        "exit_price": exit_price,
        "gross_return_pct": round(gross_return, 4),
        "net_return_pct": round(net_return, 4),
        "win": net_return > 0,
    }


def run_backtest(symbol: str):
    df = prepare_backtest_indicators(
        load_backtest_data(symbol)
    )

    trades = []
    all_signals = Counter()

    i = BacktestConfig.MINIMUM_CANDLES - 1
    holding_period = BacktestConfig.HOLDING_PERIOD

    required_indicators = [
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

    while i + holding_period < len(df):
        history = df.iloc[: i + 1].copy()

        support_zones, resistance_zones = (
            calculate_historical_zones(history)
        )

        row = history.iloc[-1]

        if row[required_indicators].isna().any():
            i += 1
            continue

        signal_result = generate_historical_signal(
            row, support_zones, resistance_zones
        )
        all_signals[signal_result["signal"]] += 1
        print(
            row["trading_date"],
            signal_result["signal"],
            signal_result["overall_score"],
        )

        if signal_result["signal"] == "neutral":
            i += 1
            continue

        entry_row = df.iloc[i + 1]
        exit_row = df.iloc[i + holding_period]

        trade = simulate_trade(
            signal_date=row["trading_date"],
            entry_row=entry_row,
            exit_row=exit_row,
            signal_results=signal_result,
        )

        if trade is not None:
            trades.append(trade)
            i += holding_period
        else:
            i += 1

    print("ALL GENERATED SIGNALS:", dict(all_signals))

    metrics = calculate_backtest_metrics(trades)
    signal_distribution = Counter(
        trade["signal"] for trade in trades
    )
    print("SIGNAL DISTRIBUTION:", dict(signal_distribution))

    return {
        "symbol": symbol.upper(),
        "total_trades": len(trades),
        "metrics": metrics,
        "trades": trades,
    }

    df = prepare_backtest_indicators(
        load_backtest_data(symbol)
    )

    trades = []

    start_index = BacktestConfig.MINIMUM_CANDLES - 1
    holding_period = BacktestConfig.HOLDING_PERIOD

    for i in range(start_index, len(df) - holding_period):
        history = df.iloc[: i + 1].copy()

        support_zones, resistance_zones = (
            calculate_historical_zones(history)
        )

        row = history.iloc[-1]

        required_indicators = [
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

        if row[required_indicators].isna().any():
            continue

        signal_result = generate_historical_signal(
            row,
            support_zones,
            resistance_zones,
        )

        print(
            row["trading_date"],
            signal_result["signal"],
            signal_result["overall_score"],
        )

        if signal_result["signal"] == "neutral":
            continue

        entry_row = df.iloc[i + 1]
        exit_row = df.iloc[i + holding_period]

        trade = simulate_trade(
            signal_date=row["trading_date"],
            entry_row=entry_row,
            exit_row=exit_row,
            signal_results=signal_result,
        )

        if trade is not None:
            trades.append(trade)

    metrics = calculate_backtest_metrics(trades)

    return {
        "symbol": symbol.upper(),
        "total_trades": len(trades),
        "metrics": metrics,
        "trades": trades,
    }

def calculate_backtest_metrics(trades):
    if not trades:
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0,
            "average_return_pct": 0,
            "average_win_pct": 0,
            "average_loss_pct": 0,
            "profit_factor": 0,
            "bullish_trades": 0,
            "bearish_trades": 0,
            "total_return_pct": 0,
            "max_drawdown_pct": 0,
        }

    trade_returns = [
        trade["net_return_pct"] for trade in trades
    ]

    winning_returns = [
        value for value in trade_returns if value > 0
    ]

    losing_returns = [
        value for value in trade_returns if value < 0
    ]

    gross_profit = sum(winning_returns)
    gross_loss = abs(sum(losing_returns))

    wins = len(winning_returns)

    returns = [value / 100 for value in trade_returns]

    equity = pd.Series(returns).add(1).cumprod()
    running_peak = equity.cummax()

    drawdown = ((equity / running_peak) - 1) * 100

    total_return = (equity.iloc[-1] - 1) * 100

    bullish_trades = sum(
        trade["signal"] in ("bullish", "strong_bullish")
        for trade in trades
    )

    bearish_trades = sum(
        trade["signal"] in ("bearish", "strong_bearish")
        for trade in trades
    )

    long_returns = [
        trade["net_return_pct"]
        for trade in trades
        if trade["signal"] in ("bullish", "strong_bullish")
    ]

    short_returns = [
        trade["net_return_pct"]
        for trade in trades
        if trade["signal"] in ("bearish", "strong_bearish")
    ]

    return {
        "total_trades": len(trades),
        "winning_trades": wins,
        "losing_trades": len(losing_returns),
        "win_rate": round(wins / len(trades) * 100, 2),
        "average_return_pct": round(
            sum(trade_returns) / len(trade_returns), 4
        ),
        "average_win_pct": round(
            sum(winning_returns) / len(winning_returns), 4
        ) if winning_returns else 0,
        "average_loss_pct": round(
            sum(losing_returns) / len(losing_returns), 4
        ) if losing_returns else 0,
        "profit_factor": round(
            gross_profit / gross_loss, 4
        ) if gross_loss else None,
        "bullish_trades": bullish_trades,
        "bearish_trades": bearish_trades,
        "total_return_pct": float(round(total_return, 4)),
        "max_drawdown_pct": float(round(drawdown.min(), 4)),
        "long_average_return_pct": (
            round(sum(long_returns) / len(long_returns), 4)
            if long_returns
            else 0
        ),
        "short_average_return_pct": (
            round(sum(short_returns) / len(short_returns), 4)
            if short_returns
            else 0
        ),
    }
