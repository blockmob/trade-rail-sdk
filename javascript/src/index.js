/**
 * TradeRail — the managed MetaTrader 5 (MT5) API.
 * A tiny, zero-dependency client for https://api.traderail.cloud (Node 18+ / modern browsers).
 *
 *   import { TradeRail } from 'traderail'
 *
 *   const tr = new TradeRail({ apiKey: 'ak_...' })
 *   const account = await tr.connect({ user: 5012345678 })   // "acct-5012345678"
 *   console.log(await tr.accountSummary(account))
 *   console.log(await tr.quote(account, 'XAUUSD'))
 *   await tr.orderSend(account, { operation: 'Buy', symbol: 'XAUUSD', volume: 0.10, sl: 2352, tp: 2378 })
 *
 * Docs: https://traderail.cloud/docs.html
 */

export const DEFAULT_BASE_URL = 'https://api.traderail.cloud'

export class TradeRailError extends Error {
  constructor(message, { status = null, payload = null } = {}) {
    super(message)
    this.name = 'TradeRailError'
    this.status = status
    this.payload = payload
  }
}

export class TradeRail {
  /**
   * @param {object} opts
   * @param {string} opts.apiKey   Your API key (ApiKey header).
   * @param {string} [opts.token]  Bearer token for copy-trade (/orchestrator) + the event stream.
   * @param {string} [opts.baseUrl]
   * @param {number} [opts.timeout] ms (default 30000)
   */
  constructor({ apiKey, token = null, baseUrl = DEFAULT_BASE_URL, timeout = 30000 } = {}) {
    if (!apiKey) throw new Error('apiKey is required')
    this.apiKey = apiKey
    this.token = token
    this.baseUrl = baseUrl.replace(/\/+$/, '')
    this.timeout = timeout
  }

