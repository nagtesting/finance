"""
market_commentary.py  ─  MoneyVeda Market Commentary (v2.0)
====================================================================
Generates daily AI-powered market commentary for Indian retail investors.

THREE MODES (v2.0 upgrade — was 2 in v1):
  1. PRE-MARKET   (08:00 IST)
       Overnight US, ADRs, dollar index, crude, gold, Asian markets,
       previous NSE close → likely Nifty opening sentiment.

  2. INTRADAY     (09:30, 10:00, 10:30 ... 15:30 IST — 13 slots/day)
       Live Nifty/Sensex level, sector indices, top movers vs prev close.
       09:30 slot = "opening tick" (10 lines, just-after-open),
       subsequent slots = "what's changed" delta narrative (10 lines).

  3. POST-MARKET  (16:00 IST)
       Today's close, sector winners/losers, top movers, filings,
       news → 20-line wrap of what drove the market.

DATA SOURCES:
  • https://moneyveda.org/api/market?mode=usa     (US markets)
  • https://moneyveda.org/api/market?mode=world   (Asia, FX, commodities)
  • https://moneyveda.org/api/market?mode=india   (NSE data + stocks)
  • Supabase filings table (today's NSE announcements — post only)
  • Supabase market_commentary table (previous intraday slot — for delta)

OUTPUT:
  • Pre/Post: ~20 lines via Gemini 2.5 Flash-Lite
  • Intraday: ~10 lines via Gemini 2.5 Flash-Lite
  • Saved to Supabase `market_commentary` table (one row per slot)
  • Frontend reads from cache (no live API calls per user click)

USAGE:
  python market_commentary.py                     # auto-detect from IST time
  python market_commentary.py --mode pre
  python market_commentary.py --mode post
  python market_commentary.py --mode intraday     # auto-snap to nearest slot
  python market_commentary.py --mode intraday --slot 10:30
  python market_commentary.py --mode pre --dry-run

EXIT CODES:
  0 = success, 2 = data too thin (skipped), 1 = config/env error
"""

import os
import sys
import json
import argparse
import requests
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from supabase import create_client

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
SUPABASE_URL        = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")
GEMINI_API_KEY      = os.getenv("GEMINI_API_KEY")

MARKET_API_BASE = "https://moneyveda.org/api/market"
GEMINI_MODEL    = "gemini-2.5-flash-lite"
IST             = timezone(timedelta(hours=5, minutes=30))

# Canonical intraday slot times (IST). Must match the cron schedule in YAML.
INTRADAY_SLOTS = [
    "09:30", "10:00", "10:30", "11:00", "11:30", "12:00", "12:30",
    "13:00", "13:30", "14:00", "14:30", "15:00", "15:30",
]
PRE_SLOT  = "08:00"   # nominal slot label for pre-market row
POST_SLOT = "16:00"   # nominal slot label for post-market row

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (MoneyVeda/2.0 MarketCommentary) "
        "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
    )
}

# Supabase client
supabase = None
if SUPABASE_URL and SUPABASE_SECRET_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)


# ─────────────────────────────────────────────────────────────────────────────
# UTILITIES
# ─────────────────────────────────────────────────────────────────────────────
def _today_ist() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d")


def _now_ist_str() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")


def _log(emoji: str, msg: str) -> None:
    print(f"{emoji}  [{datetime.now(IST).strftime('%H:%M:%S')}]  {msg}")


def _snap_to_intraday_slot(hh: int, mm: int) -> str:
    """Snap a (hour, minute) IST tuple to the nearest valid intraday slot."""
    # Find the slot whose minute distance is smallest, but don't go past current time
    candidate = None
    cur_total = hh * 60 + mm
    for s in INTRADAY_SLOTS:
        sh, sm = map(int, s.split(":"))
        s_total = sh * 60 + sm
        # Pick the largest slot <= current time
        if s_total <= cur_total:
            candidate = s
        else:
            break
    return candidate or INTRADAY_SLOTS[0]


def detect_mode_and_slot():
    """
    Auto-detect mode + slot from current IST time.
    Used when --mode is not specified, or to validate an explicit choice.
    Returns (mode, slot_label).
    """
    now = datetime.now(IST)
    hh, mm = now.hour, now.minute

    # Before 09:15 → pre-market
    if hh < 9 or (hh == 9 and mm < 15):
        return "pre", PRE_SLOT
    # 16:00 onwards → post-market
    if hh >= 16:
        return "post", POST_SLOT
    # Otherwise intraday — snap to nearest slot <= now
    return "intraday", _snap_to_intraday_slot(hh, mm)


