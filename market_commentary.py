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


def _last_trading_day_ist():
    """
    Returns the most recent trading day BEFORE today (IST).
    Simple Mon-Fri logic — doesn't account for India-specific holidays yet.
    On Monday returns last Friday; otherwise yesterday.
    Returns a date object.
    """
    today = datetime.now(IST).date()
    # weekday(): Mon=0 ... Sun=6
    if today.weekday() == 0:        # Monday → last Friday
        return today - timedelta(days=3)
    elif today.weekday() == 6:      # Sunday → last Friday
        return today - timedelta(days=2)
    elif today.weekday() == 5:      # Saturday → last Friday
        return today - timedelta(days=1)
    else:                            # Tue-Fri → yesterday
        return today - timedelta(days=1)


def _last_session_label() -> str:
    """
    Returns the natural-language reference to the most recent trading day.
    'Friday' on Monday, 'yesterday' on Tue-Fri, 'Friday' on weekends.
    Used in prompts to avoid Gemini saying 'yesterday' when it means Friday.
    """
    today_dow = datetime.now(IST).weekday()
    if today_dow == 0:               # Monday
        return "Friday's"
    elif today_dow == 5 or today_dow == 6:   # Saturday or Sunday
        return "Friday's"
    else:
        return "yesterday's"


def _overnight_label() -> str:
    """
    Returns the natural-language reference to the most recent US close.
    On Monday morning, the US close was Friday afternoon — calling that
    'overnight' is wrong. On other days, US close was actually overnight.
    """
    today_dow = datetime.now(IST).weekday()
    if today_dow == 0:               # Monday
        return "Friday's US close"
    elif today_dow == 5 or today_dow == 6:
        return "Friday's US close"
    else:
        return "overnight US session"


def _next_session_label() -> str:
    """
    Returns the natural-language reference to the next trading session.
    On Friday's post-market wrap, 'tomorrow' is wrong — should be 'Monday'.
    """
    today_dow = datetime.now(IST).weekday()
    if today_dow == 4:               # Friday → next session Monday
        return "Monday"
    elif today_dow == 5:             # Saturday → still Monday
        return "Monday"
    elif today_dow == 6:             # Sunday → still Monday
        return "Monday"
    else:
        return "tomorrow"


