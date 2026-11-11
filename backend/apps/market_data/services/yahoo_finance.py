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