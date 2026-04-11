"""
commentary_engine.py  ─  MoneyVeda Predictive Intelligence
===========================================================
Detects significant price moves, then fetches every available
data layer to produce plain-English "why it moved" commentary.

Data layers:
  1. Live price + 52-week hi/lo context      (yfinance)
  2. Today's NSE filings                     (Supabase — your scraper)
  3. Sector / Nifty benchmark comparison     (yfinance)
  4. News sentiment via web scraping         (requests + BeautifulSoup)
  5. Historical pattern matching             (yfinance)
  6. AI narrative generation                 (Claude via Anthropic API)

Run modes:
  python commentary_engine.py              → analyze all movers now
  python commentary_engine.py RELIANCE     → analyze one stock
"""

import os
import sys
import json
import time
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client
import yfinance as yf
from bs4 import BeautifulSoup

load_dotenv()

# ── Clients ───────────────────────────────────────────────────────────────────
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SECRET_KEY")
)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# ── Stock universe ─────────────────────────────────────────────────────────────
STOCKS = {
    "RELIANCE":   "RELIANCE.NS",
    "TCS":        "TCS.NS",
    "HDFCBANK":   "HDFCBANK.NS",
    "INFY":       "INFY.NS",
    "ICICIBANK":  "ICICIBANK.NS",
    "HINDUNILVR": "HINDUNILVR.NS",
    "SBIN":       "SBIN.NS",
    "BHARTIARTL": "BHARTIARTL.NS",
    "BAJFINANCE": "BAJFINANCE.NS",
    "WIPRO":      "WIPRO.NS",
    "ADANIENT":   "ADANIENT.NS",
    "TATASTEEL":  "TATASTEEL.NS",
    "MARUTI":     "MARUTI.NS",
    "SUNPHARMA":  "SUNPHARMA.NS",
    "AXISBANK":   "AXISBANK.NS",
    "KOTAKBANK":  "KOTAKBANK.NS",
    "LT":         "LT.NS",
    "TITAN":      "TITAN.NS",
    "ONGC":       "ONGC.NS",
}

# Sector mapping for benchmark comparison
SECTOR_ETF = {
    "RELIANCE":   "^NSEI",          # Conglomerate → compare to Nifty
    "TCS":        "^CNXIT",         # IT
    "INFY":       "^CNXIT",
    "WIPRO":      "^CNXIT",
    "HDFCBANK":   "^NSEBANK",       # Banking
    "ICICIBANK":  "^NSEBANK",
    "SBIN":       "^NSEBANK",
    "AXISBANK":   "^NSEBANK",
    "KOTAKBANK":  "^NSEBANK",
    "BAJFINANCE": "^NSEBANK",
    "BHARTIARTL": "^CNXTELECOM",    # Telecom
    "HINDUNILVR": "^CNXFMCG",       # FMCG
    "MARUTI":     "^CNXAUTO",       # Auto
    "TATASTEEL":  "^CNXMETAL",      # Metal
    "ADANIENT":   "^NSEI",
    "SUNPHARMA":  "^CNXPHARMA",     # Pharma
    "LT":         "^NSEI",
    "TITAN":      "^NSEI",
    "ONGC":       "^NSEI",
}

