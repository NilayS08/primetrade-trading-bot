from dataclasses import dataclass
from typing import Optional

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT"}


class ValidationError(Exception):
    """Raised when user-supplied order parameters fail validation."""


@dataclass
class OrderRequest:
    """A validated, normalized order ready to be sent to the API layer."""
    symbol: str
    side: str
    order_type: str
    quantity: float
    price: Optional[float] = None


def validate_order_request(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float],
) -> OrderRequest:
    if symbol is None or not symbol.strip():
        raise ValidationError("Symbol must not be empty.")
    symbol = symbol.strip().upper()
    if not symbol.isalnum():
        raise ValidationError(f"Symbol '{symbol}' looks invalid (expected something like BTCUSDT).")

    if side is None:
        raise ValidationError("Side must be provided.")
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValidationError(f"Side must be one of {sorted(VALID_SIDES)}, got '{side}'.")

    if order_type is None:
        raise ValidationError("Order type must be provided.")
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValidationError(f"Order type must be one of {sorted(VALID_ORDER_TYPES)}, got '{order_type}'.")

    if quantity is None or quantity <= 0:
        raise ValidationError(f"Quantity must be a positive number, got '{quantity}'.")

    if order_type == "LIMIT":
        if price is None or price <= 0:
            raise ValidationError("Price is required and must be positive for LIMIT orders.")
    else:  # MARKET
        if price is not None:
            raise ValidationError("Price must not be provided for MARKET orders.")

    return OrderRequest(
        symbol=symbol,
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=price,
    )