# ─────────────────────────────────────────────────────────────────────────────
# DATA FETCHING — uses your existing Vercel /api/market.js endpoint
# ─────────────────────────────────────────────────────────────────────────────
def fetch_market_data(mode: str, timeout: int = 12):
    """Fetch ticker data from moneyveda.org/api/market?mode=<X>."""
    url = f"{MARKET_API_BASE}?mode={mode}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        tickers = data.get("tickers", [])
        valid = [t for t in tickers if t.get("ok")]
        _log("📊", f"Fetched {len(valid)}/{len(tickers)} tickers from {mode}")
        return valid
    except Exception as e:
        _log("⚠️", f"Failed to fetch {mode} market data: {e}")
        return None


def find_ticker(tickers: list, label: str):
    if not tickers:
        return None
    for t in tickers:
        if t.get("label") == label:
            return t
    return None


def format_ticker_line(t: dict, with_value: bool = True) -> str:
    if not t:
        return "data unavailable"
    label = t.get("label", "?")
    value = t.get("value")
    pct   = t.get("pct", 0)
    sign  = "+" if pct >= 0 else ""
    if with_value and value is not None:
        val_str = f"{value:,.2f}" if isinstance(value, (int, float)) else str(value)
        return f"{label}: {val_str} ({sign}{pct}%)"
    return f"{label}: {sign}{pct}%"


def _format_ticker_list(tickers: list) -> str:
    if not tickers:
        return "  (data unavailable)"
    return "\n".join("  " + format_ticker_line(t) for t in tickers if t)


