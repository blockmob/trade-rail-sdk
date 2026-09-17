# TradeRail — Python SDK

Official Python client for the [TradeRail](https://traderail.cloud) managed MetaTrader 5 (MT5) API.

```bash
pip install traderail
```

```python
from traderail import TradeRail

tr = TradeRail(api_key="ak_...")          # issued when your account is provisioned

account = tr.connect(user=5012345678)     # -> "acct-5012345678"
print(tr.account_summary(account))        # balance, equity, margin, ...
print(tr.quote(account, "XAUUSD"))        # {'bid': ..., 'ask': ..., 'last': ...}

# DEMO-only by default
tr.order_send(account, "Buy", "XAUUSD", 0.10, sl=2352, tp=2378)
```

Copy-trade fan-out (one call → many accounts) needs a bearer token:

```python
tr = TradeRail(api_key="ak_...", token="tk_...")
tr.bulk_order("Buy", "XAUUSD", 0.01)      # omit logins => every connected account
```

Full method list and the REST reference: **https://traderail.cloud/docs.html**

## Methods
`ping` · `connect` · `check_connect` · `account_summary` · `quote` · `symbol_list` · `symbols` ·
`price_history` · `opened_orders` · `order_send` · `order_modify` · `order_close` ·
`order_history` · `order_history_paginated` · `trade_stats` · `equity_history` ·
`bulk_order` · `bulk_close`

Errors raise `TradeRailError` (HTTP errors and broker-rejected trades).

MIT licensed. © TradeRail.
