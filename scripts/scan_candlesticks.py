#!/usr/bin/env python3
"""
MoneyVeda candlestick scanner.

Runs TA-Lib CDL* pattern detection across an Indian equity universe,
applies trend + volume + liquidity filters, and writes JSON consumed by
the static pages under /candlestick-patterns.

Universe is chosen with the UNIVERSE env var:
    nifty50 | nifty100 | nifty200 | nifty500      (default: nifty100)

The symbol list is resolved in this order:
    1. data/universe/<name>.csv committed in the repo   <- authoritative
    2. live fetch from NSE archives (cached back to 1)  <- self-healing
    3. built-in NIFTY 50                                <- last resort

Output:
  data/candlestick/latest.json          -> all signals for the session
  data/candlestick/<pattern-slug>.json  -> per-pattern page feed
"""

import io
import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import talib
import yfinance as yf

IST = timezone(timedelta(hours=5, minutes=30))
OUT_DIR = Path("data/candlestick")
UNIVERSE_DIR = Path("data/universe")

UNIVERSE = os.environ.get("UNIVERSE", "nifty100").strip().lower()
LOOKBACK_DAYS = 150          # headroom for SMA50 + longest CDL pattern
MIN_BARS = 60                # skip symbols with insufficient history
VOLUME_CONFIRM_MULT = 1.2    # day's volume vs its 20-day average
CHUNK_SIZE = 60              # symbols per yfinance batch
MAX_ROWS_PER_PATTERN = 60    # cap page feeds so tables stay usable
CHART_BARS = 70              # daily bars kept per signalled symbol for the chart modal

# Liquidity floor: median daily turnover (close x volume), in rupees.
# This matters enormously past the Nifty 100 — on a thin counter a single
# large order can manufacture a textbook shape that means nothing.
MIN_TURNOVER = float(os.environ.get("MIN_TURNOVER", 2.0e7))   # Rs 2 crore

# On a weekday, refuse to publish unless the newest bar is actually today's.
# Runs soon after the close can catch Yahoo before it has posted the daily
# bar; writing then would publish yesterday's session as if it were fresh.
REQUIRE_FRESH = os.environ.get("REQUIRE_FRESH", "1") not in ("0", "false", "False")

# Constituent lists. niftyindices.com is the primary host; nsearchives is a
# mirror. Both block datacenter IPs, so these are best-effort — the committed
# CSV in data/universe/ is the real source.
NSE_LISTS = {
    "nifty50":  ["https://niftyindices.com/IndexConstituent/ind_nifty50list.csv",
                 "https://nsearchives.nseindia.com/content/indices/ind_nifty50list.csv"],
    "nifty100": ["https://niftyindices.com/IndexConstituent/ind_nifty100list.csv",
                 "https://nsearchives.nseindia.com/content/indices/ind_nifty100list.csv"],
    "nifty200": ["https://niftyindices.com/IndexConstituent/ind_nifty200list.csv",
                 "https://nsearchives.nseindia.com/content/indices/ind_nifty200list.csv"],
    "nifty500": ["https://niftyindices.com/IndexConstituent/ind_nifty500list.csv",
                 "https://nsearchives.nseindia.com/content/indices/ind_nifty500list.csv"],
}

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

# Static NIFTY 50 snapshot: last-resort universe and tier reference.
# The index is rebalanced semi-annually, so data/universe/nifty50.csv
# takes precedence wherever it exists.
NIFTY50 = [
    "RELIANCE", "HDFCBANK", "ICICIBANK", "INFY", "TCS", "ITC", "LT", "SBIN",
    "BHARTIARTL", "AXISBANK", "KOTAKBANK", "HINDUNILVR", "BAJFINANCE", "ASIANPAINT",
    "MARUTI", "SUNPHARMA", "TITAN", "ULTRACEMCO", "NESTLEIND", "WIPRO",
    "ONGC", "NTPC", "POWERGRID", "TATAMOTORS", "TATASTEEL", "JSWSTEEL",
    "HCLTECH", "TECHM", "ADANIENT", "ADANIPORTS", "COALINDIA", "GRASIM",
    "HINDALCO", "DRREDDY", "CIPLA", "DIVISLAB", "APOLLOHOSP", "BAJAJFINSV",
    "BAJAJ-AUTO", "EICHERMOT", "HEROMOTOCO", "BRITANNIA", "TATACONSUM",
    "INDUSINDBK", "SBILIFE", "HDFCLIFE", "BPCL", "SHRIRAMFIN", "LTIM", "TRENT", "M&M",
]