# ─────────────────────────────────────────────────────────────────────────────
# FILINGS (post-market only)
# ─────────────────────────────────────────────────────────────────────────────
def get_todays_filings(limit: int = 20):
    if not supabase:
        return []
    try:
        today = _today_ist()
        result = (
            supabase.table("filings")
            .select("symbol, headline, category, sentiment, sentiment_score")
            .gte("created_at", today)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        data = result.data or []
        _log("📋", f"Fetched {len(data)} filings for today")
        return data
    except Exception as e:
        _log("⚠️", f"Filings fetch failed: {e}")
        return []


def summarize_filings(filings: list) -> str:
    if not filings:
        return "No major filings today"
    lines = []
    for f in filings[:10]:
        sym  = f.get("symbol", "?")
        cat  = f.get("category", "General")
        sent = f.get("sentiment") or "neutral"
        head = (f.get("headline") or "")[:80]
        lines.append(f"  • {sym} [{cat}, {sent}]: {head}")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# PRIOR CONTEXT (intraday only) — fetch the previous slot's commentary +
# pre-market commentary so the new intraday slot can write a "delta" narrative.
# ─────────────────────────────────────────────────────────────────────────────
def get_prior_intraday_context(today: str, current_slot: str) -> dict:
    """
    Returns {
      "pre_text": str | None,
      "prev_slot": str | None,
      "prev_text": str | None,
      "prev_nifty_pct": float | None,
    }
    """
    out = {"pre_text": None, "prev_slot": None, "prev_text": None, "prev_nifty_pct": None}
    if not supabase:
        return out
    try:
        # Pre-market for today
        pre = (
            supabase.table("market_commentary")
            .select("commentary_text")
            .eq("commentary_type", "pre")
            .eq("commentary_date", today)
            .limit(1)
            .execute()
        )
        if pre.data:
            out["pre_text"] = (pre.data[0].get("commentary_text") or "")[:1200]

        # Most recent intraday before current_slot
        prev = (
            supabase.table("market_commentary")
            .select("slot_time, commentary_text, data_snapshot")
            .eq("commentary_type", "intraday")
            .eq("commentary_date", today)
            .lt("slot_time", current_slot + ":00")
            .order("slot_time", desc=True)
            .limit(1)
            .execute()
        )
        if prev.data:
            row = prev.data[0]
            out["prev_slot"] = (row.get("slot_time") or "")[:5]
            out["prev_text"] = (row.get("commentary_text") or "")[:1000]
            try:
                snap = row.get("data_snapshot")
                if isinstance(snap, str):
                    snap = json.loads(snap)
                if isinstance(snap, dict):
                    n = snap.get("nifty")
                    if isinstance(n, dict):
                        out["prev_nifty_pct"] = n.get("pct")
            except Exception:
                pass
    except Exception as e:
        _log("⚠️", f"Prior context fetch failed: {e}")
    return out


# ─────────────────────────────────────────────────────────────────────────────
# DATA PACKETS
# ─────────────────────────────────────────────────────────────────────────────
def build_pre_market_packet():
    _log("🌅", "Building pre-market data packet")
    packet = {
        "timestamp_ist": _now_ist_str(),
        "date":          _today_ist(),
        "slot":          PRE_SLOT,
        "us_markets":    [],
        "asia_pacific":  [],
        "currencies":    [],
        "commodities":   [],
        "crypto":        [],
        "us_tech":       [],
        "india_prev":    [],
    }

    usa = fetch_market_data("usa")
    if usa:
        packet["us_markets"]  = [find_ticker(usa, l) for l in
                                 ["S&P 500", "NASDAQ", "DOW JONES", "RUSSELL 2000", "VIX"]]
        packet["commodities"] = [find_ticker(usa, l) for l in ["GOLD", "CRUDE OIL", "SILVER"]]
        packet["currencies"]  = [find_ticker(usa, l) for l in ["US DOLLAR", "EUR/USD"]]
        packet["crypto"]      = [find_ticker(usa, l) for l in ["BITCOIN", "ETHEREUM"]]
        packet["us_tech"]     = [find_ticker(usa, l) for l in
                                 ["APPLE", "MICROSOFT", "NVIDIA", "ALPHABET", "META"]]

    world = fetch_market_data("world")
    if world:
        packet["asia_pacific"] = [find_ticker(world, l) for l in
                                  ["NIKKEI 225", "HANG SENG", "ASX 200", "KOSPI"]]
        usd_inr = find_ticker(world, "USD/INR")
        if usd_inr:
            packet["currencies"].append(usd_inr)

    india = fetch_market_data("india")
    if india:
        packet["india_prev"] = [find_ticker(india, l) for l in
                                ["SENSEX", "NIFTY 50", "NIFTY BANK", "NIFTY IT"]]

    for key in packet:
        if isinstance(packet[key], list):
            packet[key] = [t for t in packet[key] if t]
    return packet


def build_intraday_packet(slot: str):
    """Live snapshot during market hours."""
    _log("📈", f"Building intraday data packet for slot {slot}")
    today = _today_ist()
    packet = {
        "timestamp_ist": _now_ist_str(),
        "date":          today,
        "slot":          slot,
        "is_opening":    slot == "09:30",
        "nifty":         None,
        "sensex":        None,
        "sectors":       [],
        "top_stocks":    [],
        "currencies":    [],
        "commodities":   [],
        "asia_pacific":  [],
    }

    india = fetch_market_data("india")
    if india:
        packet["sensex"] = find_ticker(india, "SENSEX")
        packet["nifty"]  = find_ticker(india, "NIFTY 50")
        packet["sectors"] = [
            t for t in (find_ticker(india, l) for l in
                        ["NIFTY BANK", "NIFTY IT", "NIFTY AUTO",
                         "NIFTY PHARMA", "NIFTY FMCG", "NIFTY METAL", "NIFTY ENERGY"])
            if t
        ]

        stock_labels = [
            "RELIANCE", "HDFC BANK", "TCS", "INFOSYS", "ICICI BANK",
            "TATA MOTORS", "WIPRO", "AXIS BANK", "SBI", "MARUTI",
            "SUN PHARMA", "BAJAJ FIN", "HUL", "L&T", "KOTAK BANK",
            "ITC", "AIRTEL", "ASIAN PAINTS", "TITAN", "ULTRATECH CEM",
            "NESTLE INDIA", "POWER GRID", "NTPC", "ONGC", "ADANI ENT",
        ]
        stocks = [find_ticker(india, l) for l in stock_labels]
        stocks = [s for s in stocks if s and s.get("pct") is not None]
        stocks_sorted = sorted(stocks, key=lambda s: abs(s.get("pct", 0)), reverse=True)
        packet["top_stocks"] = stocks_sorted[:8]

        packet["commodities"] = [t for t in (find_ticker(india, l)
                                              for l in ["GOLD", "CRUDE OIL"]) if t]
        usd_inr = find_ticker(india, "USD/INR")
        if usd_inr:
            packet["currencies"].append(usd_inr)

    # Asian markets are still trading before 13:30 IST — useful early in the day
    if slot < "13:30":
        world = fetch_market_data("world")
        if world:
            packet["asia_pacific"] = [t for t in (find_ticker(world, l) for l in
                                       ["NIKKEI 225", "HANG SENG", "KOSPI"]) if t]

    # Fetch prior context for narrative continuity
    packet["prior"] = get_prior_intraday_context(today, slot)
    return packet


def build_post_market_packet():
    _log("🌆", "Building post-market data packet")
    packet = {
        "timestamp_ist": _now_ist_str(),
        "date":          _today_ist(),
        "slot":          POST_SLOT,
        "nifty":         None,
        "sensex":        None,
        "sectors":       [],
        "top_stocks":    [],
        "currencies":    [],
        "commodities":   [],
        "us_status":     [],
        "filings":       [],
    }

    india = fetch_market_data("india")
    if india:
        packet["sensex"] = find_ticker(india, "SENSEX")
        packet["nifty"]  = find_ticker(india, "NIFTY 50")
        packet["sectors"] = [t for t in (find_ticker(india, l) for l in
                              ["NIFTY BANK", "NIFTY IT", "NIFTY AUTO",
                               "NIFTY PHARMA", "NIFTY FMCG"]) if t]

        stock_labels = [
            "RELIANCE", "HDFC BANK", "TCS", "INFOSYS", "TATA MOTORS", "ICICI BANK",
            "WIPRO", "AXIS BANK", "SBI", "MARUTI", "SUN PHARMA", "BAJAJ FIN", "HUL",
            "L&T", "KOTAK BANK", "ITC", "AIRTEL", "ASIAN PAINTS", "TITAN",
            "ULTRATECH CEM", "NESTLE INDIA", "POWER GRID", "NTPC", "ONGC", "ADANI ENT",
        ]
        stocks = [find_ticker(india, l) for l in stock_labels]
        stocks = [s for s in stocks if s and s.get("pct") is not None]
        packet["top_stocks"] = sorted(stocks,
                                       key=lambda s: abs(s.get("pct", 0)),
                                       reverse=True)[:10]
        packet["commodities"] = [t for t in (find_ticker(india, l)
                                              for l in ["GOLD", "CRUDE OIL"]) if t]
        usd_inr = find_ticker(india, "USD/INR")
        if usd_inr:
            packet["currencies"] = [usd_inr]

    usa = fetch_market_data("usa")
    if usa:
        packet["us_status"] = [t for t in (find_ticker(usa, l)
                                            for l in ["S&P 500", "NASDAQ"]) if t]

    packet["filings"] = get_todays_filings()
    return packet


# ─────────────────────────────────────────────────────────────────────────────
# PROMPT TEMPLATES
# ─────────────────────────────────────────────────────────────────────────────
PRE_MARKET_PROMPT = """You are a senior Indian equity market analyst writing a PRE-MARKET commentary for MoneyVeda — a free financial platform for Indian retail investors. NSE opens at 9:15 AM IST today.

YOUR TASK:
Write a 20-line plain-English commentary that helps a retail investor understand how global markets overnight might impact the Indian market opening today. Use natural paragraphs (no bullet points, no headers). Write as if explaining to a friend who invests casually.

STRUCTURE (approximately):
  Lines 1-4:  Lead with the overall mood — bullish/bearish/mixed — based on overnight cues.
  Lines 5-8:  US market close: Dow, Nasdaq, S&P performance. What drove them?
  Lines 9-12: Asian markets this morning (Nikkei, Hang Seng), plus dollar index and USD/INR.
  Lines 13-16: Commodities (crude, gold) and what they imply for Indian sectors.
  Lines 17-19: Potential Nifty opening direction — educated guess, clearly framed as expectation not prediction.
  Line 20:    One-line takeaway for a retail investor.

RULES:
  1. USE ONLY the data provided. Do not invent numbers, news, or events.
  2. Frame predictions as likelihood, not certainty ("may open", "could see pressure", "likely to").
  3. Do NOT give buy/sell advice on specific stocks. Educational content only.
  4. Use Rs. for currency (not the rupee symbol to avoid encoding issues).
  5. If data for any asset is missing, just omit that asset — don't say "data unavailable".
  6. End with a clear, actionable mindset (e.g., "Watch for banking strength", "Caution advised").

=== DATA FOR TODAY ({date}) ===
Timestamp: {timestamp}

US MARKETS (overnight close):
{us_markets}

US TECH (drivers of Nifty IT sentiment):
{us_tech}

ASIA-PACIFIC (already trading this morning):
{asia_pacific}

CURRENCIES:
{currencies}

COMMODITIES:
{commodities}

CRYPTO (risk-appetite indicator):
{crypto}

INDIA — PREVIOUS DAY'S CLOSE (for reference):
{india_prev}

Now write the 20-line pre-market commentary:"""


INTRADAY_OPENING_PROMPT = """You are a senior Indian equity market analyst writing the FIRST INTRADAY commentary of the day for MoneyVeda. NSE opened at 9:15 AM IST. It is now {timestamp}.

YOUR TASK:
Write a CRISP 10-LINE plain-English commentary on how the market opened. This is the first read of the day after the bell — focus on the opening tick, sector behaviour in the first 15 minutes, and how it compares to the pre-market expectation. Use natural paragraphs (no bullet points, no headers).

STRUCTURE (approximately):
  Lines 1-2: How did Nifty/Sensex open vs yesterday's close. Set the tone.
  Lines 3-4: Which sectors are leading and lagging in the early minutes.
  Lines 5-6: Notable individual movers (gainers and losers) so far.
  Lines 7-8: How does this compare with what pre-market cues suggested? Confirm or contradict?
  Line 9:    Asian markets / USD-INR / crude — quick context.
  Line 10:   What to watch in the next half-hour.

RULES:
  1. USE ONLY the data provided. Do not invent numbers, news, or events.
  2. State the opening direction plainly. No prediction theatrics.
  3. Do NOT give buy/sell advice. Educational content only.
  4. Use Rs. for currency.
  5. Keep it tight — exactly around 10 lines. No filler.

=== DATA AT 09:30 IST ({date}) ===
Timestamp: {timestamp}

PRE-MARKET CONTEXT (what we said this morning):
{pre_context}

INDEX (live):
  Sensex: {sensex}
  Nifty 50: {nifty}

SECTOR PERFORMANCE (live):
{sectors}

TOP MOVERS (live, by magnitude):
{top_stocks}

ASIA-PACIFIC (still trading):
{asia_pacific}

CURRENCIES:
{currencies}

COMMODITIES:
{commodities}

Now write the 10-line opening commentary:"""


INTRADAY_UPDATE_PROMPT = """You are a senior Indian equity market analyst writing an INTRADAY UPDATE for MoneyVeda. The NSE session is in progress. Current time: {timestamp}, slot: {slot} IST.

YOUR TASK:
Write a CRISP 10-LINE update on what has CHANGED since the last update at {prev_slot} IST. This is a delta read, not a full recap. Focus on the move in the last 30 minutes, sector rotation, and any fresh themes. Use natural paragraphs (no bullet points, no headers).

STRUCTURE (approximately):
  Lines 1-2: Where is Nifty now vs the {prev_slot} reading. Direction and magnitude of the move in this half-hour.
  Lines 3-4: Which sectors moved, which stalled, which reversed since {prev_slot}.
  Lines 5-6: Names that have come into focus — fresh gainers or new losers in this slot.
  Line 7:    USD-INR / crude / gold context if it shifted.
  Line 8:    What's the prevailing tone now — risk-on, risk-off, choppy, range-bound?
  Lines 9-10: What to watch in the next half-hour.

RULES:
  1. Treat this as a CONTINUATION. Reference the prior slot ({prev_slot}) where the move warrants it.
  2. USE ONLY the data provided. Do not invent numbers, news, or events.
  3. If the market is essentially unchanged from {prev_slot}, say so plainly — don't manufacture drama.
  4. Do NOT give buy/sell advice. Educational content only.
  5. Use Rs. for currency.

=== DATA AT {slot} IST ({date}) ===
Timestamp: {timestamp}

PREVIOUS SLOT ({prev_slot} IST) — what we said:
{prev_context}

PREVIOUS NIFTY READING: {prev_nifty_summary}

INDEX (live now):
  Sensex: {sensex}
  Nifty 50: {nifty}

SECTOR PERFORMANCE (live now, vs prev close):
{sectors}

TOP MOVERS (live now, by magnitude):
{top_stocks}

CURRENCIES:
{currencies}

COMMODITIES:
{commodities}

ASIA-PACIFIC (if still trading):
{asia_pacific}

Now write the 10-line {slot} IST intraday update:"""


POST_MARKET_PROMPT = """You are a senior Indian equity market analyst writing a POST-MARKET wrap-up for MoneyVeda — a free financial platform for Indian retail investors. NSE closed at 3:30 PM IST today.

YOUR TASK:
Write a 20-line plain-English wrap-up of what happened in Indian markets today. Use natural paragraphs (no bullet points, no headers). Write as if explaining to a friend who invests casually.

STRUCTURE (approximately):
  Lines 1-3:  Lead with the big picture — how did Nifty/Sensex close and what's the tone?
  Lines 4-7:  Sector winners and losers — which sectors led, which lagged, and why.
  Lines 8-12: Top individual stock movers — name a few notable gainers and decliners with context.
  Lines 13-16: Key news/filings/events that influenced the day.
  Lines 17-18: Currency and commodity context (USD/INR, crude, gold).
  Line 19:    What to watch heading into tomorrow.
  Line 20:    One-line takeaway for a retail investor.

RULES:
  1. USE ONLY the data provided. Do not invent numbers, news, or events.
  2. Connect stock moves to broader themes where possible (e.g., "bank stocks fell as yields rose").
  3. Do NOT give buy/sell advice. Educational content only.
  4. Use Rs. for currency.
  5. If a theme isn't obvious from the data, don't force a narrative — state the facts plainly.
  6. Be honest about uncertainty ("appears to have been driven by...", not "was driven by...").

=== DATA FOR TODAY ({date}) ===
Timestamp: {timestamp}

INDEX CLOSE:
  Sensex: {sensex}
  Nifty 50: {nifty}

SECTOR PERFORMANCE:
{sectors}

TOP STOCK MOVERS (sorted by % change magnitude):
{top_stocks}

CURRENCIES:
{currencies}

COMMODITIES:
{commodities}

US MARKET STATUS (pre-open in New York):
{us_status}

TODAY'S NSE FILINGS (first 10):
{filings}

Now write the 20-line post-market commentary:"""


def build_pre_market_prompt(packet: dict) -> str:
    return PRE_MARKET_PROMPT.format(
        date         = packet["date"],
        timestamp    = packet["timestamp_ist"],
        us_markets   = _format_ticker_list(packet.get("us_markets",   [])),
        us_tech      = _format_ticker_list(packet.get("us_tech",      [])),
        asia_pacific = _format_ticker_list(packet.get("asia_pacific", [])),
        currencies   = _format_ticker_list(packet.get("currencies",   [])),
        commodities  = _format_ticker_list(packet.get("commodities",  [])),
        crypto       = _format_ticker_list(packet.get("crypto",       [])),
        india_prev   = _format_ticker_list(packet.get("india_prev",   [])),
    )


def build_post_market_prompt(packet: dict) -> str:
    return POST_MARKET_PROMPT.format(
        date        = packet["date"],
        timestamp   = packet["timestamp_ist"],
        sensex      = format_ticker_line(packet.get("sensex")),
        nifty       = format_ticker_line(packet.get("nifty")),
        sectors     = _format_ticker_list(packet.get("sectors",     [])),
        top_stocks  = _format_ticker_list(packet.get("top_stocks",  [])),
        currencies  = _format_ticker_list(packet.get("currencies",  [])),
        commodities = _format_ticker_list(packet.get("commodities", [])),
        us_status   = _format_ticker_list(packet.get("us_status",   [])),
        filings     = summarize_filings(packet.get("filings",       [])),
    )


def build_intraday_prompt(packet: dict) -> str:
    prior = packet.get("prior", {}) or {}
    if packet.get("is_opening"):
        pre_ctx = prior.get("pre_text") or "(pre-market commentary not available — describe the opening on its own merits)"
        return INTRADAY_OPENING_PROMPT.format(
            date         = packet["date"],
            timestamp    = packet["timestamp_ist"],
            pre_context  = pre_ctx,
            sensex       = format_ticker_line(packet.get("sensex")),
            nifty        = format_ticker_line(packet.get("nifty")),
            sectors      = _format_ticker_list(packet.get("sectors",      [])),
            top_stocks   = _format_ticker_list(packet.get("top_stocks",   [])),
            asia_pacific = _format_ticker_list(packet.get("asia_pacific", [])),
            currencies   = _format_ticker_list(packet.get("currencies",   [])),
            commodities  = _format_ticker_list(packet.get("commodities",  [])),
        )
    # Update slots — need a previous slot reference
    prev_slot = prior.get("prev_slot") or "the prior slot"
    prev_ctx  = prior.get("prev_text") or "(no prior slot found — write as a fresh update for this time)"
    prev_pct  = prior.get("prev_nifty_pct")
    prev_summary = (f"{prev_pct:+.2f}% vs yesterday close" if isinstance(prev_pct, (int, float))
                    else "not recorded")
    return INTRADAY_UPDATE_PROMPT.format(
        date            = packet["date"],
        timestamp       = packet["timestamp_ist"],
        slot            = packet["slot"],
        prev_slot       = prev_slot,
        prev_context    = prev_ctx,
        prev_nifty_summary = prev_summary,
        sensex          = format_ticker_line(packet.get("sensex")),
        nifty           = format_ticker_line(packet.get("nifty")),
        sectors         = _format_ticker_list(packet.get("sectors",      [])),
        top_stocks      = _format_ticker_list(packet.get("top_stocks",   [])),
        currencies      = _format_ticker_list(packet.get("currencies",   [])),
        commodities     = _format_ticker_list(packet.get("commodities",  [])),
        asia_pacific    = _format_ticker_list(packet.get("asia_pacific", [])),
    )


# ─────────────────────────────────────────────────────────────────────────────
# GEMINI CALL — with mode-aware token limit
# ─────────────────────────────────────────────────────────────────────────────
def call_gemini(prompt: str, max_tokens: int = 900):
    if not GEMINI_AVAILABLE:
        _log("⚠️", "google-generativeai package not installed")
        return None, "error"
    if not GEMINI_API_KEY:
        _log("⚠️", "GEMINI_API_KEY not set")
        return None, "error"
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(GEMINI_MODEL)
        _log("🧠", f"Calling Gemini ({GEMINI_MODEL}, max_tokens={max_tokens})...")
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature":       0.5,
                "max_output_tokens": max_tokens,
                "top_p":             0.9,
            },
            request_options={"timeout": 30},
        )
        if response and response.text:
            text = response.text.strip()
            if len(text) < 80:
                _log("⚠️", f"Gemini returned too-short text ({len(text)} chars)")
                return None, "error"
            _log("✅", f"Gemini returned {len(text)} characters")
            return text, "gemini"
        _log("⚠️", "Gemini returned empty response")
        return None, "error"
    except Exception as e:
        _log("⚠️", f"Gemini API error: {e}")
        return None, "error"


