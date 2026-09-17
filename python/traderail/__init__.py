"""
TradeRail — the managed MetaTrader 5 (MT5) API.

A tiny, dependency-light client for https://api.traderail.cloud

    from traderail import TradeRail

    tr = TradeRail(api_key="ak_...")
    acct = tr.connect(user=5012345678)          # -> "acct-5012345678"
    print(tr.account_summary(acct))             # balance, equity, margin, ...
    print(tr.quote(acct, "XAUUSD"))             # {'bid': ..., 'ask': ..., 'last': ...}
    tr.order_send(acct, "Buy", "XAUUSD", 0.10, sl=2352, tp=2378)

Docs: https://traderail.cloud/docs.html
"""

from __future__ import annotations

import requests

__version__ = "1.0.0"
__all__ = ["TradeRail", "TradeRailError"]

DEFAULT_BASE_URL = "https://api.traderail.cloud"


class TradeRailError(RuntimeError):
    """Raised on an HTTP error or a rejected trade (code == 'ERROR')."""

    def __init__(self, message: str, *, status: int | None = None, payload=None):
        super().__init__(message)
        self.status = status
        self.payload = payload


class TradeRail:
    """
    Client for the TradeRail MT5 API.

    :param api_key: Your API key (``ApiKey`` header) — issued when your account is provisioned.
    :param token:   Optional bearer token for copy-trade fan-out (``/orchestrator``) and the event stream.
    :param base_url: API base URL. Defaults to the production host.
    :param timeout: Per-request timeout in seconds.
    """

    def __init__(
        self,
        api_key: str,
        *,
        token: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
    ):
        if not api_key:
            raise ValueError("api_key is required")
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self._s = requests.Session()
        self._s.headers.update({"ApiKey": api_key, "Accept": "application/json"})

    # -- low-level -----------------------------------------------------------
    def _get(self, path: str, params: dict | None = None):
        r = self._s.get(self.base_url + path, params=_clean(params), timeout=self.timeout)
        return _parse(r)

    def _post(self, path: str, body: dict | None = None):
        headers = {}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        r = self._s.post(self.base_url + path, json=body or {}, headers=headers, timeout=self.timeout)
        return _parse(r)

    # -- system --------------------------------------------------------------
    def ping(self):
        """Liveness of the API surface. Returns ``{'code': 'OK'}``."""
        return self._get("/v1/Ping")

    def healthz(self):
        """Unauthenticated health check (plain text ``ok``)."""
        return self._get("/healthz")

    # -- accounts & sessions -------------------------------------------------
    def connect(self, user: int, password: str | None = None, server: str | None = None,
                symbol: str | None = None) -> str:
        """
        Confirm (or open) a session and get the ``acct-<login>`` selector to pass as
        ``account`` on later calls. ``password``/``server`` are only needed to stand up an
        account that isn't already running (normally done for you at onboarding).
        """
        return self._get("/v1/ConnectEx", {"user": user, "password": password,
                                            "server": server, "symbol": symbol})

    def check_connect(self, account) -> bool:
        """True if the account is currently connected."""
        try:
            return str(self._get("/v1/CheckConnect", {"id": account})).strip() == "ok"
        except TradeRailError:
            return False

    def account_summary(self, account) -> dict:
        """Balance, equity, margin, free margin, leverage, P/L, broker, server."""
        return self._get("/v1/AccountSummary", {"id": account})

    # -- market data ---------------------------------------------------------
    def quote(self, account, symbol: str) -> dict:
        """Latest bid / ask / last for ``symbol`` (base symbol; resolved per broker)."""
        return self._get("/v1/GetQuote", {"id": account, "symbol": symbol})

    def symbol_list(self, account) -> list:
        """Every symbol name available on the account."""
        return self._get("/v1/SymbolList", {"id": account})

    def symbols(self, account) -> dict:
        """Map of symbol name -> specification (digits, point, tick size, volume limits)."""
        return self._get("/v1/Symbols", {"id": account})

    def price_history(self, account, symbol: str, timeframe: int = 30, num_bars: int = 100) -> list:
        """
        OHLC bars, oldest -> newest. ``timeframe`` is in MINUTES (1, 5, 15, 30, 60, 240, 1440).
        ``num_bars`` up to 5000.
        """
        return self._get("/v1/PriceHistoryEx", {"id": account, "symbol": symbol,
                                                 "timeFrame": timeframe, "numBars": num_bars})

    # -- trading (DEMO-only by default) --------------------------------------
    def opened_orders(self, account) -> dict:
        """Open positions (live P/L) and pending orders currently working."""
        return self._get("/v1/OpenedOrders", {"id": account})

    def order_send(self, account, operation: str, symbol: str, volume: float,
                   sl: float | None = None, tp: float | None = None, price: float | None = None,
                   slippage: float | None = None, magic: int | None = None,
                   comment: str | None = None) -> dict:
        """
        Place a market order (``operation`` = ``Buy``/``Sell``) or a pending order
        (``BuyLimit``/``SellLimit``/``BuyStop``/``SellStop``/``BuyStopLimit``/``SellStopLimit``,
        which also needs ``price``). Raises :class:`TradeRailError` if the broker rejects it.
        """
        return self._get("/v1/OrderSendTask", {
            "id": account, "operation": operation, "symbol": symbol, "volume": volume,
            "stoploss": sl, "takeprofit": tp, "price": price, "slippage": slippage,
            "expertID": magic, "comment": comment,
        })

    def order_modify(self, account, ticket: int, sl: float | None = None,
                     tp: float | None = None, price: float | None = None) -> dict:
        """Change SL/TP of a position, or the entry price of a pending order, by ticket."""
        return self._get("/v1/OrderModifyTask", {"id": account, "ticket": ticket,
                                                  "stoploss": sl, "takeprofit": tp, "price": price})

    def order_close(self, account, ticket: int, lots: float | None = None,
                    slippage: float | None = None) -> dict:
        """Close a position fully, or partially by passing ``lots`` < the open volume."""
        return self._get("/v1/OrderCloseTask", {"id": account, "ticket": ticket,
                                                 "lots": lots, "slippage": slippage})

    # -- history & analytics -------------------------------------------------
    def order_history(self, account) -> dict:
        """Reconstructed closed trades over the default look-back window (newest first)."""
        return self._get("/v1/OrderHistory", {"id": account})

    def order_history_paginated(self, account, from_=None, to=None, sort="CloseTime",
                                ascending=False, page=0, per_page=100) -> dict:
        """Sortable, paginated closed trades over a ``from``/``to`` window."""
        return self._get("/v1/OrderHistoryPagination", {
            "id": account, "from": from_, "to": to, "sort": sort,
            "ascending": ascending, "pageNumber": page, "ordersPerPage": per_page,
        })

    def trade_stats(self, account, from_=None) -> dict:
        """Aggregate stats: win rate, profit factor, totals, net profit."""
        return self._get("/v1/TradeStats", {"id": account, "from": from_})

    def equity_history(self, account, from_=None) -> dict:
        """Equity / balance series reconstructed from deal history (equity-curve data)."""
        return self._get("/v1/EquityHistory", {"id": account, "from": from_})

    # -- copy-trade (needs a bearer token) -----------------------------------
    def bulk_order(self, operation: str, symbol: str, volume: float, sl: float | None = None,
                   tp: float | None = None, comment: str | None = None,
                   logins: list[int] | None = None) -> dict:
        """
        Fire ONE market order across many accounts at once (copy-trade). Omit ``logins`` to
        fan out to every connected account. Requires a bearer ``token`` on the client.
        """
        self._require_token()
        return self._post("/orchestrator/bulk-order", _clean({
            "operation": operation, "symbol": symbol, "volume": volume,
            "sl": sl, "tp": tp, "comment": comment, "logins": logins,
        }))

    def bulk_close(self, logins: list[int] | None = None) -> dict:
        """Close every open position across many accounts at once. Requires a bearer ``token``."""
        self._require_token()
        return self._post("/orchestrator/bulk-close", _clean({"logins": logins}))

    def _require_token(self):
        if not self.token:
            raise TradeRailError("a bearer token is required for copy-trade (/orchestrator) calls; "
                                 "pass token=... to TradeRail(...)")


# -- helpers ----------------------------------------------------------------
def _clean(params: dict | None) -> dict:
    """Drop None values so optional query params / body fields are omitted."""
    return {k: v for k, v in (params or {}).items() if v is not None}


def _parse(r: requests.Response):
    ctype = r.headers.get("content-type", "")
    is_json = "application/json" in ctype
    data = r.json() if is_json else r.text
    if r.status_code >= 400:
        msg = (data.get("message") if isinstance(data, dict) else None) or f"HTTP {r.status_code}"
        raise TradeRailError(msg, status=r.status_code, payload=data)
    # A rejected trade comes back as 200 with {"code": "ERROR", ...}
    if isinstance(data, dict) and data.get("code") == "ERROR":
        raise TradeRailError(data.get("message") or "request rejected", status=r.status_code, payload=data)
    return data