# ===========================================================================
# Universe resolution
# ===========================================================================
def _clean_symbols(series):
    out = []
    for raw in series:
        t = str(raw).strip().upper()
        if t and t != "NAN" and "SYMBOL" not in t:
            out.append(t)
    return list(dict.fromkeys(out))          # de-dupe, keep order


def load_universe(name):
    """Resolve the symbol list. Returns (symbols, source_label)."""
    # 1. committed CSV — authoritative, and uploadable from the GitHub web UI
    local = UNIVERSE_DIR / f"{name}.csv"
    if local.exists():
        try:
            df = pd.read_csv(local)
            col = next((c for c in df.columns if c.strip().lower() == "symbol"),
                       df.columns[0])
            syms = _clean_symbols(df[col])
            if len(syms) >= 20:
                # NSE rebalances semi-annually (cutoffs 31 Jan / 31 Jul, effective
                # around end-March and end-September). Warn rather than fail: a
                # stale list just means a few delisted symbols get skipped.
                age = (datetime.now(IST).date()
                       - datetime.fromtimestamp(local.stat().st_mtime, IST).date()).days
                if age > 200:
                    print(f"::warning::{local} is {age} days old — NSE has rebalanced "
                          f"at least once since. Re-download from "
                          f"niftyindices.com/IndexConstituent/", file=sys.stderr)
                return syms, f"repo:{local} ({age}d old)"
            print(f"  {local} had only {len(syms)} symbols — ignoring.", file=sys.stderr)
        except Exception as exc:
            print(f"  could not read {local}: {exc}", file=sys.stderr)

    # 2. live NSE archives — often blocked from datacenter IPs, so best-effort
    for url in NSE_LISTS.get(name, []):
        try:
            import requests
            r = requests.get(url, timeout=25, headers={
                "User-Agent": "Mozilla/5.0 (compatible; MoneyVedaScanner/1.0)",
                "Accept": "text/csv,*/*"})
            r.raise_for_status()
            df = pd.read_csv(io.StringIO(r.text))
            col = next((c for c in df.columns if c.strip().lower() == "symbol"), None)
            syms = _clean_symbols(df[col])
            if len(syms) >= 20:
                UNIVERSE_DIR.mkdir(parents=True, exist_ok=True)
                df.to_csv(local, index=False)     # cache so the repo self-heals
                host = url.split("/")[2]
                return syms, f"live:{host}({len(syms)})"
        except Exception as exc:
            print(f"  {url.split('/')[2]} failed: {exc}", file=sys.stderr)

    print("  Using built-in NIFTY 50 fallback.", file=sys.stderr)
    return list(NIFTY50), "builtin:nifty50"


def tier_of(symbol, nifty50_set, nifty100_set):
    if symbol in nifty50_set:
        return "NIFTY 50"
    if symbol in nifty100_set:
        return "NIFTY 100"
    return "BROADER"


def fetch(symbols):
    """Batch-download OHLCV in chunks. Returns ({symbol: DataFrame}, [missing])."""
    out, missing = {}, []
    chunks = [symbols[i:i + CHUNK_SIZE] for i in range(0, len(symbols), CHUNK_SIZE)]
    for n, chunk in enumerate(chunks, 1):
        tickers = [f"{s}.NS" for s in chunk]
        raw = None
        for attempt in (1, 2, 3):
            try:
                raw = yf.download(tickers, period=f"{LOOKBACK_DAYS}d", interval="1d",
                                  group_by="ticker", auto_adjust=False,
                                  progress=False, threads=True)
                break
            except Exception as exc:
                if attempt == 3:
                    print(f"  chunk {n} failed after 3 tries: {exc}", file=sys.stderr)
                else:
                    time.sleep(attempt * 4)
        if raw is None or raw.empty:
            missing.extend(chunk)
            continue
        got = 0
        for sym, tkr in zip(chunk, tickers):
            try:
                df = raw[tkr].dropna() if len(chunk) > 1 else raw.dropna()
            except (KeyError, TypeError):
                missing.append(sym)
                continue
            if len(df) >= MIN_BARS:
                out[sym] = df
                got += 1
            else:
                missing.append(sym)
        print(f"  chunk {n}/{len(chunks)}: {got}/{len(chunk)} usable", file=sys.stderr)
    return out, missing


