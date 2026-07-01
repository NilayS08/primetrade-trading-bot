import logging
from typing import Optional

from binance.client import Client
from binance.exceptions import (
    BinanceAPIException,
    BinanceOrderException,
    BinanceRequestException,
)

logger = logging.getLogger("trading_bot.client")

FUTURES_TESTNET_BASE_URL = "https://testnet.binancefuture.com"


class BinanceClientError(Exception):
    pass

class FuturesTestnetClient:
    """Thin wrapper around python-binance's Client, pinned to the USDT-M Futures Testnet."""

    def __init__(self, api_key: str, api_secret: str):
        if not api_key or not api_secret:
            raise BinanceClientError("API key and secret must be provided.")

        try:
            self._client = Client(api_key, api_secret, testnet=True)
            # Explicitly pin the futures endpoint to the testnet host. This is a
            # safety net in case a given python-binance version doesn't route
            # futures calls to the testnet host via testnet=True alone.
            self._client.FUTURES_URL = FUTURES_TESTNET_BASE_URL + "/fapi"
        except Exception as exc:  # noqa: BLE001 - convert to our domain error
            raise BinanceClientError(
                f"Failed to initialize Binance client: {exc}"
            ) from exc

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
    ) -> dict:
        params = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
            "newOrderRespType": "RESULT",
        }

        if order_type == "LIMIT":
            params["price"] = price
            params["timeInForce"] = "GTC"

        logger.info("Sending order request: %s", params)

        try:
            response = self._client.futures_create_order(**params)
            logger.info("Order response received: %s", response)
            return response
        except (BinanceAPIException, BinanceOrderException) as exc:
            logger.error("Binance API rejected the order: %s", exc)
            raise BinanceClientError(f"Binance API error: {exc}") from exc
        except BinanceRequestException as exc:
            logger.error("Malformed request sent to Binance: %s", exc)
            raise BinanceClientError(f"Request error: {exc}") from exc
        except Exception as exc:  # noqa: BLE001 - network errors, timeouts, DNS, etc.
            logger.error("Network or unexpected error while placing order: %s", exc)
            raise BinanceClientError(f"Network/unexpected error: {exc}") from exc

    def get_symbol_info(self, symbol: str) -> Optional[dict]:
        """Fetch exchange info for a single symbol. Returns None if not found."""
        try:
            info = self._client.futures_exchange_info()
            for s in info.get("symbols", []):
                if s.get("symbol") == symbol:
                    return s
            return None
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to fetch exchange info: %s", exc)
            raise BinanceClientError(f"Failed to fetch exchange info: {exc}") from exc
