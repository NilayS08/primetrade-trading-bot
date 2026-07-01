# PrimeTrade Trading Bot

A small Python CLI (with an optional GUI) that places MARKET and LIMIT
orders on the Binance USDT-M Futures Testnet, with input validation,
structured logging, and clean error handling.

## Project Structure

```
primetrade-trading-bot/
  bot/
    __init__.py
    client.py          # Binance API client wrapper (network/API layer)
    orders.py           # Order placement logic (glues validation + client)
    validators.py       # Input validation
    logging_config.py   # Logging setup (console + rotating file)
  cli.py                 # CLI entry point
  ui.py                  # Bonus: lightweight Tkinter GUI
  logs/                  # Log files land here (trading_bot.log)
  requirements.txt
  .env
  README.md
```

## 1. Setup

### 1.1 Create a Futures Testnet account and API key

1. Go to https://testnet.binancefuture.com and log in (GitHub login is
   supported).
2. Once logged in, generate an **API Key** and **Secret** from the testnet
   dashboard (usually under "API Key" on the site).
3. Your testnet account starts with demo USDT balance you can trade with —
   no real funds are involved anywhere in this project.

### 1.2 Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate        # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Requires Python 3.9+.

### 1.3 Configure credentials

Copy `.env.example` to `.env` and fill in your testnet key/secret, **or**
export them directly in your shell:

```bash
export BINANCE_TESTNET_API_KEY="your_api_key_here"
export BINANCE_TESTNET_API_SECRET="your_api_secret_here"
```

(If you use a `.env` file, load it with `python-dotenv` or `source .env`
before running — this project reads credentials from environment
variables directly to keep the dependency list minimal.)

## 2. Running the CLI

Place a **MARKET** order:

```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
```

Place a **LIMIT** order:

```bash
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 60000
```

### CLI arguments

| Argument     | Required          | Description                              |
|--------------|--------------------|-------------------------------------------|
| `--symbol`   | Yes                | Trading pair, e.g. `BTCUSDT`             |
| `--side`     | Yes                | `BUY` or `SELL`                          |
| `--type`     | Yes                | `MARKET` or `LIMIT`                      |
| `--quantity` | Yes                | Order quantity (positive number)         |
| `--price`    | Only for `LIMIT`   | Limit price (must be omitted for MARKET) |

Sample output:

```
--- Order Request Summary ---
Symbol:   BTCUSDT
Side:     BUY
Type:     MARKET
Quantity: 0.01
------------------------------

--- Order Response ---
Order ID:      123456789
Status:        FILLED
Executed Qty:  0.01
Avg Price:     60123.40
-----------------------

SUCCESS: Order placed successfully.
```

On failure (bad input, API rejection, or network issue), the CLI prints a
clear `Invalid input: ...` or `FAILURE: ...` message and exits with a
non-zero status code — nothing is silently swallowed.

## 3. Running the bonus GUI

```bash
python ui.py
```

A small Tkinter window lets you fill in symbol/side/type/quantity/price and
place an order with a click, reusing the exact same `bot/` logic as the
CLI (no duplicated business logic). Tkinter ships with standard Python, so
no extra dependency is needed.

## 4. Logging

Every run logs to both the console and `logs/trading_bot.log` (rotated at
2MB, keeping 3 backups). Each log line includes a timestamp, level,
logger name, and message, and covers:

* the outgoing order request parameters
* the raw API response
* any validation, API, or network error

This keeps the log useful for debugging/audit without being noisy (e.g. no
per-HTTP-header dumps).

## 5. Error handling

The app distinguishes three failure types and reports each clearly:

1. **Invalid input** (e.g. missing price on a LIMIT order, non-positive
   quantity, bad side/type) — caught in `bot/validators.py` before any
   network call is made.
2. **API errors** (e.g. Binance rejects the order — insufficient balance,
   invalid symbol, precision errors) — caught in `bot/client.py` and
   surfaced as `BinanceClientError`.
3. **Network errors** (timeouts, DNS failures, etc.) — also caught in
   `bot/client.py` and wrapped the same way, so the CLI layer only ever
   has to handle one exception type for anything API/network-related.

## 6. Assumptions

* This project targets **USDT-M Futures** only (not Coin-M, not Spot).
* Only `MARKET` and `LIMIT` order types are supported, per the task spec.
  LIMIT orders are sent with `timeInForce=GTC` (Good-Til-Canceled), since
  the spec didn't require configurable time-in-force.
* Credentials are read from environment variables rather than a config
  file or hard-coded values, to avoid ever committing secrets.
* The testnet host is pinned explicitly in `bot/client.py` on the futures
  URL, on top of `python-binance`'s built-in `testnet=True` flag, as a
  safety net across library versions.
* Quantity/price precision (step size, tick size) is left to Binance to
  validate/reject via the API — the project does not pre-fetch and
  enforce exchange filters, since that was not a stated requirement.
* No real funds are ever used — this only talks to
  `https://testnet.binancefuture.com`.

## 7. Deliverable log files

After running one MARKET and one LIMIT order against your own testnet
credentials, `logs/trading_bot.log` will contain both request/response
pairs, ready to include as the deliverable log evidence.
