#!/usr/bin/env python3
"""
MoneyVeda candlestick scanner.

Runs TA-Lib CDL* pattern detection across an Indian equity universe,
applies trend + volume context filters, and writes JSON consumed by
the static pages under /candlestick-patterns/.

Output:
  data/candlestick/latest.json          -> all signals for the session
  data/candlestick/<pattern-slug>.json  -> per-pattern page feed
"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import talib
import yfinance as yf

IST = timezone(timedelta(hours=5, minutes=30))
OUT_DIR = Path("data/candlestick")
LOOKBACK_DAYS = 120          # enough history for SMA50 + longest CDL pattern
MIN_BARS = 60                # skip symbols with insufficient history
VOLUME_CONFIRM_MULT = 1.2    # volume vs 20-day average

# ---------------------------------------------------------------------------
# Pattern catalogue. Each entry becomes one indexable page on moneyveda.org.
# "context" drives the trend filter:
#   "downtrend" -> reversal is only meaningful if price was below SMA20
#   "uptrend"   -> reversal is only meaningful if price was above SMA20
#   None        -> no trend precondition (continuation / indecision patterns)
# ---------------------------------------------------------------------------
PATTERNS = [
    ("CDLENGULFING",      "bullish-engulfing",    "Bullish Engulfing",     "bullish", "downtrend"),
    ("CDLENGULFING",      "bearish-engulfing",    "Bearish Engulfing",     "bearish", "uptrend"),
    ("CDLHAMMER",         "hammer",               "Hammer",                "bullish", "downtrend"),
    ("CDLINVERTEDHAMMER", "inverted-hammer",      "Inverted Hammer",       "bullish", "downtrend"),
    ("CDLMORNINGSTAR",    "morning-star",         "Morning Star",          "bullish", "downtrend"),
    ("CDLPIERCING",       "piercing-pattern",     "Piercing Pattern",      "bullish", "downtrend"),
    ("CDL3WHITESOLDIERS", "three-white-soldiers", "Three White Soldiers",  "bullish", "downtrend"),
    ("CDLHARAMI",         "bullish-harami",       "Bullish Harami",        "bullish", "downtrend"),
    ("CDLSHOOTINGSTAR",   "shooting-star",        "Shooting Star",         "bearish", "uptrend"),
    ("CDLHANGINGMAN",     "hanging-man",          "Hanging Man",           "bearish", "uptrend"),
    ("CDLEVENINGSTAR",    "evening-star",         "Evening Star",          "bearish", "uptrend"),
    ("CDLDARKCLOUDCOVER", "dark-cloud-cover",     "Dark Cloud Cover",      "bearish", "uptrend"),
    ("CDL3BLACKCROWS",    "three-black-crows",    "Three Black Crows",     "bearish", "uptrend"),
    ("CDLHARAMI",         "bearish-harami",       "Bearish Harami",        "bearish", "uptrend"),
    ("CDLDOJI",           "doji",                 "Doji",                  "neutral", None),
    ("CDLMARUBOZU",       "marubozu",             "Marubozu",              "neutral", None),
]

NIFTY50 = [
    "RELIANCE", "HDFCBANK", "ICICIBANK", "INFY", "TCS", "ITC", "LT", "SBIN",
    "BHARTIARTL", "AXISBANK", "KOTAKBANK", "HINDUNILVR", "BAJFINANCE", "ASIANPAINT",
    "MARUTI", "SUNPHARMA", "TITAN", "ULTRACEMCO", "NESTLEIND", "WIPRO",
    "ONGC", "NTPC", "POWERGRID", "TATAMOTORS", "TATASTEEL", "JSWSTEEL",
    "HCLTECH", "TECHM", "ADANIENT", "ADANIPORTS", "COALINDIA", "GRASIM",
    "HINDALCO", "DRREDDY", "CIPLA", "DIVISLAB", "APOLLOHOSP", "BAJAJFINSV",
    "BAJAJ-AUTO", "EICHERMOT", "HEROMOTOCO", "BRITANNIA", "TATACONSUM",
    "INDUSINDBK", "SBILIFE", "HDFCLIFE", "BPCL", "SHRIRAMFIN", "LTIM", "TRENT",
]


def fetch(symbols):
    """Batch-download OHLCV. Returns {symbol: DataFrame}."""
    tickers = [f"{s}.NS" for s in symbols]
    raw = yf.download(
        tickers,
        period=f"{LOOKBACK_DAYS}d",
        interval="1d",
        group_by="ticker",
        auto_adjust=False,
        progress=False,
        threads=True,
    )
    out = {}
    for sym, tkr in zip(symbols, tickers):
        try:
            df = raw[tkr].dropna()
        except (KeyError, TypeError):
            continue
        if len(df) >= MIN_BARS:
            out[sym] = df
    return out


def scan_symbol(symbol, df):
    """Return list of signal dicts for the most recent bar."""
    o = df["Open"].to_numpy(dtype=float)
    h = df["High"].to_numpy(dtype=float)
    l = df["Low"].to_numpy(dtype=float)
    c = df["Close"].to_numpy(dtype=float)
    v = df["Volume"].to_numpy(dtype=float)

    sma20 = talib.SMA(c, timeperiod=20)
    sma50 = talib.SMA(c, timeperiod=50)
    atr14 = talib.ATR(h, l, c, timeperiod=14)
    rsi14 = talib.RSI(c, timeperiod=14)

    i = -1  # latest completed bar
    prior_close, prior_sma20 = c[i - 1], sma20[i - 1]
    if np.isnan(prior_sma20):
        return []

    in_downtrend = prior_close < prior_sma20
    in_uptrend = prior_close > prior_sma20

    avg_vol = float(np.nanmean(v[-21:-1]))
    vol_ratio = float(v[i] / avg_vol) if avg_vol > 0 else 0.0
    vol_confirmed = vol_ratio >= VOLUME_CONFIRM_MULT

    # Last 5 bars, so the page can draw what the pattern actually looked like
    # rather than only the textbook diagram.
    bars = [
        {"d": df.index[j].strftime("%d %b"),
         "o": round(float(o[j]), 2), "h": round(float(h[j]), 2),
         "l": round(float(l[j]), 2), "c": round(float(c[j]), 2)}
        for j in range(-5, 0)
    ]

    signals = []
    for func, slug, label, direction, context in PATTERNS:
        raw = talib.__dict__[func](o, h, l, c)
        val = int(raw[i])
        if val == 0:
            continue

        # TA-Lib encodes direction in the sign for dual patterns
        # (e.g. CDLENGULFING: +100 bullish, -100 bearish).
        if direction == "bullish" and val < 0:
            continue
        if direction == "bearish" and val > 0:
            continue

        # Trend precondition — a reversal pattern only means something
        # if there is a prior move for it to reverse.
        if context == "downtrend" and not in_downtrend:
            continue
        if context == "uptrend" and not in_uptrend:
            continue

        signals.append({
            "symbol": symbol,
            "pattern": slug,
            "pattern_name": label,
            "direction": direction,
            "close": round(float(c[i]), 2),
            "change_pct": round(float((c[i] / c[i - 1] - 1) * 100), 2),
            "volume_ratio": round(vol_ratio, 2),
            "volume_confirmed": vol_confirmed,
            "rsi14": round(float(rsi14[i]), 1) if not np.isnan(rsi14[i]) else None,
            "atr14": round(float(atr14[i]), 2) if not np.isnan(atr14[i]) else None,
            "above_sma50": bool(c[i] > sma50[i]) if not np.isnan(sma50[i]) else None,
            "strength": "confirmed" if vol_confirmed else "unconfirmed",
            "bars": bars,
        })
    return signals


def main():
    universe = NIFTY50
    print(f"Fetching {len(universe)} symbols...", file=sys.stderr)
    data = fetch(universe)
    print(f"Got usable history for {len(data)}.", file=sys.stderr)

    if not data:
        print("No data fetched — aborting without overwriting existing JSON.", file=sys.stderr)
        return 1

    session_date = max(df.index[-1] for df in data.values()).strftime("%Y-%m-%d")
    all_signals = []
    for sym, df in data.items():
        try:
            all_signals.extend(scan_symbol(sym, df))
        except Exception as exc:  # one bad symbol must not kill the run
            print(f"  skip {sym}: {exc}", file=sys.stderr)

    all_signals.sort(key=lambda s: (not s["volume_confirmed"], -abs(s["change_pct"])))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    meta = {
        "session_date": session_date,
        "generated_at": datetime.now(IST).isoformat(),
        "universe": "NIFTY50",
        "symbols_scanned": len(data),
        "total_signals": len(all_signals),
    }

    # The hub page never draws candles, so drop the per-bar OHLC from
    # latest.json. Keeps the shared payload small; per-pattern files keep it.
    slim = [{k: v for k, v in s.items() if k != "bars"} for s in all_signals]
    (OUT_DIR / "latest.json").write_text(
        json.dumps({**meta, "signals": slim}, indent=2)
    )

    for _, slug, label, direction, _ in PATTERNS:
        hits = [s for s in all_signals if s["pattern"] == slug]
        (OUT_DIR / f"{slug}.json").write_text(json.dumps({
            **meta,
            "pattern": slug,
            "pattern_name": label,
            "direction": direction,
            "count": len(hits),
            "signals": hits,
        }, indent=2))

    print(f"{session_date}: {len(all_signals)} signals across {len(data)} symbols.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