def _day_of_week_ist() -> str:
    return datetime.now(IST).strftime("%A")


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
      "all_slots_compact": str | None,   # NEW: compact summary of all earlier slots today
      "yesterday_post_text": str | None, # NEW: yesterday's post-market wrap (cross-day memory)
    }
    """
    out = {
        "pre_text": None, "prev_slot": None, "prev_text": None,
        "prev_nifty_pct": None, "all_slots_compact": None,
        "yesterday_post_text": None,
    }
    if not supabase:
        return out
    try:
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

        # ALL intraday slots before current_slot (newest first)
        prev_all = (
            supabase.table("market_commentary")
            .select("slot_time, commentary_text, data_snapshot")
            .eq("commentary_type", "intraday")
            .eq("commentary_date", today)
            .lt("slot_time", current_slot + ":00")
            .order("slot_time", desc=True)
            .execute()
        )
        if prev_all.data:
            row = prev_all.data[0]
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

            # Compact summary of EVERY earlier slot today — used for memory continuity.
            slot_lines = []
            for r in reversed(prev_all.data):  # oldest first for natural reading
                slot_label = (r.get("slot_time") or "")[:5]
                txt = (r.get("commentary_text") or "")[:280]
                pct_str = ""
                try:
                    sn = r.get("data_snapshot")
                    if isinstance(sn, str): sn = json.loads(sn)
                    if isinstance(sn, dict):
                        n = sn.get("nifty")
                        if isinstance(n, dict) and n.get("pct") is not None:
                            pct_str = f" ({n['pct']:+.2f}%)"
                except Exception:
                    pass
                first_sentence = txt.split(".")[0].strip()
                if len(first_sentence) > 220:
                    first_sentence = first_sentence[:220]
                slot_lines.append(f"  {slot_label}{pct_str}: {first_sentence}")
            if slot_lines:
                out["all_slots_compact"] = "\n".join(slot_lines)

        # Yesterday's post-market wrap (look back up to 5 days for weekends/holidays)
        try:
            today_dt = datetime.strptime(today, "%Y-%m-%d").date()
            for days_back in range(1, 6):
                check_date = (today_dt - timedelta(days=days_back)).strftime("%Y-%m-%d")
                yres = (
                    supabase.table("market_commentary")
                    .select("commentary_text, commentary_date")
                    .eq("commentary_type", "post")
                    .eq("commentary_date", check_date)
                    .limit(1)
                    .execute()
                )
                if yres.data:
                    txt = (yres.data[0].get("commentary_text") or "")[:1200]
                    out["yesterday_post_text"] = f"[{check_date}] {txt}"
                    break
        except Exception:
            pass
    except Exception as e:
        _log("⚠️", f"Prior context fetch failed: {e}")
    return out


# ─────────────────────────────────────────────────────────────────────────────
# TECHNICAL ANALYSIS HELPERS  (Phase 1 depth — yfinance OHLC + math)
# ─────────────────────────────────────────────────────────────────────────────
# Computes the depth signals that distinguish "describe today" commentary from
# "interpret what's happening" commentary. All numbers are derived from data we
# already have access to via yfinance — no NSE scraping, no paid feeds.

try:
    import yfinance as _yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False


def _compute_index_technicals(yahoo_symbol: str) -> dict:
    """
    Pull ~90-day daily OHLC for an index/stock and compute a technical context
    block. Returns {} on any error so callers can degrade gracefully.
    """
    if not YFINANCE_AVAILABLE:
        return {}
    try:
        t = _yf.Ticker(yahoo_symbol)
        hist = t.history(period="90d", interval="1d")
        if hist is None or hist.empty or len(hist) < 30:
            return {}
        closes  = hist["Close"]
        volumes = hist["Volume"]
        last    = float(closes.iloc[-1])

        ma_20 = float(closes.tail(20).mean())
        ma_50 = float(closes.tail(50).mean()) if len(closes) >= 50 else None

        # 52-week proxy via separate longer fetch
        try:
            hist_year = t.history(period="1y", interval="1d")
            if hist_year is not None and not hist_year.empty:
                year_closes = hist_year["Close"]
                high_52w = float(year_closes.max())
                low_52w  = float(year_closes.min())
            else:
                high_52w = float(closes.max())
                low_52w  = float(closes.min())
        except Exception:
            high_52w = float(closes.max())
            low_52w  = float(closes.min())

        c5  = float(closes.iloc[-6])  if len(closes) >= 6  else last
        c30 = float(closes.iloc[-31]) if len(closes) >= 31 else last
        trend_5d_pct  = ((last - c5)  / c5)  * 100 if c5  else 0
        trend_30d_pct = ((last - c30) / c30) * 100 if c30 else 0

        avg_vol_30d = float(volumes.tail(30).mean()) if volumes.tail(30).sum() > 0 else 0
        today_vol   = float(volumes.iloc[-1])
        vol_ratio   = (today_vol / avg_vol_30d) if avg_vol_30d > 0 else None

        # Support/resistance: 30-day pivot zones via percentile of swings
        recent = hist.tail(30)
        recent_lows  = sorted([float(x) for x in recent["Low"].tolist()])
        recent_highs = sorted([float(x) for x in recent["High"].tolist()], reverse=True)
        idx_low  = max(0, int(len(recent_lows)  * 0.10))
        idx_high = max(0, int(len(recent_highs) * 0.10))
        support_30d    = recent_lows[idx_low]   if recent_lows  else None
        resistance_30d = recent_highs[idx_high] if recent_highs else None

        return {
            "last":              round(last, 2),
            "ma_20":             round(ma_20, 2),
            "ma_50":             round(ma_50, 2) if ma_50 else None,
            "vs_ma_20_pct":      round((last - ma_20) / ma_20 * 100, 2) if ma_20 else None,
            "vs_ma_50_pct":      round((last - ma_50) / ma_50 * 100, 2) if ma_50 else None,
            "high_52w":          round(high_52w, 2),
            "low_52w":           round(low_52w, 2),
            "pct_from_52w_high": round((last - high_52w) / high_52w * 100, 2) if high_52w else None,
            "pct_from_52w_low":  round((last - low_52w)  / low_52w  * 100, 2) if low_52w  else None,
            "trend_5d_pct":      round(trend_5d_pct, 2),
            "trend_30d_pct":     round(trend_30d_pct, 2),
            "today_vol_vs_avg":  round(vol_ratio, 2) if vol_ratio else None,
            "support_30d":       round(support_30d, 2)    if support_30d    else None,
            "resistance_30d":    round(resistance_30d, 2) if resistance_30d else None,
        }
    except Exception as e:
        _log("⚠️", f"Technicals fetch failed for {yahoo_symbol}: {e}")
        return {}


def get_market_breadth() -> dict:
    """
    Compute advance/decline ratio + breadth descriptor from the Render Nifty 100 cache.
    """
    out = {
        "advances": 0, "declines": 0, "unchanged": 0,
        "ad_ratio": None, "breadth_descriptor": "n/a",
    }
    try:
        cache_url = "https://finance-bxyf.onrender.com/api/market-cache"
        r = requests.get(cache_url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        data = r.json()
        tickers = data.get("tickers") or []
        if not tickers:
            return out
        adv = sum(1 for t in tickers if t.get("ok") and t.get("pct", 0) >  0.1)
        dec = sum(1 for t in tickers if t.get("ok") and t.get("pct", 0) < -0.1)
        unc = sum(1 for t in tickers if t.get("ok") and abs(t.get("pct", 0)) <= 0.1)
        out["advances"]  = adv
        out["declines"]  = dec
        out["unchanged"] = unc
        if dec > 0:
            out["ad_ratio"] = round(adv / dec, 2)
        if   adv > dec * 2:  out["breadth_descriptor"] = "broad-based rally (>2:1 advancers)"
        elif adv > dec:      out["breadth_descriptor"] = "more advancers than decliners"
        elif dec > adv * 2:  out["breadth_descriptor"] = "broad-based selling (>2:1 decliners)"
        elif dec > adv:      out["breadth_descriptor"] = "more decliners than advancers"
        else:                out["breadth_descriptor"] = "evenly split breadth"
    except Exception as e:
        _log("⚠️", f"Breadth fetch failed: {e}")
    return out


def _format_technicals(label: str, tech: dict) -> str:
    """Render the technicals dict into 4-5 dense lines for prompt input."""
    if not tech:
        return f"  {label}: (technicals unavailable)"
    lines = [f"  {label}: {tech.get('last', '?')} | "
             f"vs 20D MA: {tech.get('vs_ma_20_pct', 'n/a')}% | "
             f"vs 50D MA: {tech.get('vs_ma_50_pct', 'n/a')}%"]
    if tech.get("pct_from_52w_high") is not None:
        lines.append(f"    52W: {tech.get('pct_from_52w_high')}% from high {tech.get('high_52w')} | "
                     f"+{tech.get('pct_from_52w_low')}% from low {tech.get('low_52w')}")
    if tech.get("trend_5d_pct") is not None:
        lines.append(f"    Trend: 5D {tech.get('trend_5d_pct')}% | 30D {tech.get('trend_30d_pct')}%")
    if tech.get("support_30d") and tech.get("resistance_30d"):
        lines.append(f"    Recent 30D zone: support ~{tech.get('support_30d')}, "
                     f"resistance ~{tech.get('resistance_30d')}")
    if tech.get("today_vol_vs_avg") is not None:
        vol = tech.get("today_vol_vs_avg")
        if vol >= 1.5:    descr = "heavier than usual (institutional activity likely)"
        elif vol <= 0.7:  descr = "lighter than usual (low conviction session)"
        else:             descr = "in line with average"
        lines.append(f"    Volume: {vol}x 30D average ({descr})")
    return "\n".join(lines)


def _format_breadth(b: dict) -> str:
    if not b or (b.get("advances") == 0 and b.get("declines") == 0):
        return "  Breadth: [INSTRUCTION TO MODEL: Breadth ratio not available this slot. Infer conviction from sector dispersion (count green vs red sectors in the SECTOR PERFORMANCE block) and from top-mover skew (lopsided gainers vs losers). Do NOT mention that breadth is unavailable.]"
    return (f"  Breadth: {b.get('advances')} advancers vs {b.get('declines')} decliners "
            f"({b.get('breadth_descriptor')})")


# ─────────────────────────────────────────────────────────────────────────────
# NEWS HEADLINES (Pulse by Zerodha — pulse.zerodha.com/feed.php)
# ─────────────────────────────────────────────────────────────────────────────
# Aggregates real-time Indian financial news from ET, NDTV Profit, The Hindu,
# Mint, BS, MoneyControl etc. Free RSS feed. Used as CONTEXT input for Gemini —
# headlines never appear verbatim in the user-facing commentary (transformative
# use of public headlines for original analysis).
#
# Polling: max once per slot = ~15-20 calls/day. Honest User-Agent. No storage.

import xml.etree.ElementTree as _ET
from html import unescape as _html_unescape

PULSE_FEED_URL = "http://pulse.zerodha.com/feed.php"
PULSE_HEADERS = {
    "User-Agent": (
        "MoneyVeda/2.0 MarketCommentary "
        "(https://moneyveda.org; analysis context use; contact via website)"
    )
}

# Keyword filter — passed only headlines matching these markers go to Gemini.
# Drops sports/lifestyle/general news that pollute the feed.
_PULSE_RELEVANCE_HITS = {
    # Index/market terms
    "nifty", "sensex", "nse", "bse", "stock market", "indian market",
    "stocks", "shares", "equity", "equities", "index", "indices",
    "trading guide", "ahead of market", "market action",
    # Macro/policy
    "rbi", "sebi", "rupee", "fed", "inflation", "gdp", "policy", "rate", "rates",
    "fii", "dii", "monsoon", "budget", "fiscal",
    # Sector terms
    "bank", "banks", "banking", "it services", "pharma", "auto",
    "metals", "fmcg", "energy", "oil", "crude", "gold",
    # Common Indian large-caps + Nifty 100 names
    "reliance", "tcs", "infosys", "hdfc", "icici", "sbi", "bharti",
    "tata", "adani", "axis", "kotak", "wipro", "maruti", "ongc",
    "bajaj", "ultratech", "asian paints", "titan", "sun pharma",
    "ambuja", "coal india", "ntpc", "powergrid", "nestle", "hindustan unilever",
    "vodafone", "vodafone idea", "vi", "airtel", "indigo", "zomato", "eternal",
    "paytm", "amazon", "flipkart", "swiggy", "ola",
    "drreddy", "dr reddy", "cipla", "lupin", "torrent",
    "jsw", "jindal", "vedanta", "hindalco", "nalco",
    "bel", "hal", "siemens", "abb", "havells",
    "lic", "shriram", "muthoot", "cholamandalam",
    "mittal", "arcelormittal", "mahindra", "ambani",
    "gujarat fluoro", "kalyani steel", "time techno", "shyam metalic",
    "uco bank", "central bank", "punjab national", "canara",
    "federal bank", "indusind", "yes bank", "idbi",
    "godrej", "marico", "dabur", "britannia",
    # Earnings / corporate actions
    "results", "earnings", "profit", "loss", "dividend", "bonus",
    "split", "buyback", "ipo", "qip", "merger", "acquisition",
    "stake", "deal", "valuation", "demerger",
    # Brokerage/analyst signals
    "buy call", "sell call", "target price", "upgrade", "downgrade",
    "brokerage", "rating", "outlook", "guidance",
    "bullish", "bearish", "bullish on", "bearish on",
    # General market conditions
    "rally", "selloff", "crash", "volatility", "correction",
    "breakout", "support", "resistance", "all-time high", "52-week",
    # Geopolitics affecting Indian markets (crude/USD/risk-off)
    "iran", "hormuz", "tehran", "opec", "sanctions",
    "russia", "ukraine", "china trade", "tariff",
    # Political / electoral events (often material for Indian markets)
    "election", "elections", "exit poll", "counting", "results day",
    "bjp", "congress", "modi", "verdict", "majority", "lead", "trailing",
    "state assembly", "lok sabha", "general election", "by-election",
    "cabinet", "parliament",
    # Macro / policy events
    "monetary policy", "repo rate", "rbi mpc", "rbi minutes",
    "fed minutes", "fed meeting", "fomc",
    "cpi data", "cpi inflation", "wpi", "iip", "gdp data", "trade deficit",
    "fiscal deficit", "current account",
    # Earnings season
    "q1 results", "q2 results", "q3 results", "q4 results",
    "results announcement", "earnings result", "guidance",
    "results day", "result preview",
}


def _parse_pubdate(raw: str):
    """Parse RSS pubDate to a UTC-aware datetime; return None on failure."""
    if not raw:
        return None
    raw = raw.strip()
    # RFC 822 / RFC 2822 e.g. 'Sun, 03 May 2026 17:44:16 +0530'
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def _is_market_relevant(title: str, summary: str) -> bool:
    """True if the headline contains any market-relevance keyword."""
    blob = f"{title} {summary}".lower()
    return any(k in blob for k in _PULSE_RELEVANCE_HITS)


def get_pulse_headlines(max_age_hours: int = 12, limit: int = 12) -> list:
    """
    Fetch + filter Pulse news. Returns up to `limit` market-relevant headlines
    from the last `max_age_hours` hours, newest first.

    Each item: {"title": str, "summary": str, "source": str, "minutes_ago": int}

    Returns [] on any failure — callers must handle gracefully.
    """
    try:
        r = requests.get(PULSE_FEED_URL, headers=PULSE_HEADERS, timeout=12)
        r.raise_for_status()
        root = _ET.fromstring(r.text)
        items = root.findall(".//item")
        if not items:
            return []

        now_utc = datetime.now(timezone.utc)
        cutoff  = now_utc - timedelta(hours=max_age_hours)
        out = []
        seen_titles = set()

        for it in items:
            title_el = it.find("title")
            desc_el  = it.find("description")
            link_el  = it.find("link")
            date_el  = it.find("pubDate")

            title   = _html_unescape((title_el.text or "").strip()) if title_el is not None else ""
            summary = _html_unescape((desc_el.text  or "").strip()) if desc_el  is not None else ""
            link    = (link_el.text or "").strip() if link_el is not None else ""
            pub_dt  = _parse_pubdate(date_el.text if date_el is not None else "")

            if not title or len(title) < 8:
                continue
            if pub_dt is None:
                continue
            # Convert to UTC-aware for comparison
            if pub_dt.tzinfo is None:
                pub_dt = pub_dt.replace(tzinfo=timezone.utc)
            if pub_dt < cutoff:
                continue
            if not _is_market_relevant(title, summary):
                continue

            # Dedupe by lowercase title (multiple sources sometimes carry the same story)
            tkey = title.lower()[:80]
            if tkey in seen_titles:
                continue
            seen_titles.add(tkey)

            # Extract source from link (e.g. economictimes.indiatimes.com -> "ET")
            source = "Pulse"
            try:
                if "economictimes" in link:    source = "ET"
                elif "moneycontrol" in link:   source = "MoneyControl"
                elif "ndtvprofit" in link:     source = "NDTV Profit"
                elif "thehindu" in link:       source = "The Hindu"
                elif "livemint" in link or "mint.com" in link: source = "Mint"
                elif "business-standard" in link: source = "BS"
                elif "reuters" in link:        source = "Reuters"
            except Exception:
                pass

            minutes_ago = max(0, int((now_utc - pub_dt).total_seconds() / 60))

            out.append({
                "title":       title[:200],
                "summary":     summary[:280],
                "source":      source,
                "minutes_ago": minutes_ago,
            })
            if len(out) >= limit:
                break

        _log("📰", f"Pulse: {len(out)} relevant headline(s) in last {max_age_hours}h")
        return out
    except Exception as e:
        _log("⚠️", f"Pulse fetch failed: {e}")
        return []


def _format_pulse_headlines(headlines: list) -> str:
    """Render for prompt input. Each line carries source + age for Gemini context."""
    if not headlines:
        return "  (no recent market news available)"
    lines = []
    for h in headlines:
        age = h.get("minutes_ago", 0)
        if   age < 60:        age_str = f"{age}m ago"
        elif age < 24 * 60:   age_str = f"{age // 60}h ago"
        else:                 age_str = f"{age // (24 * 60)}d ago"
        title = h.get("title", "").strip()
        src   = h.get("source", "Pulse")
        lines.append(f"  - [{src}, {age_str}] {title}")
    return "\n".join(lines)




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

    # ── Phase 1 depth additions ──
    # Technicals for Nifty 50, Bank Nifty, Nifty IT (key indices)
    packet["technicals"] = {
        "NIFTY 50":   _compute_index_technicals("^NSEI"),
        "NIFTY BANK": _compute_index_technicals("^NSEBANK"),
        "NIFTY IT":   _compute_index_technicals("^CNXIT"),
    }
    # India VIX (volatility regime indicator)
    packet["india_vix"] = _compute_index_technicals("^INDIAVIX")
    # Yesterday's post-market wrap for cross-day continuity
    prior = get_prior_intraday_context(packet["date"], "00:00")
    packet["yesterday_post_text"] = prior.get("yesterday_post_text")
    # Real-time Indian market news from Pulse (last 12h, max 12 headlines)
    packet["news"] = get_pulse_headlines(max_age_hours=12, limit=12)

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

    # ── Phase 1 depth additions ──
    packet["technicals"] = {
        "NIFTY 50":   _compute_index_technicals("^NSEI"),
        "NIFTY BANK": _compute_index_technicals("^NSEBANK"),
        "NIFTY IT":   _compute_index_technicals("^CNXIT"),
    }
    packet["india_vix"] = _compute_index_technicals("^INDIAVIX")
    packet["breadth"]   = get_market_breadth()
    # Real-time Indian market news from Pulse (last 6h for intraday — narrower window)
    packet["news"] = get_pulse_headlines(max_age_hours=6, limit=10)

    # Fetch prior context for narrative continuity (now extended with all-slots + yesterday)
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

    # ── Phase 1 depth additions ──
    packet["technicals"] = {
        "NIFTY 50":   _compute_index_technicals("^NSEI"),
        "NIFTY BANK": _compute_index_technicals("^NSEBANK"),
        "NIFTY IT":   _compute_index_technicals("^CNXIT"),
    }
    packet["india_vix"] = _compute_index_technicals("^INDIAVIX")
    packet["breadth"]   = get_market_breadth()
    # Real-time Indian market news from Pulse (last 12h for post-market — covers full day)
    packet["news"] = get_pulse_headlines(max_age_hours=12, limit=15)
    # Arc of the day — pull all today's intraday slots so post-market can review
    packet["prior"] = get_prior_intraday_context(packet["date"], "23:59")

    packet["filings"] = get_todays_filings()
    return packet


# ─────────────────────────────────────────────────────────────────────────────
# PROMPT TEMPLATES
# ─────────────────────────────────────────────────────────────────────────────
PRE_MARKET_PROMPT = """You are a senior equity strategist briefing the trading desk on Indian markets before the 9:15 AM IST open. Your audience is retail investors using MoneyVeda — they are smart but time-pressed and want analysis, not just data.

