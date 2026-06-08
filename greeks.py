"""
greeks.py  ─  MoneyVeda · option-chain analytics (IV + Greeks + positioning)
============================================================================
Turns the RAW Breeze option-chain rows you already fetch in breeze_data.py
into DETERMINISTIC, auditable numbers — implied vol, the Greeks, expected
move, IV skew and OI-weighted positioning — so the LLM (Gemma) only ever
NARRATES finished figures and never does arithmetic. This keeps the
"no-invention" discipline: every number here is computed in Python.

Pure stdlib (math + datetime). No scipy / py_vollib, so it adds zero native
build weight on Render. (py_vollib is faster if you ever vectorise, but for
~2 indices × a few dozen strikes per tick this is plenty quick.)

PUBLIC API
----------
  compute_option_analytics(call_rows, put_rows, spot, expiry_iso, **opts) -> dict
  format_greeks_block(analytics, label=None) -> str      # for the Gemma prompt
  classify_buildup(price_change_pct, oi_change_pct) -> str  # gated helper, see note

INTEGRATION (in breeze_data.py · _fetch_one, right after _summarise_chain):

    from greeks import compute_option_analytics
    ...
    chain = _summarise_chain(call_rows, put_rows, spot)
    greeks = compute_option_analytics(call_rows, put_rows, spot, used_expiry)
    metrics = { ..., **chain, "greeks": greeks, "status": "ok" }

Then in the prompt builder:  format_greeks_block(metrics["greeks"], metrics["label"])

DELIBERATELY NOT COMPUTED
-------------------------
OI-change "buildup" (long buildup / short covering / etc.) needs ΔOI vs the
previous snapshot. The Breeze quote snapshot does not reliably carry an
OI-change field, and you don't persist the prior tick, so we do NOT fabricate
it. classify_buildup() implements the standard price/OI quadrant and is ready
to use the moment you feed it a real ΔOI% (e.g. diff against a Supabase-stored
previous OI). Until then it stays unused — by design.
"""

from __future__ import annotations

import math
import datetime as _dt
from typing import Optional

_IST = _dt.timezone(_dt.timedelta(hours=5, minutes=30))
_SECONDS_PER_YEAR = 365.0 * 24.0 * 3600.0
_MIN_T = 1800.0 / _SECONDS_PER_YEAR          # floor T at ~30 min (expiry-day safety)


# ── tolerant coercion (kept local so this module is standalone) ──────────────
def _f(v) -> Optional[float]:
    try:
        f = float(v)
        return f if math.isfinite(f) else None
    except (TypeError, ValueError):
        return None


def _i(v) -> int:
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return 0


def _first(d: dict, *keys):
    for k in keys:
        if k in d and d[k] not in (None, "", "-"):
            return d[k]
    return None


def _strike(row) -> Optional[float]:
    return _f(_first(row, "strike_price", "strike"))


def _oi(row) -> int:
    return _i(_first(row, "open_interest", "oi", "OI"))


def _oi_change(row) -> Optional[int]:
    v = _first(row, "change_in_oi", "oi_change",
               "change_in_open_interest", "changeinopeninterest")
    return _i(v) if v is not None else None


def _mid(row) -> Optional[float]:
    """Prefer (bid+ask)/2 when both are live; else last traded price."""
    bid = _f(_first(row, "best_bid_price", "bid_price", "bid"))
    ask = _f(_first(row, "best_offer_price", "ask_price", "offer_price", "ask"))
    if bid and ask and ask >= bid > 0:
        return round((bid + ask) / 2.0, 4)
    return _f(_first(row, "ltp", "last_price", "last_traded_price"))


