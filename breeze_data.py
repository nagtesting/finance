"""
breeze_data.py  ─  MoneyVeda ICICI Breeze derivatives layer (v1.0)
====================================================================
A standalone, FAIL-CLOSED data module that adds futures / options /
open-interest depth to market_commentary.py via the ICICI Breeze API.

DESIGN CONTRACT (read this before changing anything):
  • This module must NEVER raise into the commentary cron. Every public
    function returns a safe empty value ({} / None) on ANY failure and
    logs the reason. A Breeze outage, an expired token, a bad symbol, a
    rate-limit, an SDK import error — all degrade silently to "no
    derivatives this tick", exactly like every other fetcher in the
    commentary system degrades to {}.
  • It is import-isolated. market_commentary.py should `from breeze_data
    import get_derivatives` INSIDE a try/except (lazy), so a missing
    breeze-connect dependency cannot import-fail the commentary module.

AUTH MODEL (manual daily refresh — validation phase):
  • You generate a fresh Breeze session token each morning (~07:45 IST)
    by tapping the login bookmark, authenticating with OTP, and letting
    your admin page write the token to a Supabase table `breeze_session`.
  • The token expires at midnight, so a 07:45 token covers the whole
    trading day (08:00 pre → 17:00 post). This module reads the token
    from Supabase and REFUSES to use it if its stored date is not today
    (IST) — a stale token can only ever mean "no derivatives", never a
    crash or, worse, silently-wrong stale data.

SCOPE (deliberate, rate-limit aware):
  • Breeze limit is 100 calls/min and 5000 calls/day. We do NOT fetch all
    100 constituents. We fetch a SMALL set of underlyings — the indices
    plus the day's top movers — at ~3 calls each. ~12 underlyings ≈ 36
    calls/tick, well inside the budget.

SYMBOL MAPPING:
  • ICICI uses its own short codes (RELIANCE→RELIND, etc). We do NOT
    hand-maintain that table (that's how you map SHRIRAMFIN to the wrong
    company). We resolve at runtime via breeze.get_names(), cached.

WHAT IT RETURNS (per underlying, best-effort, any field may be None):
  spot, future_ltp, future_pct, basis, basis_pct,
  call_oi_total, put_oi_total, pcr_oi,
  atm_strike, max_call_oi_strike (resistance wall),
  max_put_oi_strike (support wall), expiry_used, source/status.

KNOWN UNCERTAINTIES (validate with `python breeze_data.py`):
  • Breeze field names vary across SDK versions. Extraction below tries
    several key spellings and is tolerant of str-vs-float. Run the
    self-test against the LIVE API and confirm the parsed block matches
    the raw block before trusting the numbers in production.
  • Futures get_quotes does not reliably return open-interest; the
    options-chain OI is the dependable signal. Treat future OI as bonus.
  • Monthly-expiry weekday rules change via NSE circulars; we try several
    candidate expiries and use the first that returns data, so a rule
    change self-heals (worst case: that underlying degrades to {}).
"""

from __future__ import annotations

import os
import time
import calendar
from datetime import datetime, timedelta, timezone

# ── Analytics add-ons (greeks.py + oi_history.py). Import-isolated: if either
#    module is absent or import-fails, we fall back to no-ops so the derivatives
#    path keeps working (fail-closed, same discipline as the rest of this file).
try:
    from greeks import compute_option_analytics
except Exception as _e:                                    # pragma: no cover
    def compute_option_analytics(*_a, **_k):
        return {"available": False, "reason": "greeks.py unavailable"}
try:
    from oi_history import process_oi
except Exception as _e:                                    # pragma: no cover
    def process_oi(*_a, **_k):
        return {"available": False}

# ── Conventions mirrored from market_commentary.py ───────────────────────────
IST = timezone(timedelta(hours=5, minutes=30))


def _log(emoji: str, msg: str) -> None:
    print(f"{emoji}  [{datetime.now(IST).strftime('%H:%M:%S')}]  {msg}")


# ── Config ───────────────────────────────────────────────────────────────────
BREEZE_API_KEY     = os.getenv("BREEZE_API_KEY")
BREEZE_API_SECRET  = os.getenv("BREEZE_API_SECRET")
# Optional local-testing escape hatch; production reads the token from Supabase.
BREEZE_SESSION_ENV = os.getenv("BREEZE_SESSION_TOKEN")

SUPABASE_URL        = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