YOUR TASK:
Write a structured 18-22 line strategist briefing in plain English. The goal is INTERPRETATION, not description. Identify 2-3 dominant themes; place today's setup against the recent context (last week's range, last session's wrap); call out divergences worth watching; and give a clear directional bias for the open.

IMPORTANT: Today is {day_of_week} {date}. The most recent trading session was {india_session_label}. The most recent US close was {us_close_label}. Use these labels precisely — do NOT say "yesterday" or "overnight" if today is Monday or a post-holiday open. Use "Friday's" or "{india_session_label}" when that's the accurate reference.

STRUCTURE (use markdown headers exactly as shown — frontend renders them):

**Setup**
2-3 lines on the dominant narrative from {us_close_label} and what it means for today's open. Don't just describe US closes — interpret them. Note any major divergence from {india_session_label} domestic tone.

**Global Context**
3-4 lines covering US close (Dow/Nasdaq/S&P with one driver each), Asian markets this morning, USD/INR direction, and crude. Connect movements where causally relevant (e.g., "weak crude pressuring upstream names; tailwind for OMCs").

**Technical Position**
3-4 lines on Nifty's recent range, where it sits relative to 20D/50D moving averages, the support and resistance zones, and India VIX level. Use specific levels: e.g. "Nifty closed {india_session_label} at X, with 23,950 having held twice last week as support."