MOVE_THRESHOLD = 1.0   # % move to trigger commentary


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 1 — Price context
# ─────────────────────────────────────────────────────────────────────────────
def get_price_context(symbol_ns: str) -> dict:
    """Returns today's move, 52-week position, volume context."""
    try:
        ticker = yf.Ticker(symbol_ns)
        hist_1y = ticker.history(period="1y")
        hist_5d = ticker.history(period="5d")

        if hist_1y.empty or len(hist_5d) < 2:
            return {}

        current   = float(hist_5d["Close"].iloc[-1])
        prev_close= float(hist_5d["Close"].iloc[-2])
        change_pct= round(((current - prev_close) / prev_close) * 100, 2)

        high_52w  = float(hist_1y["High"].max())
        low_52w   = float(hist_1y["Low"].min())
        pct_from_high = round(((current - high_52w) / high_52w) * 100, 1)
        pct_from_low  = round(((current - low_52w)  / low_52w)  * 100, 1)

        # Volume spike?
        avg_vol = hist_1y["Volume"].rolling(20).mean().iloc[-1]
        today_vol = hist_5d["Volume"].iloc[-1]
        vol_ratio = round(today_vol / avg_vol, 1) if avg_vol > 0 else 1.0

        # 5-day trend
        trend_5d = round(
            ((hist_5d["Close"].iloc[-1] - hist_5d["Close"].iloc[0])
             / hist_5d["Close"].iloc[0]) * 100, 1
        )

        return {
            "current_price":   round(current, 2),
            "prev_close":      round(prev_close, 2),
            "change_pct":      change_pct,
            "high_52w":        round(high_52w, 2),
            "low_52w":         round(low_52w, 2),
            "pct_from_high":   pct_from_high,
            "pct_from_low":    pct_from_low,
            "vol_ratio":       vol_ratio,
            "trend_5d_pct":    trend_5d,
        }
    except Exception as e:
        print(f"   ⚠️  Price error for {symbol_ns}: {e}")
        return {}


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 2 — NSE Filings from Supabase
# ─────────────────────────────────────────────────────────────────────────────
def get_today_filings(symbol: str) -> list[dict]:
    """Fetch today's filings for a symbol from Supabase."""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        result = supabase.table("filings")\
            .select("headline, category, sentiment, sentiment_score, filing_date")\
            .eq("symbol", symbol)\
            .gte("created_at", today)\
            .order("created_at", desc=True)\
            .limit(5)\
            .execute()
        return result.data or []
    except Exception as e:
        print(f"   ⚠️  Filing fetch error: {e}")
        return []


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 3 — Sector / Nifty comparison
# ─────────────────────────────────────────────────────────────────────────────
def get_sector_context(symbol: str) -> dict:
    """Compare today's stock move to its sector index and Nifty."""
    try:
        sector_sym = SECTOR_ETF.get(symbol, "^NSEI")
        nifty_sym  = "^NSEI"

        results = {}
        for name, sym in [("sector", sector_sym), ("nifty", nifty_sym)]:
            hist = yf.Ticker(sym).history(period="5d")
            if len(hist) >= 2:
                chg = round(
                    ((hist["Close"].iloc[-1] - hist["Close"].iloc[-2])
                     / hist["Close"].iloc[-2]) * 100, 2
                )
                results[f"{name}_change_pct"] = chg
                results[f"{name}_symbol"]     = sym

        return results
    except Exception as e:
        print(f"   ⚠️  Sector error: {e}")
        return {}


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 4 — News scraping (ET Markets / Moneycontrol headlines)
# ─────────────────────────────────────────────────────────────────────────────
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

def scrape_et_news(symbol: str) -> list[str]:
    """Scrape Economic Times Markets for recent headlines about a symbol."""
    headlines = []
    try:
        url = f"https://economictimes.indiatimes.com/topic/{symbol.lower()}-share-price"
        resp = requests.get(url, headers=HEADERS, timeout=8)
        soup = BeautifulSoup(resp.text, "html.parser")

        # ET article list items
        for item in soup.select("div.eachStory h3, div.clr.topicstry h3")[:6]:
            text = item.get_text(strip=True)
            if text and len(text) > 20:
                headlines.append(text)
    except Exception as e:
        print(f"   ⚠️  ET scrape error: {e}")

    return headlines[:5]


def scrape_moneycontrol_news(symbol: str) -> list[str]:
    """Scrape Moneycontrol news for a symbol."""
    headlines = []
    try:
        url = f"https://www.moneycontrol.com/stocks/cma/newsarticles/mnews.php?sc_id={symbol}"
        resp = requests.get(url, headers=HEADERS, timeout=8)
        soup = BeautifulSoup(resp.text, "html.parser")
        for item in soup.select("li.clearfix h2 a, div.news_main_title a")[:5]:
            text = item.get_text(strip=True)
            if text and len(text) > 20:
                headlines.append(text)
    except Exception as e:
        print(f"   ⚠️  MC scrape error: {e}")
    return headlines[:5]


def get_news_headlines(symbol: str) -> list[str]:
    """Get news headlines using yfinance (reliable)."""
    try:
        ns_symbol = STOCKS.get(symbol, symbol + ".NS")
        ticker = yf.Ticker(ns_symbol)
        news = ticker.news[:5]
        headlines = []
        for n in news:
            try:
                title = n["content"]["title"]
                if title and len(title) > 10:
                    headlines.append(title)
            except:
                pass
        return headlines
    except:
        return []

