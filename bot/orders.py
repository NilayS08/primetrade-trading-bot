import logging
from typing import Optional

from .client import FuturesTestnetClient, BinanceClientError
from .validators import validate_order_request, OrderRequest

logger = logging.getLogger("trading_bot.orders")


class OrderResult:
    """Structured outcome of an order attempt, for easy rendering by any UI layer."""

    def __init__(
        self,
        success: bool,
        request: OrderRequest,
        response: Optional[dict] = None,
        error: Optional[str] = None,
    ):
        self.success = success
        self.request = request
        self.response = response
        self.error = error


def execute_order(
    client: FuturesTestnetClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float],
) -> OrderResult:
    order_request = validate_order_request(symbol, side, order_type, quantity, price)

    logger.info(
        "Order request summary: symbol=%s side=%s type=%s quantity=%s price=%s",
        order_request.symbol,
        order_request.side,
        order_request.order_type,
        order_request.quantity,
        order_request.price,
    )

    try:
        response = client.place_order(
            symbol=order_request.symbol,
            side=order_request.side,
            order_type=order_request.order_type,
            quantity=order_request.quantity,
            price=order_request.price,
        )
        return OrderResult(success=True, request=order_request, response=response)
    except BinanceClientError as exc:
        logger.error("Order failed: %s", exc)
        return OrderResult(success=False, request=order_request, error=str(exc))
