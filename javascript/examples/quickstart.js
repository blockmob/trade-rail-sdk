/**
 * TradeRail JS quickstart (Node 18+).
 *
 *   npm install traderail
 *   TRADERAIL_API_KEY=ak_your_key node quickstart.js
 */

import { TradeRail, TradeRailError } from 'traderail'

const API_KEY = process.env.TRADERAIL_API_KEY || 'ak_your_key_here'
const LOGIN = Number(process.env.TRADERAIL_LOGIN || 5012345678)

const tr = new TradeRail({ apiKey: API_KEY })

// 1) Open a session -> "acct-<login>" selector.
const account = await tr.connect({ user: LOGIN })
console.log('session:', account)

// 2) Read the account.
const summary = await tr.accountSummary(account)
console.log(`balance=${summary.balance} equity=${summary.equity} ${summary.currency}`)

// 3) Price a symbol.
const q = await tr.quote(account, 'XAUUSD')
console.log(`XAUUSD bid=${q.bid} ask=${q.ask}`)

// 4) Recent 15-minute candles.
const bars = await tr.priceHistory(account, 'XAUUSD', { timeFrame: 15, numBars: 5 })
console.log(`got ${bars.length} bars, last close=${bars[bars.length - 1].close}`)

// 5) Place a DEMO market order (uncomment to run).
// try {
//   const res = await tr.orderSend(account, { operation: 'Buy', symbol: 'XAUUSD', volume: 0.10, sl: 2352, tp: 2378 })
//   console.log('ticket:', res.ticket)
// } catch (e) {
//   if (e instanceof TradeRailError) console.log('order rejected:', e.message)
//   else throw e
// }

// 6) See what's open.
const opened = await tr.openedOrders(account)
console.log('open positions:', (opened.positionInfos || []).length)
