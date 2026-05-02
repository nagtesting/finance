from flask import Flask, jsonify, request, send_from_directory
from supabase import create_client
from dotenv import load_dotenv
import os
import time
import threading
import requests
from datetime import datetime, timezone
from flask_cors import CORS
from commentary_engine import analyze_stock
from nifty100 import NIFTY_100, SYMBOL_TO_NAME, ALL_YAHOO_SYMS

load_dotenv()

app = Flask(__name__)
CORS(app)

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SECRET_KEY")
)

# ═════════════════════════════════════════════════════════════════
# NIFTY 100 LIVE CACHE (lazy fetch via yfinance, gunicorn-compatible)
# ═════════════════════════════════════════════════════════════════
# Architecture (revised May 2026 after gunicorn worker thread issue):
#   • No background thread (gunicorn pre-fork model kills/restarts threads
#     unpredictably across workers). Instead the cache refreshes lazily.
#   • First request to /api/market-cache after the cache goes stale
#     triggers a synchronous yfinance fetch (~3-6 seconds for 100 tickers).
#   • While one request is fetching, others get the previous cache (locked)
#     so users never see "building" repeatedly.
#   • yfinance handles Yahoo's auth/headers/cookies automatically — much
#     more reliable than raw HTTP which Yahoo has been blocking.
import yfinance as yf

CACHE_MAX_AGE_SECONDS = 60   # Refresh threshold

NIFTY100_CACHE = {
    "tickers":         [],          # list of dicts: {symbol, name, value, pct, ok}
    "updated_at":      None,        # last successful fetch (ISO string)
    "updated_at_unix": 0.0,         # for staleness math
    "fetch_attempts":  0,
    "fetch_failures":  0,
    "last_error":      None,        # last exception string for debugging
}
_cache_lock = threading.Lock()
_refresh_lock = threading.Lock()    # prevents concurrent refresh attempts


def _refresh_nifty100_cache():
    """
    One synchronous refresh pass via yfinance. ~3-6 seconds for 100 tickers.
    Returns True on success (any tickers fetched), False on total failure.
    Caller should hold _refresh_lock.
    """
    NIFTY100_CACHE["fetch_attempts"] += 1
    print(f"[cache] refresh starting attempt #{NIFTY100_CACHE['fetch_attempts']}")

    new_tickers = []
    success_count = 0

    try:
        # yfinance.Tickers() handles batching internally — pass space-separated
        tickers_str = " ".join(ALL_YAHOO_SYMS)
        yf_tickers = yf.Tickers(tickers_str)

        for sym, name, yahoo in NIFTY_100:
            try:
                t = yf_tickers.tickers.get(yahoo)
                if t is None:
                    new_tickers.append({
                        "symbol": sym, "name": name,
                        "value": None, "pct": None, "ok": False,
                    })
                    continue

                fast = t.fast_info
                price      = fast.last_price
                prev_close = fast.previous_close

                if price is None or prev_close is None or prev_close == 0:
                    new_tickers.append({
                        "symbol": sym, "name": name,
                        "value": None, "pct": None, "ok": False,
                    })
                    continue

                pct = ((price - prev_close) / prev_close) * 100
                new_tickers.append({
                    "symbol": sym,
                    "name":   name,
                    "value":  round(float(price), 2),
                    "pct":    round(float(pct), 2),
                    "ok":     True,
                })
                success_count += 1
            except Exception as e:
                # Per-ticker failure — keep the placeholder, don't kill the batch
                new_tickers.append({
                    "symbol": sym, "name": name,
                    "value": None, "pct": None, "ok": False,
                })

    except Exception as e:
        NIFTY100_CACHE["fetch_failures"] += 1
        NIFTY100_CACHE["last_error"] = f"{type(e).__name__}: {e}"
        print(f"[cache] refresh FAILED: {NIFTY100_CACHE['last_error']}")
        return False

    if success_count == 0:
        NIFTY100_CACHE["fetch_failures"] += 1
        NIFTY100_CACHE["last_error"] = "All tickers returned None price"
        print(f"[cache] refresh got 0/{len(NIFTY_100)} tickers")
        return False

    with _cache_lock:
        NIFTY100_CACHE["tickers"]         = new_tickers
        NIFTY100_CACHE["updated_at"]      = datetime.now(timezone.utc).isoformat()
        NIFTY100_CACHE["updated_at_unix"] = time.time()
        NIFTY100_CACHE["last_error"]      = None
    print(f"[cache] refresh OK: {success_count}/{len(NIFTY_100)} tickers")
    return True


