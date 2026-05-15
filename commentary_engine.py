"""
commentary_engine.py  ─  MoneyVeda Predictive Intelligence (v3.2)
===================================================================
Detects significant price moves, then fetches every available
data layer to produce plain-English "why it moved" commentary.

Data layers (unchanged):
  1. Live price + 52-week hi/lo + volume + 5-day trend  (yfinance)
  2. Today's NSE filings                                (Supabase)
  3. Sector / Nifty benchmark comparison                (yfinance)
  4. News headlines                                     (yfinance)
  5. Historical pattern matching                        (yfinance)
  6. AI narrative generation                            (Gemini, with rule-based fallback)

v3.2 CHANGES (news quality + reliability):
  - News headlines: junk-headline filter (drops "...Highlights..." trailing-off
    titles, listicles, generic roundups), catalyst-relevance scoring, FULL
    headline shown (no mid-sentence truncation), and honest "no clear catalyst"
    when the best available headline is junk — no invented causation.
  - _build_prompt(): explicitly tells the model to SUMMARISE WHAT THE NEWS SAYS
    in plain words, and to say so plainly + not invent a cause when no headline
    explains the move.
  - Timeout scales to model: Flash-Lite 15s, Pro 120s (Pro is much slower).
  - GEMINI_MODEL kept as Flash-Lite (fast, cheap, fine for 4-6 sentence stock
    notes). GEMINI_MODEL_STRONG added for optional manual escalation.

v3.1 (prior):
  - Supabase cache layer (daily_commentary table) — 1 Gemini call per stock per day max
  - Swapped Claude/Anthropic -> Gemini 2.5 Flash-Lite
  - Legacy ANTHROPIC_API_KEY still supported as a secondary fallback (optional)

Run modes (unchanged):
  python commentary_engine.py              -> analyze all movers now
  python commentary_engine.py RELIANCE     -> analyze one stock
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

# Gemini SDK (optional import — rule-based fallback works without it)
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

load_dotenv()

# ── Clients ───────────────────────────────────────────────────────────────────
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SECRET_KEY")
)

# AI provider keys — Gemini is primary, Anthropic kept as legacy fallback
GEMINI_API_KEY    = os.getenv("GEMINI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")   # legacy — still used if GEMINI fails

# ── Stock universe ─────────────────────────────────────────────────────────────
# Source of truth: nifty100.py — 100 NSE constituents. Falls back to a hardcoded
# list of 19 if the import fails (defensive — keeps legacy behavior alive).
try:
    from nifty100 import NIFTY_100 as _NIFTY_100_LIST
    STOCKS = {sym: yahoo for sym, _name, yahoo in _NIFTY_100_LIST}
except Exception:
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

# ── Sector benchmark mapping ───────────────────────────────────────────────────
# Maps each stock to its Nifty sector index for sector-relative comparison.
# Uses explicit mappings where the sector is well-defined; falls back to ^NSEI
# (Nifty 50) for stocks without a clear sector index.
SECTOR_ETF = {
    # Banks & Financials → Nifty Bank
    "HDFCBANK": "^NSEBANK", "ICICIBANK": "^NSEBANK", "SBIN": "^NSEBANK",
    "KOTAKBANK": "^NSEBANK", "AXISBANK": "^NSEBANK", "INDUSINDBK": "^NSEBANK",
    "BANKBARODA": "^NSEBANK", "PNB": "^NSEBANK", "CANBK": "^NSEBANK",
    "FEDERALBNK": "^NSEBANK", "BAJFINANCE": "^NSEBANK", "BAJAJFINSV": "^NSEBANK",
    "CHOLAFIN": "^NSEBANK", "HDFCLIFE": "^NSEBANK", "SBILIFE": "^NSEBANK",
    "ICICIPRULI": "^NSEBANK", "ICICIGI": "^NSEBANK", "LICI": "^NSEBANK",
    "SHRIRAMFIN": "^NSEBANK", "PFC": "^NSEBANK", "RECLTD": "^NSEBANK",
    "HDFCAMC": "^NSEBANK",

    # IT
    "TCS": "^CNXIT", "INFY": "^CNXIT", "WIPRO": "^CNXIT",
    "HCLTECH": "^CNXIT", "TECHM": "^CNXIT", "LTIM": "^CNXIT",

    # Energy / Oil & Gas
    "RELIANCE": "^CNXENERGY", "ONGC": "^CNXENERGY", "IOC": "^CNXENERGY",
    "BPCL": "^CNXENERGY", "GAIL": "^CNXENERGY", "ADANIENSOL": "^CNXENERGY",
    "ADANIGREEN": "^CNXENERGY",

    # Metals & Mining
    "TATASTEEL": "^CNXMETAL", "JSWSTEEL": "^CNXMETAL", "HINDALCO": "^CNXMETAL",
    "VEDL": "^CNXMETAL", "COALINDIA": "^CNXMETAL", "HINDZINC": "^CNXMETAL",
    "JINDALSTEL": "^CNXMETAL",

    # Auto
    "MARUTI": "^CNXAUTO", "M&M": "^CNXAUTO", "TMPV": "^CNXAUTO",
    "BAJAJ-AUTO": "^CNXAUTO", "EICHERMOT": "^CNXAUTO", "HEROMOTOCO": "^CNXAUTO",
    "TVSMOTOR": "^CNXAUTO", "BOSCHLTD": "^CNXAUTO", "MOTHERSON": "^CNXAUTO",

    # Pharma / Healthcare
    "SUNPHARMA": "^CNXPHARMA", "DRREDDY": "^CNXPHARMA", "CIPLA": "^CNXPHARMA",
    "DIVISLAB": "^CNXPHARMA", "APOLLOHOSP": "^CNXPHARMA",
    "TORNTPHARM": "^CNXPHARMA", "ZYDUSLIFE": "^CNXPHARMA",

    # FMCG
    "HINDUNILVR": "^CNXFMCG", "ITC": "^CNXFMCG", "NESTLEIND": "^CNXFMCG",
    "BRITANNIA": "^CNXFMCG", "DABUR": "^CNXFMCG", "MARICO": "^CNXFMCG",
    "GODREJCP": "^CNXFMCG", "VBL": "^CNXFMCG", "UNITDSPR": "^CNXFMCG",
    "TATACONSUM": "^CNXFMCG",

    # Telecom & Media
    "BHARTIARTL": "^CNXTELECOM",

    # Power & Utilities (no dedicated index — use Nifty Energy)
    "NTPC": "^CNXENERGY", "POWERGRID": "^CNXENERGY",
    "ADANIPOWER": "^CNXENERGY", "TATAPOWER": "^CNXENERGY",
}
# Default for everything else — broad market benchmark
SECTOR_ETF_DEFAULT = "^NSEI"

def _sector_for(symbol: str) -> str:
    """Return the sector ETF/index for a stock, defaulting to Nifty 50."""
    return SECTOR_ETF.get(symbol, SECTOR_ETF_DEFAULT)

MOVE_THRESHOLD = 1.0   # % move to trigger commentary

# v3.2: Flash-Lite stays primary — it's fast and fine for short stock notes.
# GEMINI_MODEL_STRONG is available if you ever want to escalate manually.
GEMINI_MODEL        = "gemini-2.5-flash-lite"   # free tier: 15 RPM, 1000 RPD
GEMINI_MODEL_STRONG = "gemini-2.5-pro"          # optional manual escalation

# v3.2: timeout scales to model. Pro thinking tokens make it MUCH slower than
# Flash-Lite — a 15s timeout would 504 on Pro every time (this is the same bug
# that hit the post-market wrap in market_commentary.py).
GEMINI_TIMEOUT_FAST   = 15    # Flash-Lite — fast
GEMINI_TIMEOUT_STRONG = 120   # Pro — needs room for thinking


# ─────────────────────────────────────────────────────────────────────────────
# CACHE LAYER — Supabase daily_commentary
# ─────────────────────────────────────────────────────────────────────────────
def _today_str() -> str:
    """Return today's date as YYYY-MM-DD (server timezone)."""
    return datetime.now().strftime("%Y-%m-%d")