def get_news_headlines_old(symbol: str):
    """Get news headlines using yfinance (reliable)."""
    try:
        ns_symbol = STOCKS.get(symbol, symbol + ".NS")
        ticker = yf.Ticker(ns_symbol)
        news = ticker.news[:5]
        headlines = []
        for n in news:
            try:
                title = n["content"]["title"]
                if title and len(title) > 10:
                    headlines.append(title)
            except:
                pass
        return headlines
    except:
        return []

def get_news_headlines_old(symbol: str):
    """Combine news from multiple sources, deduplicate."""
    et  = scrape_et_news(symbol)
    mc  = scrape_moneycontrol_news(symbol)
    seen, combined = set(), []
    for h in et + mc:
        key = h[:40].lower()
        if key not in seen:
            seen.add(key)
            combined.append(h)
    return combined[:8]


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 5 — Historical pattern matching
# ─────────────────────────────────────────────────────────────────────────────
def find_similar_historical_moves(symbol_ns: str, change_pct: float) -> dict:
    """
    Look back 1 year for similar % moves.
    Returns average recovery over next 5 days and hit-rate.
    """
    try:
        hist = yf.Ticker(symbol_ns).history(period="1y")
        if len(hist) < 30:
            return {}

        hist["daily_chg"] = hist["Close"].pct_change() * 100
        direction = 1 if change_pct > 0 else -1

        # Find days with a similar-direction move of similar magnitude
        threshold = abs(change_pct) * 0.5
        similar = hist[
            (hist["daily_chg"] * direction >= threshold) &
            (hist.index < hist.index[-1])  # exclude today
        ]

        if similar.empty:
            return {"similar_count": 0}

        recoveries = []
        for idx in similar.index:
            pos = hist.index.get_loc(idx)
            if pos + 5 < len(hist):
                after_5d = hist["Close"].iloc[pos + 5]
                day_of   = hist["Close"].iloc[pos]
                recoveries.append(((after_5d - day_of) / day_of) * 100)

        if not recoveries:
            return {"similar_count": len(similar)}

        positive_5d = sum(1 for r in recoveries if (r * direction) > 0)

        return {
            "similar_count":    len(similar),
            "avg_5d_recovery":  round(sum(recoveries) / len(recoveries), 2),
            "recovery_hit_rate": round(positive_5d / len(recoveries) * 100, 0),
        }
    except Exception as e:
        print(f"   ⚠️  Historical pattern error: {e}")
        return {}


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 6 — AI Commentary via Claude
# ─────────────────────────────────────────────────────────────────────────────
def generate_ai_commentary(symbol: str, data_packet: dict) -> str:
    """
    Send all gathered data to Claude and get plain-English commentary.
    Falls back to a rule-based summary if the API call fails.
    """
    if not ANTHROPIC_API_KEY:
        return _rule_based_commentary(symbol, data_packet)

    price  = data_packet.get("price", {})
    sector = data_packet.get("sector", {})
    filings= data_packet.get("filings", [])
    news   = data_packet.get("news", [])
    hist   = data_packet.get("historical", {})

    change_pct = price.get("change_pct", 0)
    direction  = "fell" if change_pct < 0 else "rose"

    prompt = f"""You are a senior Indian equity analyst writing for retail investors.
A stock has moved significantly today. Analyze the data below and write a clear,
concise commentary (4-6 sentences) explaining:
  1. WHY the stock moved (most likely reasons based on evidence)
  2. CONTEXT: Is this normal or unusual? Sector-driven or stock-specific?
  3. PREDICTION: What might happen in the next 3-5 days based on patterns?

Keep language simple. Avoid jargon. Use INR (₹) for prices. Be factual, not sensational.
End with one clear takeaway line for a retail investor.

=== DATA ===
Stock: {symbol}
Today's move: {change_pct:+.2f}% ({direction})
Current price: ₹{price.get('current_price', 'N/A')}
52-week high: ₹{price.get('high_52w', 'N/A')} ({price.get('pct_from_high', 'N/A')}% from high)
52-week low:  ₹{price.get('low_52w', 'N/A')} ({price.get('pct_from_low', 'N/A')}% from low)
Volume vs avg: {price.get('vol_ratio', 1.0)}x normal volume
5-day trend: {price.get('trend_5d_pct', 0):+.1f}%

Nifty 50 today: {sector.get('nifty_change_pct', 'N/A'):+}%
Sector index today: {sector.get('sector_change_pct', 'N/A'):+}%

NSE Filings today: {json.dumps(filings, indent=2) if filings else 'None found'}

Recent news headlines:
{chr(10).join('- ' + h for h in news) if news else 'No headlines scraped'}

Historical similar moves (past 1 year):
  Similar occurrences: {hist.get('similar_count', 'N/A')}
  Avg 5-day return after similar move: {hist.get('avg_5d_recovery', 'N/A')}%
  % of times it recovered in same direction over 5 days: {hist.get('recovery_hit_rate', 'N/A')}%

Write the commentary now:"""

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key":         ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type":      "application/json",
            },
            json={
                "model":      "claude-sonnet-4-20250514",
                "max_tokens": 400,
                "messages":   [{"role": "user", "content": prompt}],
            },
            timeout=20,
        )
        resp.raise_for_status()
        return resp.json()["content"][0]["text"].strip()
    except Exception as e:
        print(f"   ⚠️  Claude API error: {e} — using rule-based fallback")
        return _rule_based_commentary(symbol, data_packet)


