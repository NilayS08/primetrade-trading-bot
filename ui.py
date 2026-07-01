"""
Bonus:
A lightweight Tkinter GUI wrapping the same bot.orders.execute_order()
logic used by cli.py. No extra dependencies -- Tkinter ships with Python.

Run with:
    python ui.py

Requires BINANCE_TESTNET_API_KEY / BINANCE_TESTNET_API_SECRET env vars,
same as the CLI.
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox

from bot.client import FuturesTestnetClient, BinanceClientError
from bot.logging_config import setup_logging
from bot.orders import execute_order
from bot.validators import ValidationError

from dotenv import load_dotenv

load_dotenv()

logger = setup_logging()


class TradingBotUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Simplified Trading Bot - Futures Testnet")
        self.geometry("420x420")
        self.resizable(False, False)
        self._client = None
        self._build_form()

    def _build_form(self):
        pad = {"padx": 10, "pady": 6}

        ttk.Label(self, text="Symbol (e.g. BTCUSDT)").grid(row=0, column=0, sticky="w", **pad)
        self.symbol_var = tk.StringVar(value="BTCUSDT")
        ttk.Entry(self, textvariable=self.symbol_var).grid(row=0, column=1, **pad)

        ttk.Label(self, text="Side").grid(row=1, column=0, sticky="w", **pad)
        self.side_var = tk.StringVar(value="BUY")
        ttk.Combobox(
            self, textvariable=self.side_var, values=["BUY", "SELL"], state="readonly"
        ).grid(row=1, column=1, **pad)

        ttk.Label(self, text="Order Type").grid(row=2, column=0, sticky="w", **pad)
        self.type_var = tk.StringVar(value="MARKET")
        type_box = ttk.Combobox(
            self, textvariable=self.type_var, values=["MARKET", "LIMIT"], state="readonly"
        )
        type_box.grid(row=2, column=1, **pad)
        type_box.bind("<<ComboboxSelected>>", self._on_type_change)

        ttk.Label(self, text="Quantity").grid(row=3, column=0, sticky="w", **pad)
        self.quantity_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.quantity_var).grid(row=3, column=1, **pad)

        self.price_label = ttk.Label(self, text="Price (LIMIT only)")
        self.price_label.grid(row=4, column=0, sticky="w", **pad)
        self.price_var = tk.StringVar()
        self.price_entry = ttk.Entry(self, textvariable=self.price_var, state="disabled")
        self.price_entry.grid(row=4, column=1, **pad)

        ttk.Button(self, text="Place Order", command=self._submit).grid(
            row=5, column=0, columnspan=2, pady=12
        )

        self.output = tk.Text(self, height=13, width=48, state="disabled")
        self.output.grid(row=6, column=0, columnspan=2, padx=10, pady=6)

    def _on_type_change(self, _event=None):
        if self.type_var.get() == "LIMIT":
            self.price_entry.configure(state="normal")
        else:
            self.price_var.set("")
            self.price_entry.configure(state="disabled")

    def _log_to_box(self, text: str):
        self.output.configure(state="normal")
        self.output.insert("end", text + "\n")
        self.output.configure(state="disabled")
        self.output.see("end")

    def _get_client(self) -> FuturesTestnetClient:
        if self._client is not None:
            return self._client
        api_key = os.environ.get("BINANCE_TESTNET_API_KEY")
        api_secret = os.environ.get("BINANCE_TESTNET_API_SECRET")
        if not api_key or not api_secret:
            raise BinanceClientError(
                "Set BINANCE_TESTNET_API_KEY and BINANCE_TESTNET_API_SECRET environment variables."
            )
        self._client = FuturesTestnetClient(api_key, api_secret)
        return self._client

    def _submit(self):
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.configure(state="disabled")

        try:
            client = self._get_client()
        except BinanceClientError as exc:
            messagebox.showerror("Client Error", str(exc))
            return

        quantity_raw = self.quantity_var.get().strip()
        price_raw = self.price_var.get().strip()

        try:
            quantity = float(quantity_raw) if quantity_raw else None
        except ValueError:
            messagebox.showerror("Invalid Input", "Quantity must be a number.")
            return

        price = None
        if self.type_var.get() == "LIMIT":
            try:
                price = float(price_raw) if price_raw else None
            except ValueError:
                messagebox.showerror("Invalid Input", "Price must be a number.")
                return

        try:
            result = execute_order(
                client=client,
                symbol=self.symbol_var.get(),
                side=self.side_var.get(),
                order_type=self.type_var.get(),
                quantity=quantity,
                price=price,
            )
        except ValidationError as exc:
            messagebox.showerror("Invalid Input", str(exc))
            return

        self._log_to_box(
            f"Request: {result.request.symbol} {result.request.side} "
            f"{result.request.order_type} qty={result.request.quantity} "
            f"price={result.request.price}"
        )

        if result.success:
            r = result.response
            self._log_to_box(f"Order ID:     {r.get('orderId')}")
            self._log_to_box(f"Status:       {r.get('status')}")
            self._log_to_box(f"Executed Qty: {r.get('executedQty')}")
            if r.get("avgPrice") is not None:
                self._log_to_box(f"Avg Price:    {r.get('avgPrice')}")
            self._log_to_box("SUCCESS: Order placed successfully.")
        else:
            self._log_to_box(f"FAILURE: {result.error}")


if __name__ == "__main__":
    app = TradingBotUI()
    app.mainloop()