def get_cached_commentary(symbol: str):
    """
    Check Supabase for today's cached commentary.
    Returns the cached row dict if found, None otherwise.
    """
    try:
        today = _today_str()
        result = supabase.table("daily_commentary")\
            .select("*")\
            .eq("symbol", symbol)\
            .eq("commentary_date", today)\
            .limit(1)\
            .execute()
        if result.data and len(result.data) > 0:
            row = result.data[0]
            print(f"   💾 Cache HIT for {symbol}")
            return {
                "commentary": row["commentary_text"],
                "source":     row.get("source", "gemini"),
                "cached":     True,
            }
        return None
    except Exception as e:
        print(f"   ⚠️  Cache read error: {e}")
        return None


def save_commentary_to_cache(symbol: str, commentary_text: str, source: str) -> None:
    """Upsert commentary into daily_commentary table."""
    try:
        today = _today_str()
        supabase.table("daily_commentary").upsert(
            {
                "symbol":          symbol,
                "commentary_date": today,
                "commentary_text": commentary_text,
                "source":          source,
            },
            on_conflict="symbol,commentary_date",
        ).execute()
        print(f"   💾 Cached commentary for {symbol} (source={source})")
    except Exception as e:
        print(f"   ⚠️  Cache write error: {e}")


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

        current    = float(hist_5d["Close"].iloc[-1])
        prev_close = float(hist_5d["Close"].iloc[-2])
        change_pct = round(((current - prev_close) / prev_close) * 100, 2)

        high_52w      = float(hist_1y["High"].max())
        low_52w       = float(hist_1y["Low"].min())
        pct_from_high = round(((current - high_52w) / high_52w) * 100, 1)
        pct_from_low  = round(((current - low_52w)  / low_52w)  * 100, 1)

        avg_vol   = hist_1y["Volume"].rolling(20).mean().iloc[-1]
        today_vol = hist_5d["Volume"].iloc[-1]
        vol_ratio = round(today_vol / avg_vol, 1) if avg_vol > 0 else 1.0

        trend_5d = round(
            ((hist_5d["Close"].iloc[-1] - hist_5d["Close"].iloc[0])
             / hist_5d["Close"].iloc[0]) * 100, 1
        )

        return {
            "current_price": round(current, 2),
            "prev_close":    round(prev_close, 2),
            "change_pct":    change_pct,
            "high_52w":      round(high_52w, 2),
            "low_52w":       round(low_52w, 2),
            "pct_from_high": pct_from_high,
            "pct_from_low":  pct_from_low,
            "vol_ratio":     vol_ratio,
            "trend_5d_pct":  trend_5d,
        }
    except Exception as e:
        print(f"   ⚠️  Price error for {symbol_ns}: {e}")
        return {}


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 2 — NSE Filings from Supabase
# ─────────────────────────────────────────────────────────────────────────────
def get_today_filings(symbol: str) -> list:
    """Fetch today's filings for a symbol from Supabase."""
    try:
        today = _today_str()
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
# LAYER 4 — News headlines via yfinance
# ─────────────────────────────────────────────────────────────────────────────
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