# ─────────────────────────────────────────────────────────────────────────────
# RULE-BASED FALLBACKS
# ─────────────────────────────────────────────────────────────────────────────
def fallback_pre_market(packet: dict) -> str:
    us = packet.get("us_markets", [])
    dow    = next((t for t in us if t.get("label") == "DOW JONES"), None)
    nasdaq = next((t for t in us if t.get("label") == "NASDAQ"),    None)
    sp     = next((t for t in us if t.get("label") == "S&P 500"),   None)
    mood = "mixed"
    if dow and nasdaq and sp:
        avg_pct = (dow["pct"] + nasdaq["pct"] + sp["pct"]) / 3
        if avg_pct > 0.5:    mood = "positive"
        elif avg_pct < -0.5: mood = "negative"
    lines = [
        f"Good morning. Global cues look {mood} as Indian markets prepare for today's session.",
    ]
    if dow and nasdaq and sp:
        lines.append(
            f"Overnight on Wall Street, the Dow closed at {dow['value']:,.0f} ({dow['pct']:+.2f}%), "
            f"Nasdaq at {nasdaq['value']:,.0f} ({nasdaq['pct']:+.2f}%), and S&P 500 at "
            f"{sp['value']:,.0f} ({sp['pct']:+.2f}%)."
        )
    lines += [
        "Asian markets are taking cues from overnight US action.",
        "Commodity prices and the dollar index will influence sector-specific moves in India today.",
        "Nifty is likely to open in line with these global cues — watch the first 15 minutes for direction.",
        "This is an educational summary based on publicly available market data. Not investment advice.",
    ]
    return " ".join(lines)