def _ensure_cache_fresh(force: bool = False) -> None:
    """
    If cache is stale or empty, refresh it. Held under _refresh_lock so
    concurrent requests don't all trigger a refresh — one fetches, others
    see the new data when it lands.
    """
    age = time.time() - NIFTY100_CACHE["updated_at_unix"]
    is_stale = age > CACHE_MAX_AGE_SECONDS or not NIFTY100_CACHE["tickers"]

    if not is_stale and not force:
        return

    # Try to acquire the refresh lock — if another request is already
    # refreshing, just return whatever is currently cached.
    acquired = _refresh_lock.acquire(blocking=False)
    if not acquired:
        return
    try:
        # Re-check after acquiring (another request may have just refreshed)
        age = time.time() - NIFTY100_CACHE["updated_at_unix"]
        if age <= CACHE_MAX_AGE_SECONDS and NIFTY100_CACHE["tickers"] and not force:
            return
        _refresh_nifty100_cache()
    finally:
        _refresh_lock.release()


# ─────────────────────────────────────────
# HOME
# ─────────────────────────────────────────
@app.route("/")
def home():
    return jsonify({
        "status": "MoneyVeda backend running ✅",
        "version": "1.0",
        "endpoints": [
            "/api/signals",
            "/api/signals/<symbol>",
            "/api/filings",
            "/api/filings/<symbol>",
            "/api/prices",
            "/api/summary",
            "/api/watchlist/<session_id>",
            "/api/watchlist/<session_id>/add",
            "/api/watchlist/<session_id>/remove",
            "/api/watchlist/<session_id>/signals",
            "/api/accuracy",
            "/api/accuracy/record",
            "/api/accuracy/recent",
            "/api/accuracy/stats",
            "/api/audit/recent",
            "/api/accuracy/run-recorder",
            "/api/commentary"
        ]
    })

@app.route("/frontend/<path:filename>")
def serve_frontend(filename):
    return send_from_directory("frontend", filename)