def scan_symbol(symbol, df, tier="NIFTY 50"):
    """Return signal dicts for the latest bar, or [] if the symbol is filtered out."""
    o = df["Open"].to_numpy(dtype=float)
    h = df["High"].to_numpy(dtype=float)
    l = df["Low"].to_numpy(dtype=float)
    c = df["Close"].to_numpy(dtype=float)
    v = df["Volume"].to_numpy(dtype=float)

    # Liquidity gate, applied before anything else. Past the Nifty 100 the
    # universe includes counters where one large order makes a clean shape.
    turnover = float(np.nanmedian(c[-20:] * v[-20:]))
    if not np.isfinite(turnover) or turnover < MIN_TURNOVER:
        return []

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
            "tier": tier,
            "pattern": slug,
            "pattern_name": label,
            "direction": direction,
            "close": round(float(c[i]), 2),
            "change_pct": round(float((c[i] / c[i - 1] - 1) * 100), 2),
            "volume_ratio": round(vol_ratio, 2),
            "volume_confirmed": vol_confirmed,
            "turnover_cr": round(turnover / 1e7, 2),
            "rsi14": round(float(rsi14[i]), 1) if not np.isnan(rsi14[i]) else None,
            "atr14": round(float(atr14[i]), 2) if not np.isnan(atr14[i]) else None,
            "above_sma50": bool(c[i] > sma50[i]) if not np.isnan(sma50[i]) else None,
            "strength": "confirmed" if vol_confirmed else "unconfirmed",
            "bars": bars,
        })
    return signals


