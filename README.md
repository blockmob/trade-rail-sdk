<div align="center">

# TradeRail

### The managed MetaTrader 5 (MT5) API

Connect any MT5 account, read live prices, place and manage orders, stream trades in real time, and broadcast one order across thousands of accounts — all through **one REST + WebSocket API**. Fully hosted and managed by TradeRail; nothing to install or run.

[![Website](https://img.shields.io/badge/website-traderail.cloud-c6f24e)](https://traderail.cloud)
[![API Docs](https://img.shields.io/badge/docs-API%20reference-blue)](https://traderail.cloud/docs.html)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](./LICENSE)

**[Website](https://traderail.cloud) · [API Reference](https://traderail.cloud/docs.html) · [Request access](https://traderail.cloud/#request)**

</div>

---

## What is TradeRail?

TradeRail is a **managed MT5 API**. You call clean HTTP + WebSocket endpoints; TradeRail runs and keeps the MT5 connections online for you. It works the same across brokers and scales the same from one account to thousands — the API never changes.

- **One API for everything** — accounts, market data, orders, history, and real-time events.
- **Copy-trade in one call** — fan a single order out to many accounts at once.
- **Real-time** — a WebSocket stream pushes live quotes and trade events; no polling.
- **Demo-safe** — trading is DEMO-only by default; going live is an explicit opt-in.
- **Broker-agnostic** — send a base symbol (e.g. `XAUUSD`); it's resolved to the broker's exact name.
- **Fully managed** — no MetaTrader, no VPS, no remote desktop on your side.

This repo has the official **[Python](./python)** and **[JavaScript](./javascript)** SDKs, runnable examples, and the **[OpenAPI spec](./openapi.json)**.

## Quickstart

Every `/v1` request carries your `ApiKey` header and names the account with `?id=<login>`.

<details open><summary><b>cURL</b></summary>

```bash
# Read an account
curl -H "ApiKey: ak_your_key" \
  "https://api.traderail.cloud/v1/AccountSummary?id=5012345678"

# Live quote
curl -H "ApiKey: ak_your_key" \
  "https://api.traderail.cloud/v1/GetQuote?id=5012345678&symbol=XAUUSD"

# Place a DEMO market order
curl -H "ApiKey: ak_your_key" \
  "https://api.traderail.cloud/v1/OrderSendTask?id=5012345678&operation=Buy&symbol=XAUUSD&volume=0.10&stoploss=2352&takeprofit=2378"
```
</details>

<details open><summary><b>Python</b></summary>

```bash
pip install traderail
```
```python
from traderail import TradeRail

tr = TradeRail(api_key="ak_...")
account = tr.connect(user=5012345678)          # -> "acct-5012345678"

print(tr.account_summary(account))             # balance, equity, margin, ...
print(tr.quote(account, "XAUUSD"))             # {'bid': ..., 'ask': ..., 'last': ...}
tr.order_send(account, "Buy", "XAUUSD", 0.10, sl=2352, tp=2378)   # DEMO by default
```
</details>

<details open><summary><b>JavaScript / Node 18+</b></summary>

```bash
npm install traderail
```
```js
import { TradeRail } from 'traderail'

const tr = new TradeRail({ apiKey: 'ak_...' })
const account = await tr.connect({ user: 5012345678 })   // "acct-5012345678"

console.log(await tr.accountSummary(account))
console.log(await tr.quote(account, 'XAUUSD'))
await tr.orderSend(account, { operation: 'Buy', symbol: 'XAUUSD', volume: 0.10, sl: 2352, tp: 2378 })
```
</details>

## Authentication

| Surface | Auth | Header |
|---|---|---|
| `/v1/*` (data + trading) | **API key** | `ApiKey: ak_...` |
| `/orchestrator/*` (copy-trade) & `/events` (WebSocket) | **Bearer token** | `Authorization: Bearer tk_...` |

Both are issued when your account is provisioned. You can view and rotate them in your dashboard. Keep them secret — anyone with your key can act on your account.

## Endpoints

**Accounts & sessions** — `ConnectEx` · `ConnectByToken` · `Reconnect` · `CheckConnect` · `AccountSummary`
**Market data** — `GetQuote` · `SymbolList` · `Symbols` · `PriceHistoryEx`
**Trading** (DEMO-only by default) — `OpenedOrders` · `OrderSendTask` · `OrderModifyTask` · `OrderCloseTask` · `OrderCancelTask`
**History & analytics** — `OrderHistory` · `OrderHistoryPagination` · `TradeStats` · `EquityHistory`
**Copy-trade** (Bearer) — `POST /orchestrator/bulk-order` · `POST /orchestrator/bulk-close`
**Real-time** (Bearer) — `wss://api.traderail.cloud/events`

Full request/response reference: **[traderail.cloud/docs.html](https://traderail.cloud/docs.html)** · machine-readable **[openapi.json](./openapi.json)**.

## Copy-trade

Fire one order across many accounts in a single call — the copy-trading / PAMM primitive.

```python
tr = TradeRail(api_key="ak_...", token="tk_...")
res = tr.bulk_order("Buy", "XAUUSD", 0.01)     # omit logins => every connected account
print(res["ok"], "/", res["requested"], "filled in", res["ms"], "ms")
```

## Real-time (WebSocket)

Connect to `wss://api.traderail.cloud/events` with your bearer token, then `watch` an account and `subscribe` to symbols:

```js
const ws = new WebSocket('wss://api.traderail.cloud/events?token=tk_...')
ws.onopen = () => {
  ws.send(JSON.stringify({ event: 'watch', data: { id: 5012345678 } }))
  ws.send(JSON.stringify({ event: 'subscribe', data: { id: 5012345678, symbols: ['XAUUSD'] } }))
}
ws.onmessage = (m) => {
  const { event, accountId, data } = JSON.parse(m.data)
  // event: 'quote' | 'deal' | 'order'
  console.log(event, accountId, data)
}
```

## SDKs

| Language | Package | Folder |
|---|---|---|
| Python | `pip install traderail` | [`/python`](./python) |
| JavaScript / Node | `npm install traderail` | [`/javascript`](./javascript) |

Both are thin wrappers over the REST API and mirror the same methods. Prefer another language? The [OpenAPI spec](./openapi.json) generates a client in any of them.

## Getting access

Access is provisioned by TradeRail — [request access](https://traderail.cloud/#request) and you'll get your API key + token and a dashboard to manage them. The docs and OpenAPI spec are public, so you can evaluate the API before you commit.

## License

MIT © TradeRail. See [LICENSE](./LICENSE).