  // -- low-level ------------------------------------------------------------
  async #get(path, params) {
    const qs = new URLSearchParams(clean(params)).toString()
    return this.#req('GET', path + (qs ? `?${qs}` : ''))
  }

  async #post(path, body) {
    const headers = { 'content-type': 'application/json' }
    if (this.token) headers.authorization = 'Bearer ' + this.token
    return this.#req('POST', path, { headers, body: JSON.stringify(clean(body) || {}) })
  }

  async #req(method, path, init = {}) {
    const ctrl = new AbortController()
    const t = setTimeout(() => ctrl.abort(), this.timeout)
    try {
      const res = await fetch(this.baseUrl + path, {
        method,
        signal: ctrl.signal,
        ...init,
        headers: { ApiKey: this.apiKey, accept: 'application/json', ...(init.headers || {}) },
      })
      const text = await res.text()
      let data
      try { data = text ? JSON.parse(text) : null } catch { data = text }
      if (!res.ok) {
        const msg = (data && data.message) || `HTTP ${res.status}`
        throw new TradeRailError(msg, { status: res.status, payload: data })
      }
      if (data && typeof data === 'object' && data.code === 'ERROR') {
        throw new TradeRailError(data.message || 'request rejected', { status: res.status, payload: data })
      }
      return data
    } finally {
      clearTimeout(t)
    }
  }

  // -- system ---------------------------------------------------------------
  ping() { return this.#get('/v1/Ping') }
  healthz() { return this.#get('/healthz') }

  // -- accounts & sessions --------------------------------------------------
  /** Confirm/open a session -> "acct-<login>". password/server only for not-yet-running accounts. */
  connect({ user, password, server, symbol } = {}) {
    return this.#get('/v1/ConnectEx', { user, password, server, symbol })
  }
  async checkConnect(account) {
    try { return String(await this.#get('/v1/CheckConnect', { id: account })).trim() === 'ok' }
    catch { return false }
  }
  accountSummary(account) { return this.#get('/v1/AccountSummary', { id: account }) }

  // -- market data ----------------------------------------------------------
  quote(account, symbol) { return this.#get('/v1/GetQuote', { id: account, symbol }) }
  symbolList(account) { return this.#get('/v1/SymbolList', { id: account }) }
  symbols(account) { return this.#get('/v1/Symbols', { id: account }) }
  /** OHLC bars. timeFrame in MINUTES (1,5,15,30,60,240,1440); numBars up to 5000. */
  priceHistory(account, symbol, { timeFrame = 30, numBars = 100 } = {}) {
    return this.#get('/v1/PriceHistoryEx', { id: account, symbol, timeFrame, numBars })
  }

  // -- trading (DEMO-only by default) --------------------------------------
  openedOrders(account) { return this.#get('/v1/OpenedOrders', { id: account }) }
  /** operation: Buy|Sell (market) or BuyLimit|SellLimit|BuyStop|SellStop|BuyStopLimit|SellStopLimit (+price). */
  orderSend(account, { operation, symbol, volume, sl, tp, price, slippage, magic, comment } = {}) {
    return this.#get('/v1/OrderSendTask', {
      id: account, operation, symbol, volume,
      stoploss: sl, takeprofit: tp, price, slippage, expertID: magic, comment,
    })
  }
  orderModify(account, ticket, { sl, tp, price } = {}) {
    return this.#get('/v1/OrderModifyTask', { id: account, ticket, stoploss: sl, takeprofit: tp, price })
  }
  /** Close a position (full, or partial via lots). Passing a pending-order ticket cancels it. */
  orderClose(account, ticket, { lots, slippage } = {}) {
    return this.#get('/v1/OrderCloseTask', { id: account, ticket, lots, slippage })
  }
  /** Cancel (delete) a pending order by ticket. */
  orderCancel(account, ticket) { return this.#get('/v1/OrderCancelTask', { id: account, ticket }) }
  /** Close a position by an opposite position on the same symbol (hedging accounts only). */
  orderCloseBy(account, ticket, closeByTicket) { return this.#get('/v1/OrderCloseByTask', { id: account, ticket, closeByTicket }) }

  // -- history & analytics --------------------------------------------------
  orderHistory(account) { return this.#get('/v1/OrderHistory', { id: account }) }
  orderHistoryPaginated(account, { from, to, sort = 'CloseTime', ascending = false, page = 0, perPage = 100 } = {}) {
    return this.#get('/v1/OrderHistoryPagination', {
      id: account, from, to, sort, ascending, pageNumber: page, ordersPerPage: perPage,
    })
  }
  tradeStats(account, { from } = {}) { return this.#get('/v1/TradeStats', { id: account, from }) }
  equityHistory(account, { from } = {}) { return this.#get('/v1/EquityHistory', { id: account, from }) }
  /** Every deal belonging to one position id. */
  historyDealsByPosition(account, positionId) { return this.#get('/v1/HistoryDealsByPositionId', { id: account, positionId }) }
  /** History of pending (limit/stop) orders over a window. */
  pendingOrderHistory(account, { from, to } = {}) { return this.#get('/v1/PendingOrderHistory', { id: account, from, to }) }
  /** Raw ticks for a symbol over a window (epoch seconds / ISO). */
  tickHistory(account, symbol, { from, to } = {}) { return this.#get('/v1/TickHistory', { id: account, symbol, from, to }) }

  // -- copy-trade (needs a bearer token) -----------------------------------
  /** Fire ONE market order across many accounts. Omit logins => every connected account. */
  bulkOrder({ operation, symbol, volume, sl, tp, comment, logins } = {}) {
    this.#requireToken()
    return this.#post('/orchestrator/bulk-order', { operation, symbol, volume, sl, tp, comment, logins })
  }
  /** Close every open position across many accounts. Omit logins => every connected account. */
  bulkClose({ logins } = {}) {
    this.#requireToken()
    return this.#post('/orchestrator/bulk-close', { logins })
  }

  #requireToken() {
    if (!this.token) {
      throw new TradeRailError('a bearer token is required for copy-trade (/orchestrator) calls; pass { token } to new TradeRail(...)')
    }
  }
}

function clean(obj) {
  if (!obj) return obj
  const out = {}
  for (const [k, v] of Object.entries(obj)) if (v !== undefined && v !== null) out[k] = v
  return out
}

export default TradeRail