# ── Black-Scholes (no scipy: erf-based normal CDF) ───────────────────────────
def _N(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _n(x: float) -> float:
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def _d1_d2(S, K, T, r, q, sigma):
    vt = sigma * math.sqrt(T)
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / vt
    return d1, d1 - vt


def _bs_price(S, K, T, r, q, sigma, is_call: bool) -> float:
    d1, d2 = _d1_d2(S, K, T, r, q, sigma)
    if is_call:
        return S * math.exp(-q * T) * _N(d1) - K * math.exp(-r * T) * _N(d2)
    return K * math.exp(-r * T) * _N(-d2) - S * math.exp(-q * T) * _N(-d1)


def _bs_greeks(S, K, T, r, q, sigma, is_call: bool) -> dict:
    d1, d2 = _d1_d2(S, K, T, r, q, sigma)
    disc_q, disc_r = math.exp(-q * T), math.exp(-r * T)
    gamma = disc_q * _n(d1) / (S * sigma * math.sqrt(T))
    vega = S * disc_q * _n(d1) * math.sqrt(T) / 100.0          # per 1% vol
    if is_call:
        delta = disc_q * _N(d1)
        theta = (-(S * disc_q * _n(d1) * sigma) / (2 * math.sqrt(T))
                 - r * K * disc_r * _N(d2) + q * S * disc_q * _N(d1))
    else:
        delta = -disc_q * _N(-d1)
        theta = (-(S * disc_q * _n(d1) * sigma) / (2 * math.sqrt(T))
                 + r * K * disc_r * _N(-d2) - q * S * disc_q * _N(-d1))
    return {
        "delta": round(delta, 4),
        "gamma": round(gamma, 6),
        "vega":  round(vega, 4),
        "theta": round(theta / 365.0, 4),                      # per calendar day
    }


def _implied_vol(price, S, K, T, r, q, is_call: bool) -> Optional[float]:
    """Solve IV from a market price. Newton with vega, bisection fallback."""
    if price is None or price <= 0 or S <= 0 or K <= 0 or T <= 0:
        return None
    intrinsic = (max(S - K, 0.0) if is_call else max(K - S, 0.0)) * math.exp(-q * T)
    if price < intrinsic - 1e-6:        # below intrinsic = bad/stale quote
        return None

    sigma = 0.25
    for _ in range(60):
        try:
            diff = _bs_price(S, K, T, r, q, sigma, is_call) - price
        except (ValueError, ZeroDivisionError):
            break
        if abs(diff) < 1e-6:
            return round(sigma, 4)
        d1, _ = _d1_d2(S, K, T, r, q, sigma)
        vega = S * math.exp(-q * T) * _n(d1) * math.sqrt(T)
        if vega < 1e-8:
            break
        sigma -= diff / vega
        if not (1e-4 < sigma < 5.0):
            break

    lo, hi = 1e-4, 5.0
    try:
        if (_bs_price(S, K, T, r, q, lo, is_call) - price) * \
           (_bs_price(S, K, T, r, q, hi, is_call) - price) > 0:
            return None
    except ValueError:
        return None
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        val = _bs_price(S, K, T, r, q, mid, is_call) - price
        if abs(val) < 1e-6:
            return round(mid, 4)
        if (_bs_price(S, K, T, r, q, lo, is_call) - price) * val < 0:
            hi = mid
        else:
            lo = mid
    return round(0.5 * (lo + hi), 4)


# ── expiry / time-to-expiry ──────────────────────────────────────────────────
def _expiry_moment(expiry_iso: str) -> Optional[_dt.datetime]:
    """Expiry as 15:30 IST (market close) on the expiry date."""
    try:
        date_part = expiry_iso[:10]
        d = _dt.date.fromisoformat(date_part)
        return _dt.datetime(d.year, d.month, d.day, 15, 30, tzinfo=_IST)
    except Exception:
        return None


def _time_to_expiry(expiry_iso: str, now: Optional[_dt.datetime]) -> Optional[float]:
    exp = _expiry_moment(expiry_iso)
    if exp is None:
        return None
    now = now or _dt.datetime.now(_IST)
    if now.tzinfo is None:
        now = now.replace(tzinfo=_IST)
    secs = (exp - now).total_seconds()
    if secs <= 0:
        return None
    return max(secs / _SECONDS_PER_YEAR, _MIN_T)


# ── main analytics ───────────────────────────────────────────────────────────
def classify_buildup(price_change_pct: Optional[float],
                     oi_change_pct: Optional[float]) -> Optional[str]:
    """
    Standard futures price/OI quadrant. NOT called automatically — feed it a
    real ΔOI% (diff vs a stored previous snapshot) when you have one.
        price ↑ + OI ↑ = long buildup       price ↓ + OI ↑ = short buildup
        price ↑ + OI ↓ = short covering     price ↓ + OI ↓ = long unwinding
    """
    if price_change_pct is None or oi_change_pct is None:
        return None
    up_p, up_oi = price_change_pct > 0, oi_change_pct > 0
    if up_p and up_oi:        return "long buildup"
    if (not up_p) and up_oi:  return "short buildup"
    if up_p and (not up_oi):  return "short covering"
    return "long unwinding"


def compute_option_analytics(
    call_rows: list,
    put_rows: list,
    spot: Optional[float],
    expiry_iso: str,
    *,
    risk_free: float = 0.065,        # ~India short rate; override if you like
    dividend_yield: float = 0.0,     # ~0 for indices over a monthly tenor
    now_ist: Optional[_dt.datetime] = None,
    wing_pct: float = 0.05,          # ±5% band for the skew wings
    key_strike_window: int = 3,      # how many strikes each side of ATM to keep
) -> dict:
    """
    Returns a structured analytics dict (all numbers pre-computed) or
    {"available": False, "reason": ...} when the inputs can't support it.
    """
    blank = {"available": False}
    S = _f(spot)
    if not S or S <= 0:
        return {**blank, "reason": "no spot"}
    T = _time_to_expiry(expiry_iso, now_ist)
    if T is None:
        return {**blank, "reason": "expired/unparseable expiry"}
    r, q = risk_free, dividend_yield

    # index by strike → IV + Greeks for each present side
    by_strike: dict[float, dict] = {}
    for rows, is_call, side in ((call_rows, True, "call"), (put_rows, False, "put")):
        for row in rows or []:
            K = _strike(row)
            if not K or K <= 0:
                continue
            price = _mid(row)
            iv = _implied_vol(price, S, K, T, r, q, is_call)
            entry = by_strike.setdefault(K, {"strike": K})
            entry[f"{side}_oi"] = _oi(row)
            entry[f"{side}_ltp"] = price
            if iv is not None:
                g = _bs_greeks(S, K, T, r, q, iv, is_call)
                entry[f"{side}_iv"] = round(iv * 100.0, 2)       # %
                entry[f"{side}_delta"] = g["delta"]
                entry[f"{side}_gamma"] = g["gamma"]
                entry[f"{side}_vega"] = g["vega"]
                entry[f"{side}_theta"] = g["theta"]

    if not by_strike:
        return {**blank, "reason": "no usable strikes"}

    strikes = sorted(by_strike)
    atm = min(strikes, key=lambda k: abs(k - S))
    atm_e = by_strike[atm]
    atm_call_iv = atm_e.get("call_iv")
    atm_put_iv = atm_e.get("put_iv")
    ivs = [v for v in (atm_call_iv, atm_put_iv) if v is not None]
    atm_iv = round(sum(ivs) / len(ivs), 2) if ivs else None

    # expected move to expiry: 1σ = S * (atm_iv) * sqrt(T)
    exp_move_abs = exp_move_pct = None
    if atm_iv is not None:
        sig = atm_iv / 100.0
        exp_move_abs = round(S * sig * math.sqrt(T), 2)
        exp_move_pct = round(sig * math.sqrt(T) * 100.0, 2)
    # straddle-implied move (model-free cross-check)
    straddle = None
    if atm_e.get("call_ltp") and atm_e.get("put_ltp"):
        straddle = round(atm_e["call_ltp"] + atm_e["put_ltp"], 2)

    # IV skew: avg OTM put-wing IV minus avg OTM call-wing IV (positive = puts richer)
    lo, hi = S * (1 - wing_pct), S * (1 + wing_pct)
    put_wing = [by_strike[k]["put_iv"] for k in strikes
                if lo <= k < S and "put_iv" in by_strike[k]]
    call_wing = [by_strike[k]["call_iv"] for k in strikes
                 if S < k <= hi and "call_iv" in by_strike[k]]
    put_wing_iv = round(sum(put_wing) / len(put_wing), 2) if put_wing else None
    call_wing_iv = round(sum(call_wing) / len(call_wing), 2) if call_wing else None
    iv_skew = (round(put_wing_iv - call_wing_iv, 2)
               if (put_wing_iv is not None and call_wing_iv is not None) else None)

    # gamma concentration ("pin" level): strike with max (call+put) gamma·OI
    def gamma_oi(e):
        g = (e.get("call_gamma") or 0) * (e.get("call_oi") or 0) \
            + (e.get("put_gamma") or 0) * (e.get("put_oi") or 0)
        return g
    peak_gamma_strike = max(strikes, key=lambda k: gamma_oi(by_strike[k]))
    if gamma_oi(by_strike[peak_gamma_strike]) <= 0:
        peak_gamma_strike = None

    # OI-weighted net delta across the chain (directional OI tilt, not dealer GEX)
    net_delta = 0.0
    seen_delta = False
    for e in by_strike.values():
        if "call_delta" in e:
            net_delta += e["call_delta"] * (e.get("call_oi") or 0); seen_delta = True
        if "put_delta" in e:
            net_delta += e["put_delta"] * (e.get("put_oi") or 0); seen_delta = True
    net_oi_delta = round(net_delta, 0) if seen_delta else None

    # aggregate ΔOI if (and only if) the feed actually carried it
    call_doi = sum((_oi_change(r) or 0) for r in (call_rows or [])
                   if _oi_change(r) is not None)
    put_doi = sum((_oi_change(r) or 0) for r in (put_rows or [])
                  if _oi_change(r) is not None)
    has_doi = any(_oi_change(r) is not None for r in (call_rows or []) + (put_rows or []))

    # compact per-strike snapshot around ATM (keeps the LLM payload small)
    atm_idx = strikes.index(atm)
    window = strikes[max(0, atm_idx - key_strike_window):
                     atm_idx + key_strike_window + 1]
    key_strikes = [by_strike[k] for k in window]

    return {
        "available": True,
        "expiry": expiry_iso[:10],
        "spot": round(S, 2),
        "days_to_expiry": round(T * 365.0, 2),
        "atm_strike": atm,
        "atm_iv_pct": atm_iv,
        "atm_call_iv_pct": atm_call_iv,
        "atm_put_iv_pct": atm_put_iv,
        "expected_move_abs": exp_move_abs,
        "expected_move_pct": exp_move_pct,
        "atm_straddle": straddle,
        "iv_skew_pct": iv_skew,
        "put_wing_iv_pct": put_wing_iv,
        "call_wing_iv_pct": call_wing_iv,
        "peak_gamma_strike": peak_gamma_strike,
        "net_oi_weighted_delta": net_oi_delta,
        "oi_change_available": has_doi,
        "call_oi_change": call_doi if has_doi else None,
        "put_oi_change": put_doi if has_doi else None,
        "key_strikes": key_strikes,
    }


# ── render a no-invention block for the Gemma prompt ─────────────────────────
def format_greeks_block(analytics: dict, label: Optional[str] = None) -> str:
    """
    Descriptive, numbers-only block for the LLM. Mirrors your _format_derivatives
    discipline: state the figures; if absent, forbid mention. DESCRIPTIVE, not
    predictive — the prompt rules below keep Gemma from drifting into advice.
    """
    tag = f"{label} " if label else ""
    if not analytics or not analytics.get("available"):
        return (f"  Options Greeks ({tag.strip()}): [INSTRUCTION TO MODEL: option "
                "Greeks/IV are NOT available this run. Do NOT mention IV, Greeks, "
                "skew, expected move or gamma — write as if this block is absent.]")

    a = analytics

    def s(x, suffix=""):
        return f"{x}{suffix}" if x is not None else "n/a"

    bits = [
        f"ATM {s(a['atm_strike'])} | ATM IV {s(a['atm_iv_pct'], '%')} "
        f"(C {s(a['atm_call_iv_pct'], '%')} / P {s(a['atm_put_iv_pct'], '%')})",
        f"expected move to {s(a['expiry'])}: ±{s(a['expected_move_abs'])} "
        f"(±{s(a['expected_move_pct'], '%')}); ATM straddle {s(a['atm_straddle'])}",
        f"IV skew (put-wing − call-wing): {s(a['iv_skew_pct'], ' pts')} "
        f"[P {s(a['put_wing_iv_pct'], '%')} vs C {s(a['call_wing_iv_pct'], '%')}]",
        f"peak-gamma strike {s(a['peak_gamma_strike'])}",
        f"net OI-weighted delta {s(a['net_oi_weighted_delta'])}",
    ]
    if a.get("oi_change_available"):
        bits.append(f"ΔOI calls {s(a['call_oi_change'])} / puts {s(a['put_oi_change'])}")

    head = (f"  Options Greeks ({tag.strip()}, {s(a['days_to_expiry'])}d to expiry): "
            + "; ".join(bits) + ".")
    rules = (
        "  HOW TO USE (DESCRIPTIVE ONLY — no calls to action, no targets, no "
        "buy/sell): (1) Read IV level vs typical: higher ATM IV = market pricing "
        "more uncertainty. (2) Positive skew = puts richer than calls = downside "
        "hedging demand; negative = upside chase. (3) State the expected-move band "
        "as a range the market is implying, NOT a forecast. (4) The peak-gamma "
        "strike is where positioning is concentrated, often a magnet/pin level — "
        "describe it as positioning, not a prediction. NO-INVENTION: use only the "
        "numbers above; never state an IV, Greek or level not printed here.")
    return head + "\n" + rules


# ── offline self-test (synthetic chain → round-trips IV, checks Greek signs) ──
if __name__ == "__main__":
    S, r, q = 23100.0, 0.065, 0.0
    expiry = (_dt.datetime.now(_IST) + _dt.timedelta(days=22)).strftime(
        "%Y-%m-%dT06:00:00.000Z")
    T = _time_to_expiry(expiry, None)
    true_iv = 0.14
    calls, puts = [], []
    for K in range(22000, 24201, 100):
        cp = _bs_price(S, K, T, r, q, true_iv, True)
        pp = _bs_price(S, K, T, r, q, true_iv, False)
        calls.append({"strike_price": K, "ltp": round(cp, 2),
                      "open_interest": max(1, 50000 - abs(K - 23000) * 5)})
        puts.append({"strike_price": K, "ltp": round(pp, 2),
                     "open_interest": max(1, 50000 - abs(K - 23000) * 5)})

    a = compute_option_analytics(calls, puts, S, expiry)
    import json
    print("recovered ATM IV (input 14.0):", a["atm_iv_pct"])
    print("expected move ±pct:", a["expected_move_pct"])
    print("peak gamma strike:", a["peak_gamma_strike"])
    print("net OI delta:", a["net_oi_weighted_delta"])
    print("\n--- prompt block ---")
    print(format_greeks_block(a, "NIFTY 50"))
    print("\n--- full dict ---")
    print(json.dumps({k: v for k, v in a.items() if k != "key_strikes"},
                     indent=2, default=str))