def get_news_headlines(symbol: str) -> list:
    """Get news headlines using yfinance (reliable)."""
    try:
        ns_symbol = STOCKS.get(symbol, symbol + ".NS")
        ticker = yf.Ticker(ns_symbol)
        news = ticker.news[:8]
        headlines = []
        for n in news:
            try:
                title = n["content"]["title"]
                if title and len(title) > 10:
                    headlines.append(title)
            except Exception:
                pass
        return headlines
    except Exception:
        return []


# ─────────────────────────────────────────────────────────────────────────────
# NEWS QUALITY HELPERS  (new in v3.2)
# ─────────────────────────────────────────────────────────────────────────────
# Pulls the most informative headline out of the yfinance news list, filtering
# the junk that pollutes the feed (GuruFocus "...Highlights..." titles that
# trail off mid-sentence, generic listicles, market roundups). Used by BOTH the
# rule-based fallback and — via the prompt — the AI path.

# Words that signal a real, stock-moving catalyst.
_CATALYST_WORDS = {
    "result", "results", "profit", "loss", "revenue", "dividend", "bonus",
    "acquire", "acquisition", "merger", "demerger", "partnership", "launch",
    "wins", "bags", "secures", "quarterly", "earnings", "order", "contract",
    "upgrade", "downgrade", "target price", "rating", "stake", "buyback",
    "approval", "approved", "expansion", "guidance", "margin", "ipo", "qip",
    "block deal", "bulk deal", "fundraise", "investment", "probe", "penalty",
}

