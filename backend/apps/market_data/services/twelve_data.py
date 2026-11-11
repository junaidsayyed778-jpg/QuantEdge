import requests
from django.conf import settings


class TwelveDataClient:
    BASE_URL = "https://api.twelvedata.com"

    def __init__(self):
        self.api_key = settings.TWELVE_DATA_API_KEY

        if not self.api_key:
            raise ValueError(
                "Twelve Data API key is not configured."
            )

        self.session = requests.Session()

    def _get(self, endpoint, params=None):
        request_params = {
            "apikey": self.api_key,
        }

        if params:
            request_params.update(params)

        try:
            response = self.session.get(
                f"{self.BASE_URL}/{endpoint}",
                params=request_params,
                timeout=60,
            )

            response.raise_for_status()

            data = response.json()

            if data.get("status") == "error":
                raise RuntimeError(
                    f"Twelve Data API error: {data.get('message')}"
                )

            return data

        except requests.RequestException as error:
            raise RuntimeError(
                f"HTTP request failed: {error}"
            ) from error

    def get_stocks(self, country="India", exchange="NSE"):
        return self._get(
            "stocks",
            {
                "country": country,
                "exchange": exchange,
            },
        )
        
class get_time_series(
    self,
    symbol,
    interval= "1day",
    outputsize= 30,
    exchange="NSE",
):
    return self._get(
        "time_series",
        {
            "symbols": symbols,
            "interval": inteval,
            "outputsize": outputsize,
            "exchange": exchange,
            "country": "India",
        }
    )