# Matches the admin page / token-writer: a single canonical row in
# `api_sessions` keyed by id = "icici_breeze".
BREEZE_SESSION_TABLE  = "api_sessions"
BREEZE_SESSION_ROW_ID = "icici_breeze"

# Rate-limit pacing: 100 calls/min ⇒ ≥0.6s/call. 0.7s gives headroom.
_RATE_SLEEP = float(os.getenv("BREEZE_RATE_SLEEP", "0.7"))

# How far around ATM to scan strikes when summing OI for indices/stocks.
# We sum the WHOLE returned chain anyway; this only bounds the ATM search.
_INDEX_STRIKE_STEP = {"NIFTY": 50, "BANKNIFTY": 100, "NIFTYIT": 100}

# Map Yahoo index tickers → (breeze spot stock_code, breeze NFO underlying).
# Stocks are NOT listed here — they are resolved dynamically via get_names().
# NOTE: Breeze uses its own ISEC code as the NFO stock_code too — NOT the NSE
# trading symbol. Bank Nifty futures/options are queried as "CNXBAN" (passing
# "BANKNIFTY" returns the T10:56 service error seen in the logs); Nifty IT as
# "CNXIT". The spot code and the NFO code are therefore the same here.
_INDEX_MAP = {
    "^NSEI":     ("NIFTY",  "NIFTY"),
    "^NSEBANK":  ("CNXBAN", "CNXBAN"),
    "^CNXIT":    ("CNXIT",  "CNXIT"),
    "^NSEIT":    ("CNXIT",  "CNXIT"),
}


# ─────────────────────────────────────────────────────────────────────────────
# Small tolerant coercion helpers (Breeze returns numbers as strings a lot)
# ─────────────────────────────────────────────────────────────────────────────
def _f(v):
    """Best-effort float; None on failure."""
    try:
        if v is None or v == "":
            return None
        return float(str(v).replace(",", ""))
    except Exception:
        return None


def _i(v):
    """Best-effort int; None on failure."""
    f = _f(v)
    return int(f) if f is not None else None


def _first(d: dict, *keys):
    """Return the first present, non-empty value among several key spellings."""
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return None


# ─────────────────────────────────────────────────────────────────────────────
# SESSION TOKEN — read from Supabase with a same-IST-day staleness guard
# ─────────────────────────────────────────────────────────────────────────────
def _load_session_token() -> str | None:
    """
    Returns today's Breeze session token, or None.
    Order of preference:
      1. Supabase `breeze_session` latest row, IF its date == today (IST).
      2. BREEZE_SESSION_TOKEN env var (local testing only — no date check).
    A token whose stored date is not today is treated as ABSENT (refusing
    a midnight-expired token is the whole point of the guard).
    """
    # 1) Supabase (production path)
    if SUPABASE_URL and SUPABASE_SECRET_KEY:
        try:
            from supabase import create_client
            sb = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)
            res = (
                sb.table(BREEZE_SESSION_TABLE)
                .select("session_token, updated_at")
                .eq("id", BREEZE_SESSION_ROW_ID)
                .limit(1)
                .execute()
            )
            rows = res.data or []
            if rows:
                row = rows[0]
                token = (row.get("session_token") or "").strip()
                updated_at = row.get("updated_at")
                if token and _is_today_ist(updated_at):
                    _log("🔑", "Breeze session token loaded from Supabase (today).")
                    return token
                if token:
                    _log("🗓", f"Breeze token in Supabase is stale "
                              f"(updated_at={updated_at}) — refusing it. "
                              f"Generate a fresh token this morning.")
                else:
                    _log("🗓", "No session_token value in breeze_session row.")
            else:
                _log("🗓", f"api_sessions has no '{BREEZE_SESSION_ROW_ID}' row "
                          f"— no token to load.")
        except Exception as e:
            _log("⚠️", f"Breeze token Supabase read failed: {e}")

    # 2) Env fallback (local dev)
    if BREEZE_SESSION_ENV:
        _log("🔑", "Breeze session token loaded from env (local-dev fallback).")
        return BREEZE_SESSION_ENV.strip()

    return None