def _rule_based_commentary(symbol: str, data_packet: dict) -> str:
    """Plain-English fallback commentary without AI."""
    price   = data_packet.get("price", {})
    sector  = data_packet.get("sector", {})
    filings = data_packet.get("filings", [])
    news    = data_packet.get("news", [])
    hist    = data_packet.get("historical", {})

    chg    = price.get("change_pct", 0)
    direct = "fell" if chg < 0 else "rose"
    cur    = price.get("current_price", "N/A")
    vol    = price.get("vol_ratio", 1.0)
    nifty  = sector.get("nifty_change_pct", 0)
    sec    = sector.get("sector_change_pct", 0)

    parts = [
        f"{symbol} {direct} {abs(chg):.2f}% to ₹{cur} today."
    ]

    # Sector context
    stock_vs_nifty = abs(chg) - abs(nifty)
    if abs(stock_vs_nifty) < 0.5:
        parts.append(f"This broadly mirrors Nifty ({nifty:+.2f}%), suggesting a market-wide {'rally' if nifty > 0 else 'selloff' if nifty < 0 else 'flat session'}.")
    elif stock_vs_nifty > 0.5:
        parts.append(
            f"The move is stock-specific — Nifty only moved {nifty:+.2f}% and the sector {sec:+.2f}%."
        )

    # Volume
    if vol >= 2.0:
        parts.append(f"Volume is {vol}x above average, indicating strong conviction behind the move.")
    elif vol >= 1.3:
        parts.append(f"Volume is moderately elevated ({vol}x avg), supporting the move.")

    # NSE filings
    if filings:
        top = filings[0]
        cat = top.get("category", "")
        sent= top.get("sentiment") or "unanalyzed"
        if sent in ["positive", "negative"]:
            parts.append(
                f"A '{cat}' filing was detected today with {sent} sentiment, "
                f"which may have triggered or amplified the move."
            )
        elif sent == "neutral" or sent == "unanalyzed":
            parts.append(
                f"A '{cat}' filing was detected today — routine announcement, "
                f"unlikely to be the primary driver."
            )
    else:
        parts.append("No major NSE filings detected today — the move appears to be price/news driven.")

    # News
    if news:
           # Pick most relevant news - prefer symbol-specific headlines
    symbol_lower = symbol.lower()
    relevant = [h for h in news if symbol_lower in h.lower() or any(
        w in h.lower() for w in ['result', 'profit', 'revenue', 'order', 'contract', 'dividend', 'acquire', 'merger', 'partnership']
    )]
    best_news = relevant[0] if relevant else news[0]
    parts.append(f"Recent news: \"{best_news[:100]}\"")

    # 52-week context
    from_high = price.get("pct_from_high", 0)
    from_low  = price.get("pct_from_low", 0)
    if abs(from_high) < 5:
        parts.append("The stock is near its 52-week high — watch for resistance.")
    elif abs(from_low) < 10:
        parts.append("The stock is near its 52-week low — could attract value buyers.")

    # Historical
    recovery = hist.get("avg_5d_recovery")
    hit_rate = hist.get("recovery_hit_rate")
    if recovery is not None and hit_rate is not None:
        parts.append(
            f"In {hist.get('similar_count', 0)} similar past moves, "
            f"the stock averaged {recovery:+.1f}% over the next 5 days "
            f"({hit_rate:.0f}% of the time)."
        )

    return " ".join(parts)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN — Orchestrator