# Patterns that mark a headline as junk — generic, non-specific, or truncated.
_JUNK_MARKERS = (
    "things to know", "stocks to watch", "top gainers", "top losers",
    "market wrap", "closing bell", "opening bell", "market live",
    "share price today", "stocks in news", "buzzing stocks",
    "f&o ban", "trade setup", "stocks to buy",
)


def _is_junk_headline(h: str) -> bool:
    """
    True if the headline is generic boilerplate or a truncated 'highlights'
    title that tells the reader nothing specific about why a stock moved.
    """
    hl = h.lower().strip()
    # GuruFocus-style "...Earnings Call Highlights: Strong India Growth and ..."
    # — trails off mid-sentence, conveys nothing concrete.
    if "highlights" in hl and h.rstrip().endswith("..."):
        return True
    # Generic roundups / listicles.
    if any(marker in hl for marker in _JUNK_MARKERS):
        return True
    return False


def _pick_best_headline(symbol: str, news: list):
    """
    Score every headline and return (best_headline, score).
    score > 0  -> a usable, catalyst-relevant headline
    score <= 0 -> nothing informative; caller should NOT pretend news explains
                  the move (anti-causation-invention rule).
    Returns (None, 0) when the news list is empty.
    """
    if not news:
        return None, 0

    symbol_lower = symbol.lower()
    scored = []
    for h in news:
        hl = h.lower()
        score = 0
        if symbol_lower in hl:
            score += 2                                  # names the stock
        if any(w in hl for w in _CATALYST_WORDS):
            score += 2                                  # mentions a real catalyst
        if _is_junk_headline(h):
            score -= 4                                  # generic / truncated junk
        scored.append((score, h))

    scored.sort(key=lambda x: x[0], reverse=True)
    best_score, best_headline = scored[0]
    return best_headline, best_score


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 5 — Historical pattern matching
# ─────────────────────────────────────────────────────────────────────────────
def find_similar_historical_moves(symbol_ns: str, change_pct: float) -> dict:
    """Look back 1 year for similar % moves."""
    try:
        hist = yf.Ticker(symbol_ns).history(period="1y")
        if len(hist) < 30:
            return {}

        hist["daily_chg"] = hist["Close"].pct_change() * 100
        direction = 1 if change_pct > 0 else -1
        threshold = abs(change_pct) * 0.5
        similar = hist[
            (hist["daily_chg"] * direction >= threshold) &
            (hist.index < hist.index[-1])
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
            "similar_count":     len(similar),
            "avg_5d_recovery":   round(sum(recoveries) / len(recoveries), 2),
            "recovery_hit_rate": round(positive_5d / len(recoveries) * 100, 0),
        }
    except Exception as e:
        print(f"   ⚠️  Historical pattern error: {e}")
        return {}


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 6 — AI Commentary
# ─────────────────────────────────────────────────────────────────────────────
def _build_prompt(symbol: str, data_packet: dict) -> str:
    """Shared prompt used by both Gemini and Anthropic."""
    price   = data_packet.get("price", {})
    sector  = data_packet.get("sector", {})
    filings = data_packet.get("filings", [])
    news    = data_packet.get("news", [])
    hist    = data_packet.get("historical", {})
    change_pct = price.get("change_pct", 0)
    direction  = "fell" if change_pct < 0 else "rose"

    # v3.2: surface the single most informative headline to the model, and flag
    # whether it actually looks like a catalyst — so the model knows when it can
    # cite news and when it must NOT invent a cause.
    best_headline, best_score = _pick_best_headline(symbol, news)
    if best_headline and best_score > 0:
        news_guidance = (
            f"MOST RELEVANT HEADLINE (looks catalyst-related): \"{best_headline}\"\n"
            f"If this headline plausibly explains the move, SUMMARISE WHAT IT SAYS "
            f"in plain words (e.g. 'rose after its Q4 results showed strong India "
            f"growth and margin expansion'). Do NOT just say 'there was news'."
        )
    elif news:
        news_guidance = (
            "AVAILABLE HEADLINES ARE GENERIC (roundups / truncated 'highlights' "
            "titles) — none clearly explains today's move. Do NOT cite them as a "
            "cause. Say plainly that no clear news catalyst is visible and the "
            "move may be technical, sector-driven, or flow-driven."
        )
    else:
        news_guidance = (
            "NO HEADLINES AVAILABLE. Do NOT invent a cause. Say the move has no "
            "visible news catalyst and is likely technical or flow-driven."
        )

    return f"""You are a senior Indian equity analyst writing for retail investors.
A stock has moved significantly today. Analyze the data below and write a clear,
concise commentary (4-6 sentences) explaining:
  1. WHY the stock moved. If a news headline explains it, SUMMARISE WHAT THE NEWS
     SAYS in plain words — don't just say "there was news". If no headline
     explains the move, say so plainly and do NOT invent a cause.
  2. CONTEXT: Is this normal or unusual? Sector-driven or stock-specific?
  3. PREDICTION: What might happen in the next 3-5 days based on patterns?

Keep language simple. Avoid jargon. Use INR (Rs.) for prices. Be factual, not sensational.
Do NOT give direct buy/sell advice. End with one clear takeaway line for a retail investor.

NEWS HANDLING (important):
{news_guidance}

=== DATA ===
Stock: {symbol}
Today's move: {change_pct:+.2f}% ({direction})
Current price: Rs.{price.get('current_price', 'N/A')}
52-week high: Rs.{price.get('high_52w', 'N/A')} ({price.get('pct_from_high', 'N/A')}% from high)
52-week low:  Rs.{price.get('low_52w', 'N/A')} ({price.get('pct_from_low', 'N/A')}% from low)
Volume vs avg: {price.get('vol_ratio', 1.0)}x normal volume
5-day trend: {price.get('trend_5d_pct', 0):+.1f}%
Nifty 50 today: {sector.get('nifty_change_pct', 'N/A')}%
Sector index today: {sector.get('sector_change_pct', 'N/A')}%
NSE Filings today: {json.dumps(filings, indent=2) if filings else 'None found'}
All recent news headlines (for context — prefer the MOST RELEVANT one flagged above):
{chr(10).join('- ' + h for h in news) if news else 'No headlines found'}
Historical similar moves (past 1 year):
  Similar occurrences: {hist.get('similar_count', 'N/A')}
  Avg 5-day return after similar move: {hist.get('avg_5d_recovery', 'N/A')}%
  % of times it recovered in same direction: {hist.get('recovery_hit_rate', 'N/A')}%

Write the commentary now:"""


