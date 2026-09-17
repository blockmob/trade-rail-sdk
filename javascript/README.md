# TradeRail — JavaScript / Node SDK

Official JS client for the [TradeRail](https://traderail.cloud) managed MetaTrader 5 (MT5) API. Zero dependencies, Node 18+ (uses the built-in `fetch`).

```bash
npm install traderail
```

```js
import { TradeRail } from 'traderail'

const tr = new TradeRail({ apiKey: 'ak_...' })     // issued when your account is provisioned

const account = await tr.connect({ user: 5012345678 })   // "acct-5012345678"
console.log(await tr.accountSummary(account))            // balance, equity, margin, ...
console.log(await tr.quote(account, 'XAUUSD'))           // { bid, ask, last }

// DEMO-only by default
await tr.orderSend(account, { operation: 'Buy', symbol: 'XAUUSD', volume: 0.10, sl: 2352, tp: 2378 })
```

Copy-trade fan-out (one call → many accounts) needs a bearer token:

```js
const tr = new TradeRail({ apiKey: 'ak_...', token: 'tk_...' })
await tr.bulkOrder({ operation: 'Buy', symbol: 'XAUUSD', volume: 0.01 })  // omit logins => all connected
```

Full method list and the REST reference: **https://traderail.cloud/docs.html**

## Methods
`ping` · `connect` · `checkConnect` · `accountSummary` · `quote` · `symbolList` · `symbols` ·
`priceHistory` · `tickHistory` · `openedOrders` · `orderSend` · `orderModify` · `orderClose` · `orderCancel` · `orderCloseBy` ·
`orderHistory` · `orderHistoryPaginated` · `historyDealsByPosition` · `pendingOrderHistory` · `tradeStats` · `equityHistory` ·
`bulkOrder` · `bulkClose`

Errors throw `TradeRailError` (HTTP errors and broker-rejected trades).

MIT licensed. © TradeRail.
