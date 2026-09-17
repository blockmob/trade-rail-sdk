"""
TradeRail Python quickstart.

    pip install traderail
    export TRADERAIL_API_KEY=ak_your_key
    python quickstart.py
"""

import os
from traderail import TradeRail, TradeRailError

# Your API key is issued when your account is provisioned. Keep it secret.
API_KEY = os.environ.get("TRADERAIL_API_KEY", "ak_your_key_here")

# The MT5 account (login) you were set up with.
LOGIN = int(os.environ.get("TRADERAIL_LOGIN", "5012345678"))

tr = TradeRail(api_key=API_KEY)

# 1) Open a session -> "acct-<login>" selector used on every later call.
account = tr.connect(user=LOGIN)
print("session:", account)

# 2) Read the account.
summary = tr.account_summary(account)
print(f"balance={summary['balance']} equity={summary['equity']} {summary['currency']}")

# 3) Price a symbol (base symbol; resolved to the broker's exact name).
q = tr.quote(account, "XAUUSD")
print(f"XAUUSD bid={q['bid']} ask={q['ask']}")

# 4) Recent 15-minute candles.
bars = tr.price_history(account, "XAUUSD", timeframe=15, num_bars=5)
print(f"got {len(bars)} bars, last close={bars[-1]['close']}")

# 5) Place a DEMO market order (uncomment to run).
# try:
#     res = tr.order_send(account, "Buy", "XAUUSD", 0.10, sl=2352, tp=2378)
#     print("ticket:", res["ticket"])
# except TradeRailError as e:
#     print("order rejected:", e)

# 6) See what's open.
opened = tr.opened_orders(account)
print("open positions:", len(opened.get("positionInfos", [])))