**Themes to Watch**
3-4 lines on 2-3 themes likely to drive today's session — sector rotation continuation, an upcoming event, a divergence between sectors, etc. Reference {india_session_label} wrap if relevant.

**Bias**
2 lines: directional view for the open (positive / mixed / cautious / negative) with the level that confirms or invalidates the view. Frame as expectation, not certainty.

**Takeaway**
One sentence — what should a retail investor watch in the first 30 minutes.

RULES:
1. USE ONLY data provided. Do not invent numbers, levels, news, or events.
2. Reference SPECIFIC LEVELS where the data supports it (e.g., "23,950", "+1.4% above 20D MA").
3. Frame predictions as expectation, not certainty ("likely to", "should test", "watch for").
4. NO buy/sell advice on individual stocks. Educational analysis only.
5. Use Rs. for currency.
6. If you don't have enough data for a section, do NOT confess the gap to the reader. Quietly omit, or use the data you DO have. Never write "data unavailable" or "while not explicitly provided".
7. Voice: confident, specific, professional. Like a desk strategist, not a TV anchor.
8. ANTI-HEDGING: Avoid filler phrases like "possibly", "appears to", "suggesting a potential", "ongoing concerns". When the data supports a claim, state it directly. Examples:
   - WEAK: "Auto outperformed, suggesting a potential rotation into cyclical names."
   - STRONG: "Auto's 1.93% rally alongside FMCG weakness (HUL -1.94%, ITC -1.06%) confirms defensive-to-cyclical rotation."
   - WEAK: "IT lagged, possibly reflecting ongoing concerns in the technology space."
   - STRONG: "IT lagged with TCS -1.4% and Wipro -0.88% — overnight Nasdaq weakness translating to Indian IT names."

