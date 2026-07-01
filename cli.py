#!/usr/bin/env python3
"""
CLI entry point for the Simplified Trading Bot (Binance Futures Testnet).

Examples:
    python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
    python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 60000
"""
import argparse
import os
import sys

from bot.client import FuturesTestnetClient, BinanceClientError
from bot.logging_config import setup_logging
from bot.orders import execute_order, OrderResult
from bot.validators import ValidationError, OrderRequest, validate_order_request

from dotenv import load_dotenv

load_dotenv()

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Place MARKET or LIMIT orders on Binance Futures Testnet (USDT-M)."
    )
    parser.add_argument("--symbol", required=True, help="Trading pair symbol, e.g. BTCUSDT")
    parser.add_argument(
        "--side", required=True, choices=["BUY", "SELL", "buy", "sell"], help="Order side"
    )
    parser.add_argument(
        "--type",
        dest="order_type",
        required=True,
        choices=["MARKET", "LIMIT", "market", "limit"],
        help="Order type",
    )
    parser.add_argument("--quantity", required=True, type=float, help="Order quantity")
    parser.add_argument(
        "--price",
        required=False,
        type=float,
        default=None,
        help="Limit price (required for LIMIT orders, omit for MARKET orders)",
    )
    return parser


def print_summary(order_request: OrderRequest) -> None:
    print("\n--- Order Request Summary ---")
    print(f"Symbol:   {order_request.symbol}")
    print(f"Side:     {order_request.side}")
    print(f"Type:     {order_request.order_type}")
    print(f"Quantity: {order_request.quantity}")
    if order_request.price is not None:
        print(f"Price:    {order_request.price}")
    print("------------------------------\n")


def print_response(response: dict) -> None:
    print("--- Order Response ---")
    print(f"Order ID:      {response.get('orderId')}")
    print(f"Status:        {response.get('status')}")
    print(f"Executed Qty:  {response.get('executedQty')}")
    avg_price = response.get("avgPrice")
    if avg_price is not None:
        print(f"Avg Price:     {avg_price}")
    print("-----------------------\n")


def main() -> None:
    logger = setup_logging()
    parser = build_parser()
    args = parser.parse_args()

    api_key = os.environ.get("BINANCE_TESTNET_API_KEY")
    api_secret = os.environ.get("BINANCE_TESTNET_API_SECRET")

    if not api_key or not api_secret:
        logger.error("Missing BINANCE_TESTNET_API_KEY / BINANCE_TESTNET_API_SECRET environment variables.")
        print(
            "Error: Set BINANCE_TESTNET_API_KEY and BINANCE_TESTNET_API_SECRET "
            "environment variables before running this command."
        )
        sys.exit(1)

    # Validate CLI input before touching the network, so bad input fails fast
    # with a clear message instead of a confusing connection error.
    try:
        order_request = validate_order_request(
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
        )
    except ValidationError as exc:
        logger.error("Validation error: %s", exc)
        print(f"Invalid input: {exc}")
        sys.exit(1)

    try:
        client = FuturesTestnetClient(api_key, api_secret)
    except BinanceClientError as exc:
        logger.error("Client initialization failed: %s", exc)
        print(f"Error: {exc}")
        sys.exit(1)

    result: OrderResult = execute_order(
        client=client,
        symbol=order_request.symbol,
        side=order_request.side,
        order_type=order_request.order_type,
        quantity=order_request.quantity,
        price=order_request.price,
    )

    print_summary(result.request)

    if result.success:
        print_response(result.response)
        print("SUCCESS: Order placed successfully.")
    else:
        print(f"FAILURE: {result.error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
