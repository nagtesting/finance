"""
warm_commentary_cache.py  ─  MoneyVeda Commentary Cache Warmer
================================================================
Pre-generates Gemini commentary for the full Nifty 100 universe
(nifty100.SYMBOL_TO_YAHOO). Runs daily at 4:00 PM IST via GitHub
Actions, after the NSE close.

BEFORE THIS SCRIPT:
  The first user to click each stock pays 2-5 sec of Gemini latency.

AFTER THIS SCRIPT:
  Every user click is an instant Supabase read.

RUNTIME: ~100 stocks x (4 s spacing + 2-5 s per Gemini call) is roughly
12-15 minutes. warm_cache.yml MUST set timeout-minutes to at least 25 or
the job is cancelled partway and most symbols stay uncached.

IDEMPOTENT: Safe to run multiple times — skips stocks already cached today.

USAGE:
  python warm_commentary_cache.py              # warm every Nifty 100 symbol
  python warm_commentary_cache.py --force      # regenerate even if cached
  python warm_commentary_cache.py --symbols TCS,INFY  # specific subset
"""

import os
import sys
import time
import argparse
from datetime import datetime, timezone, timedelta

# Reuse the existing commentary engine — don't duplicate logic
import commentary_engine as ce

# Canonical stock universe. commentary_engine has no STOCKS attribute; the
# old `ce.STOCKS` reference meant this warmer crashed on startup every run,
# so nothing was ever cached and every user click fell through to a slow
# live generation.
from nifty100 import SYMBOL_TO_YAHOO

IST = timezone(timedelta(hours=5, minutes=30))

# Rate limiting: Gemini free tier allows 15 req/min.
# We space calls 4 seconds apart → 15/min max, safe headroom.
DELAY_BETWEEN_CALLS_SEC = 4


def _log(emoji: str, msg: str) -> None:
    """Timestamped log for GitHub Actions visibility."""
    t = datetime.now(IST).strftime("%H:%M:%S")
    print(f"{emoji}  [{t}]  {msg}", flush=True)


def warm_one_stock(symbol: str, force: bool = False):
    """
    Generate and cache commentary for one stock.
    Returns 'cached', 'generated', 'skipped', or 'failed'.
    """
    symbol = symbol.upper()

    # Skip check: is this symbol already cached today?
    if not force:
        cached = ce.get_cached_commentary(symbol)
        if cached:
            _log("⏭️", f"{symbol}: already cached (skipping)")
            return "skipped"

    # Generate commentary using the existing pipeline
    # ignore_threshold=True → get commentary even on quiet-move days
    # force_refresh=True → don't double-check cache (we just did)
    try:
        result = ce.analyze_stock(symbol, force_refresh=True, ignore_threshold=True)
        if not result:
            _log("❌", f"{symbol}: analyze_stock returned None")
            return "failed"

        source = result.get("source", "unknown")
        if source == "gemini":
            _log("✅", f"{symbol}: generated (gemini)")
            return "generated"
        elif source == "anthropic":
            _log("✅", f"{symbol}: generated (anthropic fallback)")
            return "generated"
        else:
            # rule_based means Gemini failed — worth logging
            _log("⚠️", f"{symbol}: rule-based fallback (Gemini failed)")
            return "fallback"
    except Exception as e:
        _log("❌", f"{symbol}: exception — {e}")
        return "failed"


def warm_all(symbols=None, force=False):
    """
    Loop through stocks and warm each one.
    Tracks summary stats and returns exit code (0 = success).
    """
    stocks = symbols if symbols else list(SYMBOL_TO_YAHOO.keys())

    _log("🚀", f"Cache warmer starting — {len(stocks)} stocks to process")
    _log("📅", f"Date: {datetime.now(IST).strftime('%Y-%m-%d %H:%M IST')}")
    _log("⚙️", f"Force regenerate: {force}")
    print("─" * 60, flush=True)

    stats = {"generated": 0, "skipped": 0, "fallback": 0, "failed": 0}

    for i, symbol in enumerate(stocks, start=1):
        print(f"\n[{i}/{len(stocks)}]", flush=True)
        result = warm_one_stock(symbol, force=force)
        stats[result] = stats.get(result, 0) + 1

        # Rate limit: pause between Gemini calls (except after last stock)
        if result == "generated" and i < len(stocks):
            time.sleep(DELAY_BETWEEN_CALLS_SEC)

    # Summary
    print("\n" + "═" * 60, flush=True)
    _log("📊", "CACHE WARMING SUMMARY")
    print("═" * 60, flush=True)
    print(f"   ✅ Generated:     {stats.get('generated', 0)}", flush=True)
    print(f"   ⏭️  Skipped:       {stats.get('skipped', 0)} (already cached)", flush=True)
    print(f"   ⚠️  Fallback:      {stats.get('fallback', 0)} (Gemini failed)", flush=True)
    print(f"   ❌ Failed:        {stats.get('failed', 0)}", flush=True)
    print(f"   📍 Total stocks:  {len(stocks)}", flush=True)
    print("═" * 60, flush=True)

    # Exit code: 0 if everything worked, 1 if any stock outright failed
    # (fallback counts as success since rule-based commentary was saved)
    exit_code = 1 if stats.get("failed", 0) > 0 else 0
    _log("🏁", f"Done (exit code {exit_code})")
    return exit_code


def main():
    parser = argparse.ArgumentParser(description="Warm MoneyVeda commentary cache")
    parser.add_argument("--force", action="store_true",
                        help="Regenerate even if today's cache already exists")
    parser.add_argument("--symbols", type=str, default=None,
                        help="Comma-separated stock symbols (default: all)")
    args = parser.parse_args()

    # Validate env vars before starting (so we fail fast, not mid-loop)
    required = ["SUPABASE_URL", "SUPABASE_SECRET_KEY", "GEMINI_API_KEY"]
    missing = [v for v in required if not os.getenv(v)]
    if missing:
        print(f"❌ Missing env vars: {', '.join(missing)}", flush=True)
        sys.exit(2)

    # Parse symbol list if provided
    symbols = None
    if args.symbols:
        symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
        # Validate all symbols exist
        unknown = [s for s in symbols if s not in SYMBOL_TO_YAHOO]
        if unknown:
            print(f"❌ Unknown symbols: {', '.join(unknown)}", flush=True)
            print(f"   Valid: {', '.join(SYMBOL_TO_YAHOO.keys())}", flush=True)
            sys.exit(3)

    exit_code = warm_all(symbols=symbols, force=args.force)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