def _call_gemini(prompt: str, model: str = None):
    """
    Call Gemini API. Returns text on success, None on any failure.
    v3.2: timeout scales to the model — Pro needs far longer than Flash-Lite.
    """
    if not GEMINI_AVAILABLE or not GEMINI_API_KEY:
        return None
    model = model or GEMINI_MODEL
    # Pro's thinking tokens make it much slower; a short timeout 504s every time.
    call_timeout = GEMINI_TIMEOUT_STRONG if "pro" in model else GEMINI_TIMEOUT_FAST
    # Pro also needs a bigger output budget — thinking tokens count against it.
    max_out = 2000 if "pro" in model else 400
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gen_model = genai.GenerativeModel(model)
        response = gen_model.generate_content(
            prompt,
            generation_config={
                "temperature":       0.4,
                "max_output_tokens": max_out,
                "top_p":             0.9,
            },
            request_options={"timeout": call_timeout},
        )
        if response and response.text:
            text = response.text.strip()
            if len(text) >= 30:
                return text
        print(f"   ⚠️  Gemini returned empty/short response ({model})")
        return None
    except Exception as e:
        print(f"   ⚠️  Gemini API error ({model}): {e}")
        return None


def _call_anthropic(prompt: str):
    """Legacy Anthropic call — kept for backward compat. Returns text or None."""
    if not ANTHROPIC_API_KEY:
        return None
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
        print(f"   ⚠️  Anthropic API error: {e}")
        return None