# ─────────────────────────────────────────
# SIGNALS
# ─────────────────────────────────────────
@app.route("/api/signals")
def get_signals():
    try:
        limit = request.args.get("limit", 20)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        result = supabase.table("signals")\
            .select("*")\
            .like("message", "%PUBLISHED%")\
            .gte("created_at", today)\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        return jsonify({
            "status": "success",
            "count": len(result.data),
            "signals": result.data
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/signals/<symbol>")
def get_signals_by_symbol(symbol):
    try:
        result = supabase.table("signals")\
            .select("*")\
            .eq("symbol", symbol.upper())\
            .order("created_at", desc=True)\
            .limit(10)\
            .execute()
        return jsonify({
            "status": "success",
            "symbol": symbol.upper(),
            "count": len(result.data),
            "signals": result.data
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ─────────────────────────────────────────
# FILINGS
# ─────────────────────────────────────────
@app.route("/api/filings")
def get_filings():
    try:
        limit = request.args.get("limit", 20)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        result = supabase.table("filings")\
            .select("id, symbol, source, headline, category, sentiment, sentiment_score, created_at")\
            .gte("created_at", today)\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        return jsonify({
            "status": "success",
            "count": len(result.data),
            "filings": result.data
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/filings/<symbol>")
def get_filings_by_symbol(symbol):
    try:
        result = supabase.table("filings")\
            .select("id, symbol, source, headline, category, sentiment, sentiment_score, created_at")\
            .eq("symbol", symbol.upper())\
            .order("created_at", desc=True)\
            .limit(10)\
            .execute()
        return jsonify({
            "status": "success",
            "symbol": symbol.upper(),
            "count": len(result.data),
            "filings": result.data
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ─────────────────────────────────────────
# PRICES
# ─────────────────────────────────────────
@app.route("/api/prices")
def get_prices():
    try:
        import yfinance as yf
        STOCKS = [
            "^NSEI", "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS",
            "INFY.NS", "ICICIBANK.NS", "SBIN.NS", "BHARTIARTL.NS",
            "BAJFINANCE.NS", "WIPRO.NS", "ADANIENT.NS", "TATASTEEL.NS",
            "MARUTI.NS", "SUNPHARMA.NS", "AXISBANK.NS", "KOTAKBANK.NS",
            "LT.NS", "TITAN.NS", "ONGC.NS"
        ]
        prices = []
        for symbol in STOCKS:
            try:
                ticker = yf.Ticker(symbol)
                price = ticker.fast_info.last_price
                prices.append({
                    "symbol": symbol,
                    "price": round(price, 2) if price else None
                })
            except:
                pass
        return jsonify({
            "status": "success",
            "count": len(prices),
            "timestamp": datetime.now().isoformat(),
            "prices": prices
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ─────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────
@app.route("/api/summary")
def get_summary():
    try:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        signals = supabase.table("signals")\
            .select("*", count="exact")\
            .gte("created_at", today)\
            .execute()
        filings = supabase.table("filings")\
            .select("*", count="exact")\
            .gte("created_at", today)\
            .execute()
        published = supabase.table("signals")\
            .select("*", count="exact")\
            .like("message", "%PUBLISHED%")\
            .gte("created_at", today)\
            .execute()
        return jsonify({
            "status": "success",
            "summary": {
                "total_signals": signals.count,
                "published_signals": published.count,
                "total_filings": filings.count,
                "last_updated": datetime.now().isoformat()
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ─────────────────────────────────────────
# WATCHLIST
# ─────────────────────────────────────────
@app.route("/api/watchlist/<session_id>")
def get_watchlist(session_id):
    try:
        result = supabase.table("watchlists")\
            .select("symbol, created_at")\
            .eq("session_id", session_id)\
            .order("created_at", desc=True)\
            .execute()
        return jsonify({
            "status": "success",
            "session_id": session_id,
            "symbols": [r["symbol"] for r in result.data]
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/watchlist/<session_id>/add", methods=["POST"])
def add_to_watchlist(session_id):
    try:
        data = request.get_json()
        symbol = data.get("symbol", "").upper()
        if not symbol:
            return jsonify({"status": "error", "message": "Symbol required"}), 400
        supabase.table("watchlists").insert({
            "session_id": session_id,
            "symbol": symbol
        }).execute()
        return jsonify({"status": "success", "message": f"{symbol} added"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/watchlist/<session_id>/remove", methods=["POST"])
def remove_from_watchlist(session_id):
    try:
        data = request.get_json()
        symbol = data.get("symbol", "").upper()
        supabase.table("watchlists")\
            .delete()\
            .eq("session_id", session_id)\
            .eq("symbol", symbol)\
            .execute()
        return jsonify({"status": "success", "message": f"{symbol} removed"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/watchlist/<session_id>/signals")
def get_watchlist_signals(session_id):
    try:
        watchlist = supabase.table("watchlists")\
            .select("symbol")\
            .eq("session_id", session_id)\
            .execute()
        symbols = [r["symbol"] for r in watchlist.data]
        if not symbols:
            return jsonify({"status": "success", "signals": [], "symbols": []})
        result = supabase.table("signals")\
            .select("*")\
            .in_("symbol", symbols)\
            .like("message", "%PUBLISHED%")\
            .order("created_at", desc=True)\
            .limit(30)\
            .execute()
        return jsonify({
            "status": "success",
            "symbols": symbols,
            "count": len(result.data),
            "signals": result.data
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ─────────────────────────────────────────
# ACCURACY DASHBOARD
# ─────────────────────────────────────────
@app.route("/api/accuracy")
def get_accuracy():
    try:
        result = supabase.table("signal_outcomes")\
            .select("*")\
            .execute()
        outcomes = result.data
        if not outcomes:
            return jsonify({
                "status": "success",
                "accuracy": {
                    "total_checked": 0,
                    "correct": 0,
                    "incorrect": 0,
                    "accuracy_pct": 0,
                    "by_type": {}
                }
            })
        total = len(outcomes)
        correct = len([o for o in outcomes if o["correct"] == True])
        incorrect = total - correct
        accuracy_pct = round((correct / total) * 100, 1) if total > 0 else 0
        by_type = {}
        for o in outcomes:
            t = o["signal_type"]
            if t not in by_type:
                by_type[t] = {"total": 0, "correct": 0}
            by_type[t]["total"] += 1
            if o["correct"]:
                by_type[t]["correct"] += 1
        for t in by_type:
            by_type[t]["accuracy_pct"] = round(
                (by_type[t]["correct"] / by_type[t]["total"]) * 100, 1
            )
        return jsonify({
            "status": "success",
            "accuracy": {
                "total_checked": total,
                "correct": correct,
                "incorrect": incorrect,
                "accuracy_pct": accuracy_pct,
                "by_type": by_type
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/accuracy/record", methods=["POST"])
def record_outcome():
    try:
        data = request.get_json()
        supabase.table("signal_outcomes").insert({
            "signal_id": data.get("signal_id"),
            "symbol": data.get("symbol"),
            "signal_type": data.get("signal_type"),
            "confidence": data.get("confidence"),
            "price_at_signal": data.get("price_at_signal"),
            "price_after_24h": data.get("price_after_24h"),
            "outcome": data.get("outcome"),
            "correct": data.get("correct")
        }).execute()
        return jsonify({"status": "success", "message": "Outcome recorded"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/accuracy/recent")
def get_recent_outcomes():
    try:
        result = supabase.table("signal_outcomes")\
            .select("*")\
            .order("checked_at", desc=True)\
            .limit(20)\
            .execute()
        return jsonify({
            "status": "success",
            "count": len(result.data),
            "outcomes": result.data
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/accuracy/stats")
def get_accuracy_stats():
    try:
        result = supabase.table("signal_outcomes").select("*")\
                         .order("checked_at", desc=True).execute()
        outcomes = result.data
        resolved = [o for o in outcomes if o["correct"] is not None]
        total = len(resolved)
        correct = len([o for o in resolved if o["correct"]])
        by_sym = {}
        for o in resolved:
            s = o["symbol"]
            if s not in by_sym:
                by_sym[s] = {"total":0,"correct":0}
            by_sym[s]["total"] += 1
            if o["correct"]:
                by_sym[s]["correct"] += 1
        leaderboard = sorted(
            [{"symbol":s,**v,"pct":round(v["correct"]/v["total"]*100,1) if v["total"] else 0}
             for s,v in by_sym.items()],
            key=lambda x: (-x["pct"], -x["total"])
        )
        streak = [{"symbol":o["symbol"],"correct":o["correct"],"signal_type":o["signal_type"]}
                  for o in outcomes[:20]]
        return jsonify({"status":"success","stats":{
            "total_resolved": total,
            "total_correct": correct,
            "accuracy_pct": round(correct/total*100,1) if total else 0,
            "pending_count": len([o for o in outcomes if o["correct"] is None]),
            "leaderboard": leaderboard[:10],
            "last_20_streak": streak
        }})
    except Exception as e:
        return jsonify({"status":"error","message":str(e)}), 500


@app.route("/api/audit/recent")
def get_audit_recent():
    try:
        result = supabase.table("signal_outcomes")\
                         .select("*")\
                         .order("checked_at", desc=True)\
                         .limit(20)\
                         .execute()
        return jsonify({"status":"success","count":len(result.data),"audit_log":result.data})
    except Exception as e:
        return jsonify({"status":"error","message":str(e)}), 500


@app.route("/api/accuracy/run-recorder", methods=["POST"])
def trigger_recorder():
    secret = request.headers.get("X-Admin-Secret","")
    if secret != os.getenv("ADMIN_SECRET","moneyveda-admin"):
        return jsonify({"status":"error","message":"Unauthorized"}), 401
    try:
        record_all_pending_outcomes()
        return jsonify({"status":"success","message":"Recorder ran successfully"})
    except Exception as e:
        return jsonify({"status":"error","message":str(e)}), 500


def record_all_pending_outcomes():
    import yfinance as yf
    from datetime import timedelta
    print(f"Running outcome recorder…")
    done = supabase.table("signal_outcomes").select("signal_id").execute()
    done_ids = {r["signal_id"] for r in done.data if r["signal_id"]}
    cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat()
    signals = supabase.table("signals")\
                      .select("*")\
                      .like("message","%PUBLISHED%")\
                      .lt("created_at", cutoff)\
                      .execute()
    candidates = [s for s in signals.data if s["id"] not in done_ids]
    print(f"{len(candidates)} signals to resolve")
    for sig in candidates:
        try:
            symbol = sig["symbol"]
            sig_type = sig["signal_type"]
            conf = sig.get("confidence", 0)
            ticker = yf.Ticker(symbol)
            price_now = ticker.fast_info.last_price
            if not price_now:
                continue
            hist = ticker.history(period="5d")
            if hist.empty:
                continue
            price_entry = float(hist["Close"].iloc[0])
            pct_change = (price_now - price_entry) / price_entry * 100
            if sig_type == "BULLISH":
                correct = pct_change > 0
            elif sig_type == "BEARISH":
                correct = pct_change < 0
            elif sig_type == "WATCH":
                correct = abs(pct_change) >= 0.5
            else:
                continue
            supabase.table("signal_outcomes").insert({
                "signal_id": sig["id"],
                "symbol": symbol,
                "signal_type": sig_type,
                "confidence": conf,
                "price_at_signal": round(price_entry, 2),
                "price_after_24h": round(price_now, 2),
                "outcome": f"Price moved {pct_change:+.2f}%",
                "correct": bool(correct)
            }).execute()
            print(f"{symbol} → {'✅' if correct else '❌'} ({pct_change:+.2f}%)")
        except Exception as e:
            print(f"Error: {sig.get('symbol','?')} — {e}")

# ─────────────────────────────────────────
# COMMENTARY  (v3.1 — uses cache + Gemini + rule-based fallback)
# ─────────────────────────────────────────
@app.route("/api/commentary")
def get_commentary():
    """
    On-demand commentary endpoint.

    Flow (handled inside analyze_stock):
      1. Check Supabase daily_commentary cache. If hit → return instantly.
      2. Else: fetch 5 data layers (price, filings, sector, news, history).
      3. Try Gemini → Anthropic (legacy) → rule-based fallback.
      4. Cache the AI result for the rest of the day.

    ignore_threshold=True → users get commentary even on quiet-move days.
    force_refresh defaults to False → cache-first, saves API quota.
    """
    try:
        symbol = request.args.get("symbol", "TCS").upper()
        import commentary_engine as ce

        # Quick existence check before running the pipeline
        if symbol not in ce.STOCKS:
            return jsonify({
                "status": "error",
                "message": f"Unknown symbol: {symbol}. Use symbols like TCS, RELIANCE, INFY etc."
            }), 404

        result = ce.analyze_stock(symbol, force_refresh=False, ignore_threshold=True)

        if not result:
            return jsonify({
                "status": "error",
                "message": f"Could not generate commentary for {symbol}. Price data may be unavailable (market closed / holiday)."
            }), 500

        # Fetch full price context so frontend can show all 6 metrics
        # (cache-hit path returns minimal price; this ensures consistency)
        ns_symbol = ce.STOCKS.get(symbol)
        price_ctx = ce.get_price_context(ns_symbol) if ns_symbol else {}

        return jsonify({
            "status":       "success",
            "symbol":       symbol,
            "commentary":   result["commentary"],
            "source":       result.get("source", "unknown"),
            "cached":       result.get("cached", False),
            "generated_at": result.get("generated_at"),
            # Flat price fields (frontend expects these)
            "price":          price_ctx.get("current_price") or result.get("price"),
            "change_pct":     price_ctx.get("change_pct", result.get("change_pct", 0)),
            "high_52w":       price_ctx.get("high_52w"),
            "low_52w":        price_ctx.get("low_52w"),
            "pct_from_high":  price_ctx.get("pct_from_high"),
            "pct_from_low":   price_ctx.get("pct_from_low"),
            "vol_ratio":      price_ctx.get("vol_ratio"),
            "trend_5d_pct":   price_ctx.get("trend_5d_pct"),
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ─────────────────────────────────────────
# MARKET COMMENTARY (pre / intraday / post)  ── v2.0
# ─────────────────────────────────────────
# Serves daily pre/intraday/post market commentary from Supabase cache.
# No AI calls happen here — GitHub Actions generates + caches via
# market_commentary.py, this endpoint just reads and returns.
#
# Query parameters:
#   type=pre        → today's pre-market (one row)
#   type=post       → today's post-market (one row)
#   type=intraday   → intraday rows. Defaults to LATEST one.
#                     Add &all=1 to get every intraday slot for today.
#   type=latest     → auto-pick by IST time (default)
# ─────────────────────────────────────────
# ─────────────────────────────────────────
# NIFTY 100 LIVE CACHE — read endpoint
# ─────────────────────────────────────────
# Returns the in-memory snapshot of all 100 stock prices + % changes.
# Refreshes lazily on demand: if cache is older than 60 sec when this
# endpoint is hit, a fresh yfinance fetch runs synchronously (~3-6 sec
# for first request, instant for subsequent ones within the window).
#
# Query params:
#   sort=movers   → sorted by abs(pct) descending (top movers first)
#   limit=N       → return only first N tickers after sort
@app.route("/api/market-cache")
def get_market_cache():
    try:
        sort_mode = request.args.get("sort", "default").lower()
        limit = request.args.get("limit", type=int)

        # Trigger a refresh if cache is stale or empty (synchronous on first hit,
        # ~3-6 seconds; subsequent hits within 60 sec return cached data instantly)
        _ensure_cache_fresh()

        with _cache_lock:
            tickers = list(NIFTY100_CACHE["tickers"])
            updated_at = NIFTY100_CACHE["updated_at"]
            last_error = NIFTY100_CACHE["last_error"]

        # If we still have no data after attempting refresh, surface the error
        if not tickers:
            return jsonify({
                "status":     "building",
                "message":    "Cache fetch failed. Try again in 30 seconds.",
                "error":      last_error,
                "tickers":    [],
                "updated_at": None,
            })

        if sort_mode == "movers":
            tickers = sorted(
                [t for t in tickers if t["ok"] and t["pct"] is not None],
                key=lambda t: abs(t["pct"]),
                reverse=True,
            )
        if limit and limit > 0:
            tickers = tickers[:limit]

        return jsonify({
            "status":     "success",
            "count":      len(tickers),
            "tickers":    tickers,
            "updated_at": updated_at,
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ─────────────────────────────────────────
# NIFTY 100 SYMBOL CATALOG — for autocomplete / dropdown
# ─────────────────────────────────────────
# Static list of (symbol, display_name) — frontend caches this on first load.
@app.route("/api/market-cache/symbols")
def get_symbol_catalog():
    return jsonify({
        "status": "success",
        "count":  len(NIFTY_100),
        "symbols": [
            {"symbol": sym, "name": name}
            for sym, name, _ in NIFTY_100
        ],
    })


@app.route("/api/market-commentary")
def get_market_commentary():
    try:
        from datetime import timezone, timedelta
        IST = timezone(timedelta(hours=5, minutes=30))

        ctype = request.args.get("type", "latest").lower()
        want_all = request.args.get("all", "").lower() in ("1", "true", "yes")

        now_ist = datetime.now(IST)
        today = now_ist.strftime("%Y-%m-%d")
        hour_min = now_ist.hour * 60 + now_ist.minute

        # Resolve 'latest' to a concrete type based on IST time
        if ctype == "latest":
            if hour_min >= 16 * 60:           # 16:00 IST onwards
                ctype = "post"
            elif hour_min >= 9 * 60 + 15:     # 09:15 - 15:59 IST
                ctype = "intraday"
            else:                             # before 09:15 IST
                ctype = "pre"

        if ctype not in ("pre", "intraday", "post"):
            return jsonify({
                "status":  "error",
                "message": "Invalid type. Use 'pre', 'intraday', 'post', or 'latest'."
            }), 400

        # Intraday + all=1: return today's full timeline
        if ctype == "intraday" and want_all:
            res = (
                supabase.table("market_commentary")
                .select("commentary_date, slot_time, commentary_text, source, created_at")
                .eq("commentary_type", "intraday")
                .eq("commentary_date", today)
                .order("slot_time", desc=False)
                .execute()
            )
            rows = res.data or []
            return jsonify({
                "status":   "success",
                "type":     "intraday",
                "date":     today,
                "is_today": True,
                "count":    len(rows),
                "rows": [
                    {
                        "slot":         (r.get("slot_time") or "")[:5],
                        "commentary":   r.get("commentary_text"),
                        "source":       r.get("source", "gemini"),
                        "generated_at": r.get("created_at"),
                    }
                    for r in rows
                ],
            })

        # Single-row queries (pre, post, or latest intraday)
        q = (
            supabase.table("market_commentary")
            .select("*")
            .eq("commentary_type", ctype)
            .eq("commentary_date", today)
        )

        if ctype == "intraday":
            q = q.order("slot_time", desc=True).limit(1)
        else:
            q = q.limit(1)

        result = q.execute()

        # Fallback: today's row not ready yet — return most recent of this type
        if not result.data:
            fallback_q = (
                supabase.table("market_commentary")
                .select("*")
                .eq("commentary_type", ctype)
                .order("commentary_date", desc=True)
                .order("slot_time",      desc=True)
                .limit(1)
                .execute()
            )
            if not fallback_q.data:
                msg = {
                    "pre":      "No pre-market commentary yet. Generated daily at 08:00 IST.",
                    "intraday": "No intraday commentary yet. Generated every 30 min from 09:30 to 15:30 IST.",
                    "post":     "No post-market commentary yet. Generated daily at 16:00 IST.",
                }[ctype]
                return jsonify({"status": "empty", "message": msg})
            row = fallback_q.data[0]
            is_today = False
        else:
            row = result.data[0]
            is_today = True

        return jsonify({
            "status":       "success",
            "type":         row["commentary_type"],
            "date":         row["commentary_date"],
            "slot":         (row.get("slot_time") or "")[:5],
            "is_today":     is_today,
            "commentary":   row["commentary_text"],
            "source":       row.get("source", "gemini"),
            "generated_at": row["created_at"],
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