def main():
    universe, source = load_universe(UNIVERSE)
    print(f"Universe '{UNIVERSE}': {len(universe)} symbols from {source}", file=sys.stderr)

    # Tier reference sets. Prefer the committed CSVs; the built-in NIFTY50
    # constant is a static snapshot and drifts as the index is rebalanced.
    n50_csv = UNIVERSE_DIR / "nifty50.csv"
    if n50_csv.exists():
        n50, _ = load_universe("nifty50")
        nifty50_set = set(n50)
    else:
        nifty50_set = set(NIFTY50)

    if UNIVERSE == "nifty100":
        nifty100_set = set(universe)
    elif (UNIVERSE_DIR / "nifty100.csv").exists():
        n100, _ = load_universe("nifty100")
        nifty100_set = set(n100)
    else:
        nifty100_set = set(nifty50_set)

    data, missing = fetch(universe)
    pct = 100.0 * len(data) / max(len(universe), 1)
    print(f"Usable history for {len(data)}/{len(universe)} ({pct:.1f}%).", file=sys.stderr)
    if missing:
        # Yahoo has no data for these .NS tickers — usually recent listings,
        # post-merger renames, or a symbol Yahoo spells differently.
        print(f"  no Yahoo data for {len(missing)}: {', '.join(sorted(missing))}",
              file=sys.stderr)
        if pct < 90:
            print(f"::warning::Only {pct:.0f}% of the universe returned data. "
                  f"Check the missing-symbol list above.", file=sys.stderr)

    if not data:
        print("No data fetched — aborting without overwriting existing JSON.", file=sys.stderr)
        return 1

    session_date = max(df.index[-1] for df in data.values()).strftime("%Y-%m-%d")

    now_ist = datetime.now(IST)
    today_ist = now_ist.strftime("%Y-%m-%d")
    if REQUIRE_FRESH and now_ist.weekday() < 5 and session_date != today_ist:
        print(f"Newest bar is {session_date}, today is {today_ist}. "
              f"Yahoo has not posted today's close yet — exiting without "
              f"overwriting. A later run will pick it up.", file=sys.stderr)
        print(f"::notice::Skipped: latest data is {session_date}, not {today_ist}.",
              file=sys.stderr)
        return 0
    all_signals = []
    for sym, df in data.items():
        try:
            all_signals.extend(scan_symbol(sym, df, tier_of(sym, nifty50_set, nifty100_set)))
        except Exception as exc:  # one bad symbol must not kill the run
            print(f"  skip {sym}: {exc}", file=sys.stderr)

    # Confirmed first, then larger-cap tier, then most liquid, then biggest move.
    tier_rank = {"NIFTY 50": 0, "NIFTY 100": 1, "BROADER": 2}
    all_signals.sort(key=lambda s: (
        not s["volume_confirmed"],
        tier_rank.get(s["tier"], 3),
        -s["turnover_cr"],
        -abs(s["change_pct"]),
    ))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    meta = {
        "session_date": session_date,
        "generated_at": datetime.now(IST).isoformat(),
        "universe": UNIVERSE.upper(),
        "universe_source": source,
        "symbols_scanned": len(data),
        "symbols_requested": len(universe),
        "symbols_missing": sorted(missing),
        "min_turnover_cr": round(MIN_TURNOVER / 1e7, 2),
        "total_signals": len(all_signals),
    }

    # The hub page never draws candles, so drop the per-bar OHLC from
    # latest.json. Keeps the shared payload small; per-pattern files keep it.
    slim = [{k: v for k, v in s.items() if k != "bars"} for s in all_signals]
    (OUT_DIR / "latest.json").write_text(
        json.dumps({**meta, "signals": slim}, indent=2)
    )

    # ── per-symbol chart history, for the in-page chart modal ──────────
    # Only symbols that actually produced a signal, so the payload stays small
    # and the browser fetches one small file on demand rather than a bundle.
    chart_dir = OUT_DIR / "charts"
    chart_dir.mkdir(parents=True, exist_ok=True)
    signalled = {s["symbol"] for s in all_signals}
    by_symbol = {}
    for s in all_signals:
        by_symbol.setdefault(s["symbol"], []).append(
            {"pattern": s["pattern"], "name": s["pattern_name"], "dir": s["direction"]})

    for sym in signalled:
        df = data[sym].tail(CHART_BARS)
        c = df["Close"].to_numpy(dtype=float)
        sma20 = talib.SMA(data[sym]["Close"].to_numpy(dtype=float), timeperiod=20)[-len(df):]
        (chart_dir / f"{sym}.json").write_text(json.dumps({
            "symbol": sym,
            "session_date": session_date,
            "patterns": by_symbol[sym],
            "bars": [
                {"d": df.index[i].strftime("%Y-%m-%d"),
                 "o": round(float(df["Open"].iloc[i]), 2),
                 "h": round(float(df["High"].iloc[i]), 2),
                 "l": round(float(df["Low"].iloc[i]), 2),
                 "c": round(float(c[i]), 2),
                 "v": int(df["Volume"].iloc[i]),
                 "s": (round(float(sma20[i]), 2)
                       if not np.isnan(sma20[i]) else None)}
                for i in range(len(df))
            ],
        }, separators=(",", ":")))
    print(f"  wrote {len(signalled)} chart files", file=sys.stderr)

    # ── remove chart files for symbols no longer signalling ────────────
    for old_file in chart_dir.glob("*.json"):
        if old_file.stem not in signalled:
            old_file.unlink()

    for _, slug, label, direction, _ in PATTERNS:
        hits = [s for s in all_signals if s["pattern"] == slug]
        (OUT_DIR / f"{slug}.json").write_text(json.dumps({
            **meta,
            "pattern": slug,
            "pattern_name": label,
            "direction": direction,
            "count": len(hits),
            "truncated": len(hits) > MAX_ROWS_PER_PATTERN,
            "signals": hits[:MAX_ROWS_PER_PATTERN],
        }, indent=2))

    by_tier = {}
    for sig in all_signals:
        by_tier[sig["tier"]] = by_tier.get(sig["tier"], 0) + 1
    print(f"{session_date}: {len(all_signals)} signals {by_tier} "
          f"from {len(data)} symbols.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