def fallback_intraday(packet: dict) -> str:
    nifty = packet.get("nifty")
    sectors = packet.get("sectors", [])
    top = packet.get("top_stocks", [])
    slot = packet.get("slot", "now")
    lines = []
    if nifty:
        direction = "up" if nifty["pct"] >= 0 else "down"
        lines.append(f"At {slot} IST, Nifty 50 is {direction} {abs(nifty['pct']):.2f}% at {nifty['value']:,.2f}.")
    if sectors:
        leader = max(sectors, key=lambda s: s.get("pct", 0))
        laggard = min(sectors, key=lambda s: s.get("pct", 0))
        lines.append(f"Sector leadership: {leader['label']} ({leader['pct']:+.2f}%); laggard: {laggard['label']} ({laggard['pct']:+.2f}%).")
    if top:
        gainers = [s for s in top if s.get("pct", 0) > 0][:2]
        losers  = [s for s in top if s.get("pct", 0) < 0][:2]
        if gainers:
            lines.append("Top gainers: " + ", ".join(f"{s['label']} ({s['pct']:+.2f}%)" for s in gainers) + ".")
        if losers:
            lines.append("Notable declines: " + ", ".join(f"{s['label']} ({s['pct']:+.2f}%)" for s in losers) + ".")
    lines.append("Educational summary based on live market data. Not investment advice.")
    return " ".join(lines)