def generate_ai_commentary(symbol: str, data_packet: dict):
    """
    Try Gemini first, then Anthropic (if key set), then rule-based fallback.
    Returns (commentary_text, source_name).
    source_name: 'gemini', 'anthropic', or 'rule_based'
    """
    prompt = _build_prompt(symbol, data_packet)

    # Primary: Gemini (Flash-Lite)
    text = _call_gemini(prompt)
    if text:
        return text, "gemini"

    # Secondary: Anthropic (legacy — only fires if ANTHROPIC_API_KEY is set)
    text = _call_anthropic(prompt)
    if text:
        return text, "anthropic"

    # Tertiary: rule-based
    print(f"   ℹ️  Using rule-based fallback for {symbol}")
    return _rule_based_commentary(symbol, data_packet), "rule_based"


# ─────────────────────────────────────────────────────────────────────────────
# RULE-BASED FALLBACK  (v3.2 — improved news handling)
# ─────────────────────────────────────────────────────────────────────────────
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

    parts = [f"{symbol} {direct} {abs(chg):.2f}% to ₹{cur} today."]

    # Sector context
    stock_vs_nifty = abs(chg) - abs(nifty)
    if abs(stock_vs_nifty) < 0.5:
        mood = "rally" if nifty > 0 else "selloff" if nifty < 0 else "flat session"
        parts.append(f"This broadly mirrors Nifty ({nifty:+.2f}%), suggesting a market-wide {mood}.")
    elif stock_vs_nifty > 0.5:
        parts.append(f"The move is stock-specific — Nifty only moved {nifty:+.2f}% and the sector {sec:+.2f}%.")

    # Volume
    if vol >= 2.0:
        parts.append(f"Volume is {vol}x above average, indicating strong conviction behind the move.")
    elif vol >= 1.3:
        parts.append(f"Volume is moderately elevated ({vol}x avg), supporting the move.")

    # NSE filings
    if filings:
        top  = filings[0]
        cat  = top.get("category", "General")
        sent = top.get("sentiment") or "unanalyzed"
        if sent in ["positive", "negative"]:
            parts.append(
                f"A '{cat}' filing was detected today with {sent} sentiment, "
                f"which may have triggered or amplified the move."
            )
        else:
            parts.append(
                f"A '{cat}' filing was detected today — routine announcement, "
                f"unlikely to be the primary driver."
            )
    else:
        parts.append("No major NSE filings detected today.")

    # News — v3.2: use the scored picker. Show the FULL headline (no mid-sentence
    # truncation), and only present it as a likely driver when it actually scores
    # as catalyst-relevant. If the best headline is junk, say so honestly rather
    # than pasting a meaningless "...Highlights..." title.
    best_headline, best_score = _pick_best_headline(symbol, news)
    if best_headline and best_score > 0:
        parts.append(f"Likely news driver: \"{best_headline}\"")
    elif news:
        parts.append(
            "No clear news catalyst in today's headlines — the move may be "
            "technical, sector-driven, or flow-driven."
        )
    else:
        parts.append(
            "No news catalyst visible today — the move appears technical "
            "or flow-driven."
        )

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
# MAIN — Orchestrator  (cache check + cache write)
# ─────────────────────────────────────────────────────────────────────────────
def analyze_stock(symbol: str, force_refresh: bool = False, ignore_threshold: bool = False):
    """
    Full analysis pipeline for one stock.

    force_refresh:    if True, skip the cache and regenerate from Gemini.
                      Default False (cache-first — best for on-demand user requests).
    ignore_threshold: if True, generate commentary even if the stock hasn't moved
                      more than MOVE_THRESHOLD. Use True for user-initiated requests
                      (users want commentary even on quiet days).
                      Default False (batch/scheduled mode — only movers).
    """
    ns_symbol = STOCKS.get(symbol)
    if not ns_symbol:
        print(f"❓ Unknown symbol: {symbol}")
        return None

    print(f"\n🔍 Analyzing {symbol}...")

    # --- CACHE CHECK ---
    if not force_refresh:
        cached = get_cached_commentary(symbol)
        if cached:
            # Return cached commentary without re-running the full pipeline.
            # Still fetch fresh price so the UI shows current price alongside cached text.
            price_ctx = get_price_context(ns_symbol)
            return {
                "symbol":       symbol,
                "change_pct":   price_ctx.get("change_pct", 0) if price_ctx else 0,
                "price":        price_ctx.get("current_price", "N/A") if price_ctx else "N/A",
                "commentary":   cached["commentary"],
                "source":       cached["source"],
                "cached":       True,
                "generated_at": datetime.now().isoformat(),
            }

    # --- FULL PIPELINE ---
    price_ctx = get_price_context(ns_symbol)
    if not price_ctx:
        print(f"   ❌ Could not fetch price data.")
        return None

    change_pct = price_ctx["change_pct"]
    if abs(change_pct) < MOVE_THRESHOLD and not ignore_threshold:
        print(f"   ➖ {change_pct:+.2f}% — below threshold, skipping.")
        return None

    emoji = "🔴" if change_pct < 0 else "🟢"
    print(f"   {emoji} Price move: {change_pct:+.2f}% to ₹{price_ctx['current_price']}")

    print("   📋 Fetching NSE filings...")
    filings = get_today_filings(symbol)
    print(f"      → {len(filings)} filing(s) found today")

    print("   📊 Fetching sector/Nifty comparison...")
    sector_ctx = get_sector_context(symbol)

    print("   📰 Fetching news headlines...")
    news = get_news_headlines(symbol)
    print(f"      → {len(news)} headline(s) found")

    print("   📈 Checking historical patterns...")
    hist_ctx = find_similar_historical_moves(ns_symbol, change_pct)

    print("   🧠 Generating commentary...")
    data_packet = {
        "price":      price_ctx,
        "sector":     sector_ctx,
        "filings":    filings,
        "news":       news,
        "historical": hist_ctx,
    }
    commentary, source = generate_ai_commentary(symbol, data_packet)

    # --- CACHE WRITE ---
    # Only cache AI-generated commentary. Don't cache rule-based — we want
    # to retry the AI API on the next user click.
    if source in ("gemini", "anthropic"):
        save_commentary_to_cache(symbol, commentary, source)

    result = {
        "symbol":       symbol,
        "change_pct":   change_pct,
        "price":        price_ctx["current_price"],
        "commentary":   commentary,
        "source":       source,
        "cached":       False,
        "filings":      filings,
        "news":         news,
        "sector":       sector_ctx,
        "historical":   hist_ctx,
        "generated_at": datetime.now().isoformat(),
    }

    # Save signal to Supabase signals table (v3 — proper thresholds)
    # ─────────────────────────────────────────────────────────────────
    # Signal classification rules (calibrated for Indian large-cap volatility):
    #   |move| < 0.5%   → NEUTRAL  (skip writing — pure noise on a normal day)
    #   |move| 0.5–1.5% → WATCH    (worth flagging, low conviction)
    #   |move| ≥ 1.5%   → BULLISH or BEARISH (genuine signal)
    #
    # Confidence formula recalibrated so 1.5% move ≈ 30% confidence,
    # 3% move ≈ 60%, 5% move ≈ 100%. Previously a 5% move was the cap which
    # meant typical days showed misleading single-digit confidence even on
    # real signals.
    abs_move = abs(change_pct)
    if abs_move < 0.5:
        signal_type = "NEUTRAL"
    elif abs_move < 1.5:
        signal_type = "WATCH"
    else:
        signal_type = "BULLISH" if change_pct > 0 else "BEARISH"

    # Skip writing NEUTRAL signals — they're noise, not signal.
    if signal_type == "NEUTRAL":
        print(f"   ⚪ {symbol} {change_pct:+.2f}% — below threshold, no signal saved.")
        return result

    # Confidence: linear ramp from 0.5% (start) to 5% (cap), squared for emphasis
    # so small moves get small confidence and big moves get high confidence.
    raw = max(0.0, (abs_move - 0.5) / 4.5)        # 0 at 0.5%, 1 at 5%
    confidence = round(min(1.0, raw ** 0.7), 3)   # gentle curve, hits ~30% at 1.5%

    try:
        supabase.table("signals").insert({
            "symbol":      symbol,
            "signal_type": signal_type,
            "confidence":  confidence,
            "source":      "commentary_engine",
            "message":     f"{symbol} {change_pct:+.2f}% | {commentary[:200]} | PUBLISHED",
        }).execute()
        print(f"   ✅ Saved {signal_type} signal ({confidence:.0%} confidence) to Supabase.")
    except Exception as e:
        print(f"   ⚠️  Supabase save failed: {e}")

    return result