def _is_today_ist(updated_at) -> bool:
    """True iff `updated_at` (ISO string or datetime) falls on today's IST date."""
    if not updated_at:
        return False
    try:
        if isinstance(updated_at, datetime):
            dt = updated_at
        else:
            s = str(updated_at).replace("Z", "+00:00")
            dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            # Assume UTC if Supabase stored a naive timestamp.
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(IST).date() == datetime.now(IST).date()
    except Exception as e:
        _log("⚠️", f"Could not parse token timestamp '{updated_at}': {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# CONNECTION — lazy, singleton, fail-closed
# ─────────────────────────────────────────────────────────────────────────────
_breeze = None          # cached BreezeConnect instance
_breeze_ready = False    # True once generate_session succeeded this process


def _connect():
    """
    Returns a session-authenticated BreezeConnect instance, or None.
    Cached for the life of the process. Any failure → None (caller degrades).
    """
    global _breeze, _breeze_ready
    if _breeze_ready and _breeze is not None:
        return _breeze

    if not (BREEZE_API_KEY and BREEZE_API_SECRET):
        _log("⚠️", "BREEZE_API_KEY / BREEZE_API_SECRET not set — skipping Breeze.")
        return None

    token = _load_session_token()
    if not token:
        _log("⚠️", "No usable Breeze session token — skipping derivatives.")
        return None

    try:
        from breeze_connect import BreezeConnect   # lazy import
    except Exception as e:
        _log("⚠️", f"breeze-connect not importable ({e}) — skipping derivatives.")
        return None

    try:
        bz = BreezeConnect(api_key=BREEZE_API_KEY)
        bz.generate_session(api_secret=BREEZE_API_SECRET, session_token=token)
        _breeze = bz
        _breeze_ready = True
        _log("✅", "Breeze session established.")
        return _breeze
    except Exception as e:
        _log("⚠️", f"Breeze generate_session failed: {e} — skipping derivatives.")
        _breeze = None
        _breeze_ready = False
        return None


# ─────────────────────────────────────────────────────────────────────────────
# SYMBOL RESOLUTION — Yahoo ticker → (breeze_spot_code, nfo_underlying, kind)
# ─────────────────────────────────────────────────────────────────────────────
_name_cache: dict[str, str] = {}


def _resolve_codes(yahoo: str) -> tuple[str | None, str | None, str]:
    """
    Returns (spot_code, nfo_underlying, kind) where kind is 'index'|'stock'.
    Indices use the static _INDEX_MAP (their codes are fixed & special).
    Stocks are resolved via breeze.get_names() and cached.
    """
    if yahoo in _INDEX_MAP:
        spot, nfo = _INDEX_MAP[yahoo]
        return spot, nfo, "index"

    nse_symbol = yahoo.replace(".NS", "").strip().upper()
    if not nse_symbol:
        return None, None, "stock"

    if nse_symbol in _name_cache:
        code = _name_cache[nse_symbol]
        return code, code, "stock"

    bz = _connect()
    if bz is None:
        return None, None, "stock"

    try:
        names = bz.get_names(exchange_code="NSE", stock_code=nse_symbol)
        # get_names returns a dict; the ICICI code key varies by SDK version.
        code = None
        if isinstance(names, dict):
            code = _first(names,
                          "isec_stock_code", "ISEC_stock_code",
                          "stock_code", "isec_stock", "exchange_stock_code")
        if not code:
            _log("⚠️", f"get_names returned no ISEC code for {nse_symbol}: {names}")
            # Last resort: try the raw NSE symbol as the code (often works).
            code = nse_symbol
        code = str(code).strip().upper()
        _name_cache[nse_symbol] = code
        return code, code, "stock"
    except Exception as e:
        _log("⚠️", f"get_names failed for {nse_symbol}: {e}")
        return None, None, "stock"


# ─────────────────────────────────────────────────────────────────────────────
# EXPIRY DISCOVERY — try candidate monthly expiries, self-heal on rule changes
# ─────────────────────────────────────────────────────────────────────────────
def _last_weekday_of_month(year: int, month: int, weekday: int) -> datetime:
    """weekday: Mon=0 … Sun=6. Returns the last such weekday of the month."""
    last_day = calendar.monthrange(year, month)[1]
    d = datetime(year, month, last_day, tzinfo=IST)
    while d.weekday() != weekday:
        d -= timedelta(days=1)
    return d


def _expiry_candidates() -> list[str]:
    """
    Ordered ISO8601 monthly-futures expiry strings to try, nearest first.

    Single-stock and index FUTURES are MONTHLY-only (there is no weekly futures
    contract), so we only ever need monthly expiries here. Since NSE circular
    NSE/FAOP/68747 (effective 2025-09-01), the monthly expiry for NIFTY,
    BANKNIFTY, FINNIFTY, MIDCPNIFTY, NIFTYNXT50 and single stocks is the LAST
    TUESDAY of the expiry month (it was the last Thursday before that date —
    the old Thursday logic is why every futures fetch returned "No Data Found").

    Strategy (self-healing):
      • Primary: last Tuesday of this + next two months.
      • Fallbacks: last Monday (covers a Tuesday-holiday shift to prev session),
        then last Wednesday / Thursday (covers any future NSE weekday change).
    The first candidate that actually returns futures data wins and is cached
    per process by the caller, so the fallbacks cost nothing on normal days.
    """
    now = datetime.now(IST)
    today = now.date()
    seen: set = set()
    ordered: list = []

    def _add(d):
        if d >= today and d not in seen:
            seen.add(d)
            ordered.append(d)

    def _month(delta_month: int):
        y = now.year + (now.month - 1 + delta_month) // 12
        m = (now.month - 1 + delta_month) % 12 + 1
        return y, m

    # Primary: last TUESDAY of this + next two months (correct monthly expiry).
    for dm in (0, 1, 2):
        y, m = _month(dm)
        _add(_last_weekday_of_month(y, m, calendar.TUESDAY).date())

    # Fallbacks: holiday-shift (Mon) + future rule-change safety (Wed, Thu).
    for dm in (0, 1, 2):
        y, m = _month(dm)
        for wd in (calendar.MONDAY, calendar.WEDNESDAY, calendar.THURSDAY):
            _add(_last_weekday_of_month(y, m, wd).date())

    return [d.strftime("%Y-%m-%dT06:00:00.000Z") for d in ordered]


# ─────────────────────────────────────────────────────────────────────────────
# RAW FETCHERS (each wraps one or two Breeze calls, fail-closed)
# ─────────────────────────────────────────────────────────────────────────────
def _success_rows(resp) -> list:
    """Normalise a Breeze response to a list of row-dicts (or [])."""
    if not isinstance(resp, dict):
        return []
    rows = resp.get("Success")
    return rows if isinstance(rows, list) else []


def _fetch_future(bz, nfo_underlying: str, expiry_iso: str) -> dict:
    """One get_quotes futures call. Returns {} on miss."""
    try:
        time.sleep(_RATE_SLEEP)
        resp = bz.get_quotes(
            stock_code=nfo_underlying, exchange_code="NFO",
            product_type="futures", expiry_date=expiry_iso,
            right="others", strike_price="0",
        )
        rows = _success_rows(resp)
        if not rows:
            # Log the raw response (truncated) so we can see what Breeze returned.
            raw_preview = str(resp)[:300] if resp is not None else "None"
            _log("⚠️", f"Futures empty [{nfo_underlying} {expiry_iso[:10]}]: {raw_preview}")
            return {}
        r = rows[0]
        return {
            "future_ltp":  _f(_first(r, "ltp", "last_price")),
            "future_pct":  _f(_first(r, "ltp_percent_change", "change_percentage")),
            "spot":        _f(_first(r, "spot_price")),
            "future_oi":   _i(_first(r, "open_interest", "oi", "OI")),  # best-effort
        }
    except Exception as e:
        _log("⚠️", f"Futures fetch failed [{nfo_underlying} {expiry_iso[:10]}]: {e}")
        return {}


def _fetch_option_side(bz, nfo_underlying: str, expiry_iso: str, right: str) -> list:
    """One get_option_chain_quotes call for one side. Returns list of rows."""
    try:
        time.sleep(_RATE_SLEEP)
        resp = bz.get_option_chain_quotes(
            stock_code=nfo_underlying, exchange_code="NFO",
            product_type="options", right=right,
            strike_price="", expiry_date=expiry_iso,
        )
        rows = _success_rows(resp)
        if not rows:
            raw_preview = str(resp)[:300] if resp is not None else "None"
            _log("⚠️", f"Option chain ({right}) empty [{nfo_underlying} {expiry_iso[:10]}]: {raw_preview}")
        return rows
    except Exception as e:
        _log("⚠️", f"Option chain ({right}) failed [{nfo_underlying} {expiry_iso[:10]}]: {e}")
        return []


def _summarise_chain(call_rows: list, put_rows: list, spot: float | None) -> dict:
    """Compute total OI, PCR, ATM, and max-OI support/resistance walls."""
    def oi_of(row):
        return _i(_first(row, "open_interest", "oi", "OI")) or 0

    def strike_of(row):
        return _f(_first(row, "strike_price", "strike"))

    call_oi_total = sum(oi_of(r) for r in call_rows)
    put_oi_total  = sum(oi_of(r) for r in put_rows)

    pcr = round(put_oi_total / call_oi_total, 2) if call_oi_total else None

    def max_oi_strike(rows):
        best, best_oi = None, -1
        for r in rows:
            o, s = oi_of(r), strike_of(r)
            if s is not None and o > best_oi:
                best, best_oi = s, o
        return best

    max_call_strike = max_oi_strike(call_rows)   # overhead resistance wall
    max_put_strike  = max_oi_strike(put_rows)     # downside support wall

    atm = None
    if spot is not None:
        strikes = sorted({strike_of(r) for r in (call_rows + put_rows)
                          if strike_of(r) is not None})
        if strikes:
            atm = min(strikes, key=lambda s: abs(s - spot))

    return {
        "call_oi_total":      call_oi_total or None,
        "put_oi_total":       put_oi_total or None,
        "pcr_oi":             pcr,
        "atm_strike":         atm,
        "max_call_oi_strike": max_call_strike,   # resistance
        "max_put_oi_strike":  max_put_strike,    # support
        "strikes_seen":       len(call_rows) + len(put_rows),
    }


# ─────────────────────────────────────────────────────────────────────────────
# PER-UNDERLYING ORCHESTRATION
# ─────────────────────────────────────────────────────────────────────────────
def _fetch_one(bz, label: str, yahoo: str, expiry_cache: dict) -> dict | None:
    """
    Fetch futures + option-chain metrics for one underlying.
    Returns a metrics dict, or None if nothing usable was retrieved.
    `expiry_cache` maps nfo_underlying → working expiry_iso (filled lazily).
    """
    spot_code, nfo, kind = _resolve_codes(yahoo)
    if not nfo:
        _log("⚠️", f"No NFO code resolved for {label} ({yahoo}) — skipping.")
        return None

    # Pick / reuse a working expiry for this underlying.
    expiries = [expiry_cache[nfo]] if nfo in expiry_cache else _expiry_candidates()
    _log("🔍", f"Fetching {label} ({nfo}) — expiries: {[e[:10] for e in expiries]}")
    if not expiries:
        _log("⚠️", f"No future expiry candidates for {label} ({nfo}).")
        return None

    fut, used_expiry = {}, None
    for exp in expiries:
        fut = _fetch_future(bz, nfo, exp)
        if fut:
            used_expiry = exp
            break
    if used_expiry is None:
        _log("⚠️", f"No futures data for {label} ({nfo}) across "
                   f"{len(expiries)} expiry candidate(s).")
        return None
    expiry_cache[nfo] = used_expiry

    spot = fut.get("spot")
    call_rows = _fetch_option_side(bz, nfo, used_expiry, "call")
    put_rows  = _fetch_option_side(bz, nfo, used_expiry, "put")

    # ΔOI vs the previous stored tick: annotates call_rows/put_rows in place with
    # "change_in_oi" (so compute_option_analytics picks it up automatically) and
    # classifies the futures price/OI buildup. Safe no-op if Supabase/state absent.
    oi_flow = process_oi(
        nfo, used_expiry, call_rows, put_rows,
        future_ltp=fut.get("future_ltp"),
        future_oi=fut.get("future_oi"),
    )

    chain  = _summarise_chain(call_rows, put_rows, spot)
    greeks = compute_option_analytics(call_rows, put_rows, spot, used_expiry)

    basis = basis_pct = None
    if fut.get("future_ltp") is not None and spot:
        basis = round(fut["future_ltp"] - spot, 2)
        basis_pct = round(basis / spot * 100, 3)

    metrics = {
        "label":       label,
        "yahoo":       yahoo,
        "breeze_code": nfo,
        "kind":        kind,
        "expiry_used": used_expiry[:10],   # human-readable date part
        "spot":        spot,
        **{k: fut.get(k) for k in ("future_ltp", "future_pct", "future_oi")},
        "basis":       basis,
        "basis_pct":   basis_pct,
        **chain,
        "greeks":      greeks,
        "oi_flow":     oi_flow,
        "status":      "ok",
    }
    return metrics


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC ENTRYPOINT
# ─────────────────────────────────────────────────────────────────────────────
def get_derivatives(underlyings: list[dict], max_underlyings: int = 14) -> dict:
    """
    The one function market_commentary.py calls.

    Args:
      underlyings: list of {"label": str, "yahoo": str} dicts. Indices use a
                   Yahoo ticker like "^NSEI"/"^NSEBANK"; stocks use "XXX.NS".
                   Pass indices + the day's movers (NOT all 100 constituents).
      max_underlyings: hard cap to protect the daily rate budget.

    Returns:
      {} on total failure (no Breeze, no token, etc.), else:
      {
        "asof": "YYYY-MM-DD HH:MM IST",
        "source": "ICICI_Breeze",
        "underlyings": [ <metrics dict>, ... ],   # only successful ones
        "count": int,
      }
    NEVER raises.
    """
    try:
        if not underlyings:
            return {}
        bz = _connect()
        if bz is None:
            return {}

        wanted = underlyings[:max_underlyings]
        out, expiry_cache = [], {}
        for u in wanted:
            try:
                label = u.get("label") or u.get("yahoo") or "?"
                yahoo = u.get("yahoo")
                if not yahoo:
                    continue
                m = _fetch_one(bz, label, yahoo, expiry_cache)
                if m:
                    out.append(m)
            except Exception as e:
                _log("⚠️", f"Derivatives fetch errored for {u}: {e}")
                continue

        if not out:
            _log("⚠️", "Breeze returned no usable derivatives this tick.")
            return {}

        _log("📊", f"Breeze derivatives: {len(out)}/{len(wanted)} underlyings "
                   f"resolved.")
        return {
            "asof":   _now_ist_str(),
            "source": "ICICI_Breeze",
            "underlyings": out,
            "count":  len(out),
        }
    except Exception as e:
        # Absolute backstop — this module must never propagate an exception.
        _log("⚠️", f"get_derivatives hard failure (returning {{}}): {e}")
        return {}


def _now_ist_str() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")


# ─────────────────────────────────────────────────────────────────────────────
# SELF-TEST  ─  run `python breeze_data.py` locally with env vars set.
# Prints BOTH the raw first-row payloads and the parsed metrics so you can
# confirm field names against the live API before wiring into the cron.
# ─────────────────────────────────────────────────────────────────────────────
def _selftest():
    import json
    print("=" * 70)
    print("BREEZE_DATA SELF-TEST")
    print(f"  api_key set:    {bool(BREEZE_API_KEY)}")
    print(f"  api_secret set: {bool(BREEZE_API_SECRET)}")
    print(f"  supabase set:   {bool(SUPABASE_URL and SUPABASE_SECRET_KEY)}")
    print(f"  session env:    {bool(BREEZE_SESSION_ENV)}")
    print("=" * 70)

    bz = _connect()
    if bz is None:
        print("❌ Could not establish a Breeze session. "
              "Check token / api_key / api_secret and retry.")
        return

    # Show one raw futures payload + one raw option row so key names are visible.
    exp = _expiry_candidates()
    print(f"\nExpiry candidates tried (first that returns data wins):\n  {exp}\n")
    for exp_iso in exp:
        try:
            time.sleep(_RATE_SLEEP)
            raw_fut = bz.get_quotes(stock_code="NIFTY", exchange_code="NFO",
                                    product_type="futures", expiry_date=exp_iso,
                                    right="others", strike_price="0")
            rows = _success_rows(raw_fut)
            if rows:
                print(f"--- RAW NIFTY FUTURES ROW (expiry {exp_iso[:10]}) ---")
                print(json.dumps(rows[0], indent=2, default=str))
                time.sleep(_RATE_SLEEP)
                raw_ce = bz.get_option_chain_quotes(
                    stock_code="NIFTY", exchange_code="NFO",
                    product_type="options", right="call",
                    strike_price="", expiry_date=exp_iso)
                ce_rows = _success_rows(raw_ce)
                if ce_rows:
                    print("\n--- RAW NIFTY CALL OPTION ROW ---")
                    print(json.dumps(ce_rows[0], indent=2, default=str))
                break
        except Exception as e:
            print(f"(expiry {exp_iso[:10]} raw probe failed: {e})")

    # Now exercise the full public path on a tiny representative set.
    sample = [
        {"label": "NIFTY 50",  "yahoo": "^NSEI"},
        {"label": "NIFTY BANK", "yahoo": "^NSEBANK"},
        {"label": "Reliance",  "yahoo": "RELIANCE.NS"},
    ]
    print("\n" + "=" * 70)
    print("PARSED get_derivatives() OUTPUT")
    print("=" * 70)
    result = get_derivatives(sample)
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    _selftest()