def fallback_post_market(packet: dict) -> str:
    nifty  = packet.get("nifty")
    sensex = packet.get("sensex")
    lines = []
    if nifty:
        d = "rose" if nifty["pct"] >= 0 else "fell"
        lines.append(f"Nifty {d} {abs(nifty['pct']):.2f}% to close at {nifty['value']:,.2f} today.")
    if sensex:
        d = "rose" if sensex["pct"] >= 0 else "fell"
        lines.append(f"Sensex {d} {abs(sensex['pct']):.2f}% to {sensex['value']:,.2f}.")
    sectors = packet.get("sectors", [])
    if sectors:
        winners = sorted([s for s in sectors if s.get("pct", 0) > 0], key=lambda s: s["pct"], reverse=True)
        losers  = sorted([s for s in sectors if s.get("pct", 0) < 0], key=lambda s: s["pct"])
        if winners:
            lines.append(f"Among sector indices, {winners[0]['label']} led with {winners[0]['pct']:+.2f}%.")
        if losers:
            lines.append(f"{losers[0]['label']} dragged the most at {losers[0]['pct']:+.2f}%.")
    top = packet.get("top_stocks", [])
    if top:
        gainers = [s for s in top if s.get("pct", 0) > 0][:2]
        losers  = [s for s in top if s.get("pct", 0) < 0][:2]
        if gainers:
            lines.append("Top gainers: " + ", ".join(f"{s['label']} ({s['pct']:+.2f}%)" for s in gainers) + ".")
        if losers:
            lines.append("Notable declines: " + ", ".join(f"{s['label']} ({s['pct']:+.2f}%)" for s in losers) + ".")
    lines.append("This is an educational summary based on publicly available market data. Not investment advice.")
    return " ".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# SUPABASE CACHE WRITE — schema v2 (slot_time column required)