=== DATA FOR TODAY ({date}) ===
Timestamp: {timestamp}

US MARKETS ({us_close_label}):
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

INDIA — {india_session_label_caps} CLOSE:
{india_prev}

INDIA TECHNICAL POSITION:
{technicals_block}

INDIA VIX (volatility regime):
{vix_line}

{last_session_wrap_label} POST-MARKET WRAP (for continuity):
{yesterday_wrap}

RECENT MARKET NEWS HEADLINES (last 12 hours, from Indian financial press via Pulse):
{news_block}

These headlines are CONTEXT to weave into the briefing. Categories that are usually MATERIAL and worth citing if present:
- Election results, exit polls, political shifts (BJP/Congress/state polls)
- RBI announcements, monetary policy, repo rate moves
- Major company news (results, M&A, regulatory action against named Nifty names)
- Brokerage upgrades/downgrades on specific stocks
- Macro events (Budget, CPI/IIP/GDP data, Fed meetings)
- Geopolitical flashpoints affecting crude or risk appetite (Iran, Russia, China trade)

Categories that are usually NOISE and should be ignored: sports, lifestyle, crime, IPL, entertainment.

Rules: Do NOT cite headlines verbatim. Do NOT invent causation. But DO connect material headlines to specific themes in your briefing — if BJP wins state elections and the index is gapping up, say so directly.

Now write the strategist pre-market briefing:"""


INTRADAY_OPENING_PROMPT = """You are a senior equity strategist writing the FIRST INTRADAY UPDATE of the day for MoneyVeda. NSE opened at 9:15 AM IST. It is now {timestamp}, slot 09:30 IST.

IMPORTANT: Today is {day_of_week} {date}. The most recent prior trading session was {india_session_label} (NOT "yesterday" if today is Monday or post-holiday). Use "{india_session_label}" or "Friday's" precisely — never substitute "yesterday" when that's inaccurate.

YOUR TASK:
Write a structured 10-12 line briefing on how the opening 15 minutes played out. The KEY angle: did the market open as the pre-market expected, or is reality diverging? Be specific. Use markdown headers.

STRUCTURE:

**Open**
2 lines on Nifty/Sensex opening level and direction vs {india_session_label} close. Specific number, no fluff.

**Vs Pre-Market**
2-3 lines comparing what's actually happening to what pre-market expected. Where is the bias confirmed? Where is reality diverging? This is the most important section — interpret, don't just describe.

**Sectors & Movers**
2-3 lines on sector behavior so far + 1-2 individual names worth flagging. Use the technical position data — e.g., "Bank Nifty opening below its 20D MA confirms the weakness pre-market flagged."