def run_all_movers():
    """Scan all stocks and generate commentary for significant movers."""
    print(f"\n🚀 Commentary Engine starting at {datetime.now().strftime('%H:%M:%S')}")
    print(f"   Threshold: ±{MOVE_THRESHOLD}% move required\n")
    print("─" * 60)

    results = []
    for symbol in list(STOCKS.keys()):
        result = analyze_stock(symbol)
        if result:
            results.append(result)
        time.sleep(0.5)

    print("\n" + "═" * 60)
    print(f"📊 COMMENTARY SUMMARY — {len(results)} mover(s) detected")
    print("═" * 60)

    for r in sorted(results, key=lambda x: abs(x["change_pct"]), reverse=True):
        chg   = r["change_pct"]
        arrow = "▼" if chg < 0 else "▲"
        emoji = "🔴" if chg < 0 else "🟢"
        src   = r.get("source", "?")
        cached = " (cached)" if r.get("cached") else ""
        print(f"\n{emoji} {r['symbol']} {arrow} {abs(chg):.2f}% | ₹{r['price']} | source={src}{cached}")
        print(f"{'─'*58}")
        print(r["commentary"])

    if not results:
        print(f"\n✅ No significant movers today (all within ±{MOVE_THRESHOLD:.1f}%)")

    return results


if __name__ == "__main__":
    if len(sys.argv) > 1:
        sym = sys.argv[1].upper()
        result = analyze_stock(sym, ignore_threshold=True)
        if result:
            print(f"\n{'═'*60}")
            print(f"📝 Commentary for {sym}")
            print(f"   source={result.get('source', '?')}  cached={result.get('cached', False)}")
            print(f"{'═'*60}")
            print(result["commentary"])
    else:
        run_all_movers()
