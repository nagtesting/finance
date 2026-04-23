from flask import Flask, jsonify, request, send_from_directory
from supabase import create_client
from dotenv import load_dotenv
import os
from datetime import datetime, timezone
from flask_cors import CORS
from commentary_engine import analyze_stock

load_dotenv()

app = Flask(__name__)
CORS(app)

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SECRET_KEY")
)

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

        return jsonify({
            "status":       "success",
            "symbol":       symbol,
            "commentary":   result["commentary"],
            "source":       result.get("source", "unknown"),
            "cached":       result.get("cached", False),
            "price":        result.get("price"),
            "change_pct":   result.get("change_pct"),
            "generated_at": result.get("generated_at"),
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