**Levels in Play**
1-2 lines: the key support/resistance the market is testing right now, and what a break would signal.

**Watch**
1 line on what to monitor in the next 30 minutes.

RULES:
1. Use only provided data. No invented numbers or events.
2. Reference SPECIFIC LEVELS — distance from MAs, support/resistance touches, breadth ratios.
3. NO buy/sell advice. Educational analysis only.
4. Frame as expectation, not certainty.
5. Voice: senior strategist, not TV anchor.
6. NEVER confess data gaps to the reader (no "data unavailable", "not explicitly provided"). Quietly omit or use alternative signals.
7. ANTI-HEDGING: Be specific. Avoid "possibly", "appears to", "suggesting a potential", "may be reflecting". State claims directly when data supports them.
   - WEAK: "Bank Nifty showing some strength, possibly reflecting positive sentiment."
   - STRONG: "Bank Nifty +0.8% leads sectors, confirming the morning rally is institution-led not retail-FOMO."

=== DATA AT 09:30 IST ({date}) ===
Timestamp: {timestamp}

PRE-MARKET BRIEFING (this morning's expectation — compare against it):
{pre_context}

INDEX (live now):
  Sensex: {sensex}
  Nifty 50: {nifty}

TECHNICAL POSITION (where indices are vs MAs and recent range):
{technicals_block}

INDIA VIX:
{vix_line}

MARKET BREADTH (advance-decline from Nifty 100):
{breadth_line}

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

RECENT MARKET NEWS HEADLINES (last 6 hours, from Indian financial press via Pulse):
{news_block}

Material categories worth citing if they explain the open: election results, RBI/SEBI moves, named-stock company news (results, M&A, regulatory), brokerage calls on specific names, macro data (CPI/IIP/GDP/Fed), geopolitical events affecting crude/USD. Sports/lifestyle/IPL/entertainment headlines are noise — ignore.

Rules: Do NOT cite headlines verbatim. Do NOT invent causation. But DO connect material headlines to today's open — if a Citi upgrade explains a stock's strength, say so. If election counting explains a sector rally, say so.

Now write the 10-12 line opening update:"""


INTRADAY_UPDATE_PROMPT = """You are a senior equity strategist writing an INTRADAY UPDATE for MoneyVeda. The session is in progress. Current time: {timestamp}, slot: {slot} IST.

YOUR TASK:
Write a 10-12 line delta update on what has CHANGED since the last slot — and connect to the day's overall arc. This is a continuation, not a recap. Use markdown headers.

STRUCTURE:

**The Move**
2 lines: where is Nifty now vs the {prev_slot} reading? Up/down how much in this 30 minutes? Specific.

**What Changed**
2-3 lines: the most important shift since {prev_slot}. Sector rotation? A name suddenly leading or lagging? Breadth deterioration? Volume spike? Be specific and concrete.

**Day's Arc**
2-3 lines: where does this slot fit in today's story so far? Reference the day-so-far summary if it shows a pattern (steady fade, bounce attempts, range-bound, etc.). If the open expected one thing and we're seeing another, say so.

**Levels & Breadth**
1-2 lines: which level is being tested or held? What does breadth (advance/decline) tell us about conviction?

**Watch**
1 line on what to monitor in the next 30 minutes.

RULES:
1. Treat this as continuation. Reference earlier slots and themes by their data.
2. If the market is essentially flat from {prev_slot}, say so plainly — don't manufacture drama. Use it as a signal of indecision, then pivot to what's developing under the surface (sector rotation, breadth changes, individual stock moves).
3. Use specific numbers and levels. No vague "the market is mixed."
4. Use only provided data. No buy/sell advice. Professional voice.
5. NEVER confess data gaps. If breadth data is unavailable, infer conviction from sector dispersion or top-mover skew instead. Do NOT write "breadth data unavailable" or similar.
6. ANTI-HEDGING: Be specific. Avoid "possibly", "appears to", "suggesting a potential", "may be reflecting". State claims when data supports them.
   - WEAK: "The pullback could possibly indicate profit-taking."
   - STRONG: "Auto giving back 0.4% of the morning's 1.5% gain — profit-taking after the upgrade-driven rally."
7. ANTI-REPETITION: Don't reuse phrases or framings from prior slots. If three slots in a row say "consolidating", you're not reading the data hard enough. Find what's actually developing.

=== DATA AT {slot} IST ({date}) ===
Timestamp: {timestamp}

PRE-MARKET BRIEFING (this morning's setup):
{pre_context}

DAY'S ARC SO FAR (all earlier intraday slots, oldest first):
{day_arc}

PREVIOUS SLOT ({prev_slot} IST) — full text:
{prev_context}
PREVIOUS NIFTY READING: {prev_nifty_summary}

INDEX (live now):
  Sensex: {sensex}
  Nifty 50: {nifty}

TECHNICAL POSITION:
{technicals_block}

INDIA VIX:
{vix_line}

MARKET BREADTH:
{breadth_line}

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

RECENT MARKET NEWS HEADLINES (last 6 hours, from Indian financial press via Pulse):
{news_block}

Material categories that often drive intraday moves: company-specific news (results, regulatory, M&A on named Nifty stocks), election counting trends, RBI/SEBI actions, brokerage calls on specific names, macro data releases. Sports/lifestyle/IPL are noise — ignore.

Rules: Do NOT cite headlines verbatim. Do NOT invent causation. DO connect material headlines to specific moves if the price action and headline align — e.g. if Vodafone Idea is up 4% and there's a Citi bullish-on-VI headline, that's the explanation, say so.

Now write the {slot} IST intraday update:"""


POST_MARKET_PROMPT = """You are a senior equity strategist writing the POST-MARKET WRAP for MoneyVeda. NSE closed at 3:30 PM IST today. Your audience is retail investors who want to understand the day they just lived through.

YOUR TASK:
Write a structured 20-24 line wrap. This is the day's THESIS — pull together the pre-market setup, how the day actually unfolded across the 13 intraday slots, the close, and the implications for tomorrow. Interpret, don't describe. Use markdown headers.

STRUCTURE:

**The Close**
2-3 lines on Nifty/Sensex close — direction, magnitude, where on the day's range we settled. Specific levels.

**The Story**
4-5 lines on how the day actually unfolded. Reference the pre-market expectation: did it play out, or did the day reject the setup? Walk through the arc: open, mid-morning, midday, close. Identify the inflection points using the slot summaries provided.

**Sector & Stock Highlights**
4-5 lines on which sectors led/lagged AND why (use the data — connect a sector move to a sub-theme). Name 2-3 individual stocks with context (not just "X was up Y%" — say what the move means: earnings beat, sector rotation, technical breakout).

**Technical Read**
3-4 lines on where the close leaves Nifty technically: above/below 20D and 50D MAs, position vs 52W high/low, distance from recent support/resistance. India VIX direction too. What does the technical setup imply for tomorrow?

**Filings & Flows**
2-3 lines on the day's NSE filings if any were market-moving; note the breadth (advance/decline) and what it says about institutional conviction.

**Tomorrow**
2 lines on what matters {next_session_label} — a level being tested, a global event, a sector to watch. Frame as expectation.

**Bottom Line**
One sentence — the day in a single insight a retail investor can take home.

RULES:
1. USE ONLY provided data. No invented numbers, news, or events.
2. Reference SPECIFIC LEVELS in the technical section.
3. Connect dots — what THEME explains today's price action? Resist describing without interpreting.
4. NO buy/sell advice on individual stocks. Use Rs. for currency.
5. Professional desk voice.
6. NEVER confess data gaps. If a section's input is missing (e.g., no pre-market on file, breadth unavailable), quietly omit that comparison/sentence. Do NOT write "data unavailable", "while not explicitly provided", or similar. The user should never see plumbing leaking into copy.
7. ANTI-HEDGING: Be specific and direct. Avoid "possibly", "appears to", "suggesting a potential", "ongoing concerns". When the data supports a claim, state it.
   - WEAK: "Auto outperformed, suggesting a potential rotation."
   - STRONG: "Auto's 1.93% rally alongside FMCG weakness (HUL -1.94%, ITC -1.06%) confirms defensive-to-cyclical rotation — likely election-result-driven."
   - WEAK: "The session was characterized by indecisive undertones."
   - STRONG: "A 0.02% close masks a session that tried twice to break 24,400 and failed both times. Auto rotation alone wasn't enough."
8. Calibrate certainty: when interpretation is genuinely uncertain, say so once. Don't hedge every sentence.

=== DATA FOR TODAY ({date}) ===
Timestamp: {timestamp}

PRE-MARKET BRIEFING (today's setup, from this morning):
{pre_context}

DAY'S ARC (every intraday slot from open to close, oldest first):
{day_arc}

INDEX CLOSE:
  Sensex: {sensex}
  Nifty 50: {nifty}

TECHNICAL POSITION (where the close leaves us):
{technicals_block}

INDIA VIX:
{vix_line}

MARKET BREADTH:
{breadth_line}

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

RECENT MARKET NEWS HEADLINES (last 12 hours, from Indian financial press via Pulse):
{news_block}

These headlines should help explain the day's narrative. Material categories: election results (named parties/states), RBI/SEBI moves, named-company news (results, M&A, regulatory), brokerage upgrades/downgrades, macro data (CPI/IIP/GDP/Fed minutes), geopolitical flashpoints. Sports/lifestyle/IPL are noise — ignore.

Rules: Do NOT cite headlines verbatim. DO connect headlines to specific themes when price action and headline align — e.g. if state election results are out and Auto sector outperformed, the rotation explanation is real. If a brokerage upgrade aligns with a stock's outsized move, name it. Don't be so cautious that you miss obvious causation.

Now write the strategist post-market wrap:"""


# ─────────────────────────────────────────────────────────────────────────────
# PROMPT BUILDERS — wire packet data into prompt templates
# ─────────────────────────────────────────────────────────────────────────────
def _build_technicals_block(packet: dict) -> str:
    tech = packet.get("technicals") or {}
    if not tech:
        return "  (technical data unavailable)"
    parts = []
    for label in ("NIFTY 50", "NIFTY BANK", "NIFTY IT"):
        t = tech.get(label) or {}
        parts.append(_format_technicals(label, t))
    return "\n".join(parts)


def _build_vix_line(packet: dict) -> str:
    vix = packet.get("india_vix") or {}
    last = vix.get("last")
    if last is None:
        return "  India VIX: (data unavailable)"
    trend = vix.get("trend_5d_pct")
    note = ""
    if   last < 13: note = " — low volatility regime, complacency risk"
    elif last < 18: note = " — normal volatility regime"
    elif last < 25: note = " — elevated, caution warranted"
    else:           note = " — high stress regime"
    if trend is not None:
        return f"  India VIX: {last} ({trend:+.1f}% over 5D){note}"
    return f"  India VIX: {last}{note}"


def build_pre_market_prompt(packet: dict) -> str:
    yest = packet.get("yesterday_post_text") or "(no recent post-market wrap on file)"
    sess_lbl = _last_session_label()                  # "Friday's" on Mon, "yesterday's" otherwise
    sess_caps = sess_lbl.upper().rstrip("S")          # "FRIDAY'" or "YESTERDAY'" — for heading
    return PRE_MARKET_PROMPT.format(
        date                     = packet["date"],
        timestamp                = packet["timestamp_ist"],
        day_of_week              = _day_of_week_ist(),
        india_session_label      = sess_lbl,
        india_session_label_caps = sess_lbl.upper(),  # "FRIDAY'S" or "YESTERDAY'S"
        us_close_label           = _overnight_label(),
        last_session_wrap_label  = sess_lbl.upper().replace("'S", "'S"),  # heading version
        us_markets               = _format_ticker_list(packet.get("us_markets",   [])),
        us_tech                  = _format_ticker_list(packet.get("us_tech",      [])),
        asia_pacific             = _format_ticker_list(packet.get("asia_pacific", [])),
        currencies               = _format_ticker_list(packet.get("currencies",   [])),
        commodities              = _format_ticker_list(packet.get("commodities",  [])),
        crypto                   = _format_ticker_list(packet.get("crypto",       [])),
        india_prev               = _format_ticker_list(packet.get("india_prev",   [])),
        technicals_block         = _build_technicals_block(packet),
        vix_line                 = _build_vix_line(packet),
        yesterday_wrap           = yest,
        news_block               = _format_pulse_headlines(packet.get("news") or []),
    )


def build_post_market_prompt(packet: dict) -> str:
    prior = packet.get("prior") or {}
    return POST_MARKET_PROMPT.format(
        date                = packet["date"],
        timestamp           = packet["timestamp_ist"],
        next_session_label  = _next_session_label(),
        sensex              = format_ticker_line(packet.get("sensex")),
        nifty               = format_ticker_line(packet.get("nifty")),
        sectors             = _format_ticker_list(packet.get("sectors",     [])),
        top_stocks          = _format_ticker_list(packet.get("top_stocks",  [])),
        currencies          = _format_ticker_list(packet.get("currencies",  [])),
        commodities         = _format_ticker_list(packet.get("commodities", [])),
        us_status           = _format_ticker_list(packet.get("us_status",   [])),
        filings             = summarize_filings(packet.get("filings",       [])),
        technicals_block    = _build_technicals_block(packet),
        vix_line            = _build_vix_line(packet),
        breadth_line        = _format_breadth(packet.get("breadth") or {}),
        pre_context         = (prior.get("pre_text") or "[INSTRUCTION TO MODEL: No pre-market briefing on file. SKIP all 'compare to pre-market' comparisons in your wrap. Do NOT mention that pre-market is missing. Just describe today's session on its own terms.]")[:1200],
        day_arc             = (prior.get("all_slots_compact") or "  [INSTRUCTION: No intraday slots recorded today. Skip the 'arc' walkthrough; describe the day from open to close using the close-of-day data only.]"),
        news_block          = _format_pulse_headlines(packet.get("news") or []),
    )


def build_intraday_prompt(packet: dict) -> str:
    prior = packet.get("prior", {}) or {}
    sess_lbl = _last_session_label()
    if packet.get("is_opening"):
        pre_ctx = prior.get("pre_text") or "[INSTRUCTION TO MODEL: No pre-market briefing exists for today. SKIP all 'vs pre-market' comparisons. Describe the opening on its own merits using the live data below. Do NOT mention that pre-market is missing.]"
        return INTRADAY_OPENING_PROMPT.format(
            date                = packet["date"],
            timestamp           = packet["timestamp_ist"],
            day_of_week         = _day_of_week_ist(),
            india_session_label = sess_lbl,
            pre_context         = pre_ctx,
            sensex              = format_ticker_line(packet.get("sensex")),
            nifty               = format_ticker_line(packet.get("nifty")),
            sectors             = _format_ticker_list(packet.get("sectors",      [])),
            top_stocks          = _format_ticker_list(packet.get("top_stocks",   [])),
            asia_pacific        = _format_ticker_list(packet.get("asia_pacific", [])),
            currencies          = _format_ticker_list(packet.get("currencies",   [])),
            commodities         = _format_ticker_list(packet.get("commodities",  [])),
            technicals_block    = _build_technicals_block(packet),
            vix_line            = _build_vix_line(packet),
            breadth_line        = _format_breadth(packet.get("breadth") or {}),
            news_block          = _format_pulse_headlines(packet.get("news") or []),
        )
    # Update slots
    prev_slot = prior.get("prev_slot") or "the prior slot"
    prev_ctx  = prior.get("prev_text") or "[INSTRUCTION: No prior intraday slot found. Write as a fresh update for this time. Do not mention that prior context is missing.]"
    prev_pct  = prior.get("prev_nifty_pct")
    prev_summary = (f"{prev_pct:+.2f}% vs {sess_lbl} close" if isinstance(prev_pct, (int, float))
                    else "not recorded")
    pre_ctx_short = (prior.get("pre_text") or "[INSTRUCTION TO MODEL: No pre-market briefing on file. SKIP any 'vs pre-market' framing. Do NOT mention that pre-market is missing.]")[:900]
    day_arc = prior.get("all_slots_compact") or "  [INSTRUCTION: This is the first intraday update of the day; no earlier slots to reference.]"
    return INTRADAY_UPDATE_PROMPT.format(
        date               = packet["date"],
        timestamp          = packet["timestamp_ist"],
        slot               = packet["slot"],
        prev_slot          = prev_slot,
        prev_context       = prev_ctx,
        prev_nifty_summary = prev_summary,
        pre_context        = pre_ctx_short,
        day_arc            = day_arc,
        sensex             = format_ticker_line(packet.get("sensex")),
        nifty              = format_ticker_line(packet.get("nifty")),
        sectors            = _format_ticker_list(packet.get("sectors",      [])),
        top_stocks         = _format_ticker_list(packet.get("top_stocks",   [])),
        currencies         = _format_ticker_list(packet.get("currencies",   [])),
        commodities        = _format_ticker_list(packet.get("commodities",  [])),
        asia_pacific       = _format_ticker_list(packet.get("asia_pacific", [])),
        technicals_block   = _build_technicals_block(packet),
        vix_line           = _build_vix_line(packet),
        breadth_line       = _format_breadth(packet.get("breadth") or {}),
        news_block         = _format_pulse_headlines(packet.get("news") or []),
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
