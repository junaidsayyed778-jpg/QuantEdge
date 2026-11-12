# Communicate with Yahoo Finance

import yfinance as yf


class YahooFinanceClient:

    def get_time_series(
        self,
        symbol,
        period="1mo",
        interval="1d",
    ):
        ticker = yf.Ticker(symbol)

        data = ticker.history(
            period=period,
            interval=interval,
            auto_adjust=False,
            actions=False,
        )

        if data.empty:
            raise ValueError(
                f"No historical data found for {symbol}."
            )

        return data

    def get_latest_price(self, symbol):
        ticker = yf.Ticker(symbol)

        data = ticker.history(
            period="1d",
            interval="1m",
            auto_adjust=False,
            actions=False,
        )

        if data.empty:
            raise ValueError(
                f"No latest price data found for {symbol}."
            )

        latest = data.iloc[-1]

        return {
            "price": float(latest["Close"]),
            "open": float(latest["Open"]),
            "high": float(latest["High"]),
            "low": float(latest["Low"]),
            "volume": int(latest["Volume"]),
            "timestamp": data.index[-1].isoformat(),
        }