# ─────────────────────────────────────────────────────────────────────────────
def analyze_stock(symbol: str) -> dict | None:
    """
    Full analysis pipeline for one stock.
    Returns commentary dict or None if move is below threshold.
    """
    ns_symbol = STOCKS.get(symbol)
    if not ns_symbol:
        print(f"❓ Unknown symbol: {symbol}")
        return None

    print(f"\n🔍 Analyzing {symbol}...")

    # Layer 1 — Price
    price_ctx = get_price_context(ns_symbol)
    if not price_ctx:
        print(f"   ❌ Could not fetch price data.")
        return None

    change_pct = price_ctx["change_pct"]
    if abs(change_pct) < MOVE_THRESHOLD:
        print(f"   ➖ {change_pct:+.2f}% — below threshold, skipping.")
        return None

    emoji = "🔴" if change_pct < 0 else "🟢"
    print(f"   {emoji} Price move: {change_pct:+.2f}% to ₹{price_ctx['current_price']}")

    # Layer 2 — Filings
    print("   📋 Fetching NSE filings...")
    filings = get_today_filings(symbol)
    print(f"      → {len(filings)} filing(s) found today")

    # Layer 3 — Sector
    print("   📊 Fetching sector/Nifty comparison...")
    sector_ctx = get_sector_context(symbol)

    # Layer 4 — News
    print("   📰 Scraping news headlines...")
    news = get_news_headlines(symbol)
    print(f"      → {len(news)} headline(s) found")

    # Layer 5 — Historical
    print("   📈 Checking historical patterns...")
    hist_ctx = find_similar_historical_moves(ns_symbol, change_pct)

    # Layer 6 — AI Commentary
    print("   🧠 Generating commentary...")
    data_packet = {
        "price":      price_ctx,
        "sector":     sector_ctx,
        "filings":    filings,
        "news":       news,
        "historical": hist_ctx,
    }
    commentary = generate_ai_commentary(symbol, data_packet)

    result = {
        "symbol":      symbol,
        "change_pct":  change_pct,
        "price":       price_ctx["current_price"],
        "commentary":  commentary,
        "filings":     filings,
        "news":        news,
        "sector":      sector_ctx,
        "historical":  hist_ctx,
        "generated_at": datetime.now().isoformat(),
    }

    # Save to Supabase
    try:
        supabase.table("signals").insert({
            "symbol":      symbol,
            "signal_type": "BEARISH" if change_pct < 0 else "BULLISH",
            "confidence":  round(min(abs(change_pct) / 5.0, 1.0), 3),
            "source":      "commentary_engine",
            "message":     f"{symbol} {change_pct:+.2f}% | {commentary[:200]} | PUBLISHED",
        }).execute()
        print("   ✅ Saved to Supabase signals table.")
    except Exception as e:
        print(f"   ⚠️  Supabase save failed: {e}")

    return result


def run_all_movers():
    """Scan all stocks and generate commentary for significant movers."""
    print(f"\n🚀 Commentary Engine starting at {datetime.now().strftime('%H:%M:%S')}")
    print(f"   Threshold: ±{MOVE_THRESHOLD}% move required\n")
    print("─" * 60)

    results = []
    target_stocks = list(STOCKS.keys())

    for symbol in target_stocks:
        result = analyze_stock(symbol)
        if result:
            results.append(result)
        time.sleep(0.5)   # polite delay between yfinance calls

    print("\n" + "═" * 60)
    print(f"📊 COMMENTARY SUMMARY — {len(results)} mover(s) detected")
    print("═" * 60)

    for r in sorted(results, key=lambda x: abs(x["change_pct"]), reverse=True):
        chg   = r["change_pct"]
        arrow = "▼" if chg < 0 else "▲"
        emoji = "🔴" if chg < 0 else "🟢"
        print(f"\n{emoji} {r['symbol']} {arrow} {abs(chg):.2f}% | ₹{r['price']}")
        print(f"{'─'*58}")
        print(r["commentary"])
        print()

    if not results:
        print("\n✅ No significant movers today (all within ±{:.1f}%)".format(MOVE_THRESHOLD))

    return results


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Single stock mode: python commentary_engine.py RELIANCE
        sym = sys.argv[1].upper()
        result = analyze_stock(sym)
        if result:
            print(f"\n{'═'*60}")
            print(f"📝 Commentary for {sym}")
            print(f"{'═'*60}")
            print(result["commentary"])
    else:
        # Full market scan
        run_all_movers()