# ─────────────────────────────────────────────────────────────────────────────
def save_commentary(commentary_type: str, slot: str, text: str, source: str, packet: dict) -> bool:
    if not supabase:
        _log("⚠️", "Supabase not configured — skipping save")
        return False
    try:
        date = _today_ist()
        # slot stored as TIME 'HH:MM:00'
        slot_full = f"{slot}:00"
        supabase.table("market_commentary").upsert(
            {
                "commentary_type": commentary_type,    # 'pre' | 'intraday' | 'post'
                "commentary_date": date,
                "slot_time":       slot_full,
                "commentary_text": text,
                "source":          source,
                "data_snapshot":   json.dumps(packet, default=str),
            },
            on_conflict="commentary_type,commentary_date,slot_time",
        ).execute()
        _log("💾", f"Saved {commentary_type} commentary for {date} {slot} (source={source})")
        return True
    except Exception as e:
        _log("⚠️", f"Supabase save failed: {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# ORCHESTRATION
# ─────────────────────────────────────────────────────────────────────────────
def generate_commentary(mode: str, slot: str = None, dry_run: bool = False):
    _log("🚀", f"Starting {mode.upper()} commentary generation (slot={slot})")
    _log("📅", f"IST now: {_now_ist_str()}")

    if mode == "pre":
        slot   = slot or PRE_SLOT
        packet = build_pre_market_packet()
        prompt = build_pre_market_prompt(packet)
        max_tokens = 900
    elif mode == "post":
        slot   = slot or POST_SLOT
        packet = build_post_market_packet()
        prompt = build_post_market_prompt(packet)
        max_tokens = 900
    elif mode == "intraday":
        # Validate / snap slot
        if slot is None:
            now = datetime.now(IST)
            slot = _snap_to_intraday_slot(now.hour, now.minute)
        elif slot not in INTRADAY_SLOTS:
            _log("⚠️", f"Slot {slot} not in canonical list — snapping")
            sh, sm = map(int, slot.split(":"))
            slot = _snap_to_intraday_slot(sh, sm)
        packet = build_intraday_packet(slot)
        prompt = build_intraday_prompt(packet)
        max_tokens = 500   # 10-line target — keeps output tight + costs lower
    else:
        _log("❌", f"Unknown mode: {mode}")
        return None

    # Sanity check — bail if data is too thin
    total_datapoints = sum(
        len(v) if isinstance(v, list) else (1 if v and not isinstance(v, dict) else 0)
        for v in packet.values()
    )
    if total_datapoints < 4:
        _log("❌", f"Data packet too thin ({total_datapoints} items). Skipping.")
        return None

    if dry_run:
        print("\n" + "=" * 70)
        print(f"DRY RUN — prompt for {mode} {slot}:")
        print("=" * 70)
        print(prompt)
        print("=" * 70)

    text, source = call_gemini(prompt, max_tokens=max_tokens)

    if not text:
        _log("🔁", "Gemini failed — using rule-based fallback")
        if mode == "pre":
            text = fallback_pre_market(packet)
        elif mode == "intraday":
            text = fallback_intraday(packet)
        else:
            text = fallback_post_market(packet)
        source = "rule_based"

    print("\n" + "=" * 70)
    print(f"{mode.upper()} {slot} COMMENTARY  ({source})")
    print("=" * 70)
    print(text)
    print("=" * 70 + "\n")

    if dry_run:
        _log("🏁", "Dry run complete — nothing saved")
        return {"text": text, "source": source, "saved": False, "slot": slot}

    saved = save_commentary(mode, slot, text, source, packet)
    return {"text": text, "source": source, "saved": saved, "slot": slot}


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="MoneyVeda Market Commentary v2.0")
    parser.add_argument("--mode", choices=["pre", "intraday", "post", "auto"], default="auto",
                        help="'auto' detects from current IST time (default)")
    parser.add_argument("--slot", default=None,
                        help="Intraday slot HH:MM (e.g. 10:30). Optional — auto-detected if omitted.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print prompt and output but do not save to Supabase")
    args = parser.parse_args()

    # Resolve mode
    mode = args.mode
    slot = args.slot
    if mode == "auto":
        mode, auto_slot = detect_mode_and_slot()
        slot = slot or auto_slot
        _log("🤖", f"Auto-detected: mode={mode}, slot={slot}")

    # Validate environment
    missing = []
    if not SUPABASE_URL:        missing.append("SUPABASE_URL")
    if not SUPABASE_SECRET_KEY: missing.append("SUPABASE_SECRET_KEY")
    if not GEMINI_API_KEY:      missing.append("GEMINI_API_KEY")
    if missing and not args.dry_run:
        print(f"❌ Missing env vars: {', '.join(missing)}")
        sys.exit(1)

    result = generate_commentary(mode, slot=slot, dry_run=args.dry_run)
    if not result:
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
