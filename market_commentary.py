"""
market_commentary.py  ─  MoneyVeda Market Commentary (v2.2)
====================================================================
Generates daily AI-powered market commentary for Indian retail investors.

v2.2 CHANGES (Render scheduling fix):
  • detect_mode_and_slot() now returns (None, None) for off-schedule fires
    instead of misclassifying 07:30/08:30/09:00 IST as pre-market.
  • main() exits cleanly (exit 0, no API calls) when off-schedule.
  • This lets the Render cron use a broad schedule like `0,30 2-10 * * 1-5`
    (fires every :00 and :30 from 02:00 to 10:30 UTC = 07:30 to 16:00 IST).
    Real slots fire normally; "extra" fires exit in ~2 seconds.

v2.1 CHANGES (reasoning upgrade):
  • SHARED_PRINCIPLES block injected into every prompt:
      - Internal reasoning framework (8 questions, silent CoT)
      - "What is the market TRYING to do" core framing
      - Banned filler phrases list
      - Interpreting-moves checklist (breadth/volume/peer/persistence confirmation)
      - Market-ignoring-news detection rule
      - Causal-chain examples (crude → OMC, rupee → IT, etc.)
      - Non-obvious insight requirement (>= 1 per commentary)
  • Hybrid model selection:
      - Post-market always uses gemini-2.5-pro (best wrap quality)
      - Event days (>1.5% move, VIX spike, extreme breadth) use Pro for intraday
      - Routine intraday/pre-market stay on flash-lite
  • Sharpened role line ("You are not a news summarizer") in every prompt

THREE MODES (unchanged from v2.0):
  1. PRE-MARKET   (08:00 IST)
  2. INTRADAY     (09:30, 10:00 ... 15:30 IST — 13 slots/day)
  3. POST-MARKET  (16:00 IST)

USAGE:
  python market_commentary.py                     # auto-detect from IST time
  python market_commentary.py --mode pre
  python market_commentary.py --mode intraday --slot 10:30
  python market_commentary.py --mode pre --dry-run

RENDER CRON SCHEDULE (set in Render dashboard, Settings → Deploy → Schedule):
  0,30 2-10 * * 1-5
  → fires every :00 and :30 from 02:00 UTC to 10:30 UTC, Mon-Fri
  → covers all 15 real slots (pre + 13 intraday + post) in IST
  → 3 "extra" fires exit cleanly via detect_mode_and_slot() returning None

EXIT CODES:
  0 = success OR clean exit (off-schedule fire)
  1 = config/env error
  2 = data too thin (skipped)
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

# v2.1: model selection is now per-call. These are the candidate models.
GEMINI_MODEL_FAST   = "gemini-2.5-flash-lite"   # cheap, fast — default intraday
GEMINI_MODEL_STRONG = "gemini-2.5-pro"          # post-market + event days

IST = timezone(timedelta(hours=5, minutes=30))

# Canonical intraday slot times (IST). Must match the cron schedule in YAML.
INTRADAY_SLOTS = [
    "09:30", "10:00", "10:30", "11:00", "11:30", "12:00", "12:30",
    "13:00", "13:30", "14:00", "14:30", "15:00", "15:30",
]
PRE_SLOT  = "08:00"   # nominal slot label for pre-market row
POST_SLOT = "16:00"   # nominal slot label for post-market row

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (MoneyVeda/2.1 MarketCommentary) "
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
    today = datetime.now(IST).date()
    if today.weekday() == 0:        # Monday → last Friday
        return today - timedelta(days=3)
    elif today.weekday() == 6:      # Sunday → last Friday
        return today - timedelta(days=2)
    elif today.weekday() == 5:      # Saturday → last Friday
        return today - timedelta(days=1)
    else:
        return today - timedelta(days=1)


def _last_session_label() -> str:
    today_dow = datetime.now(IST).weekday()
    if today_dow == 0:
        return "Friday's"
    elif today_dow == 5 or today_dow == 6:
        return "Friday's"
    else:
        return "yesterday's"


def _overnight_label() -> str:
    today_dow = datetime.now(IST).weekday()
    if today_dow == 0:
        return "Friday's US close"
    elif today_dow == 5 or today_dow == 6:
        return "Friday's US close"
    else:
        return "overnight US session"


def _next_session_label() -> str:
    today_dow = datetime.now(IST).weekday()
    if today_dow == 4:
        return "Monday"
    elif today_dow == 5:
        return "Monday"
    elif today_dow == 6:
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
    candidate = None
    cur_total = hh * 60 + mm
    for s in INTRADAY_SLOTS:
        sh, sm = map(int, s.split(":"))
        s_total = sh * 60 + sm
        if s_total <= cur_total:
            candidate = s
        else:
            break
    return candidate or INTRADAY_SLOTS[0]


def detect_mode_and_slot():
    """
    Auto-detect mode + slot from current IST time.

    Returns (None, None) if the current time is NOT inside a valid scheduled
    slot window. This lets the caller exit cleanly when Render fires the cron
    at a time that doesn't correspond to a real slot (e.g. 07:30, 08:30, 09:00
    IST when using a broad `0,30 2-10 * * 1-5` Render schedule).

    Valid windows (each ±15 min for cron drift tolerance):
      - Pre-market: 08:00 IST  (07:45 – 08:15)
      - Intraday:   09:30, 10:00, ... 15:30 IST  (each ±15 min)
      - Post-market: 16:00 IST  (15:45 – 16:15)
    """
    now = datetime.now(IST)
    cur_min = now.hour * 60 + now.minute  # minutes since midnight IST

    # Pre-market window: 08:00 IST = 480 min
    if 465 <= cur_min <= 495:
        return "pre", PRE_SLOT

    # Post-market window: 16:00 IST = 960 min
    if 945 <= cur_min <= 975:
        return "post", POST_SLOT

    # Intraday slots: each ±15 min
    for slot in INTRADAY_SLOTS:
        sh, sm = map(int, slot.split(":"))
        slot_min = sh * 60 + sm
        if abs(cur_min - slot_min) <= 15:
            return "intraday", slot

    # Off-schedule fire — caller should exit cleanly
    return None, None


# ─────────────────────────────────────────────────────────────────────────────
# DATA FETCHING
# ─────────────────────────────────────────────────────────────────────────────
def fetch_market_data(mode: str, timeout: int = 12):
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
# FILINGS
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
# PRIOR CONTEXT (intraday continuity)
# ─────────────────────────────────────────────────────────────────────────────
def get_prior_intraday_context(today: str, current_slot: str) -> dict:
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

            slot_lines = []
            for r in reversed(prev_all.data):
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
# TECHNICAL ANALYSIS HELPERS
# ─────────────────────────────────────────────────────────────────────────────
try:
    import yfinance as _yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False


def _compute_index_technicals(yahoo_symbol: str) -> dict:
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
# NEWS HEADLINES (Pulse by Zerodha)
# ─────────────────────────────────────────────────────────────────────────────
import xml.etree.ElementTree as _ET
from html import unescape as _html_unescape

PULSE_FEED_URL = "http://pulse.zerodha.com/feed.php"
PULSE_HEADERS = {
    "User-Agent": (
        "MoneyVeda/2.1 MarketCommentary "
        "(https://moneyveda.org; analysis context use; contact via website)"
    )
}

_PULSE_RELEVANCE_HITS = {
    "nifty", "sensex", "nse", "bse", "stock market", "indian market",
    "stocks", "shares", "equity", "equities", "index", "indices",
    "trading guide", "ahead of market", "market action",
    "rbi", "sebi", "rupee", "fed", "inflation", "gdp", "policy", "rate", "rates",
    "fii", "dii", "monsoon", "budget", "fiscal",
    "bank", "banks", "banking", "it services", "pharma", "auto",
    "metals", "fmcg", "energy", "oil", "crude", "gold",
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
    "results", "earnings", "profit", "loss", "dividend", "bonus",
    "split", "buyback", "ipo", "qip", "merger", "acquisition",
    "stake", "deal", "valuation", "demerger",
    "buy call", "sell call", "target price", "upgrade", "downgrade",
    "brokerage", "rating", "outlook", "guidance",
    "bullish", "bearish", "bullish on", "bearish on",
    "rally", "selloff", "crash", "volatility", "correction",
    "breakout", "support", "resistance", "all-time high", "52-week",
    "iran", "hormuz", "tehran", "opec", "sanctions",
    "russia", "ukraine", "china trade", "tariff",
    "election", "elections", "exit poll", "counting", "results day",
    "bjp", "congress", "modi", "verdict", "majority", "lead", "trailing",
    "state assembly", "lok sabha", "general election", "by-election",
    "cabinet", "parliament",
    "monetary policy", "repo rate", "rbi mpc", "rbi minutes",
    "fed minutes", "fed meeting", "fomc",
    "cpi data", "cpi inflation", "wpi", "iip", "gdp data", "trade deficit",
    "fiscal deficit", "current account",
    "q1 results", "q2 results", "q3 results", "q4 results",
    "results announcement", "earnings result", "guidance",
    "results day", "result preview",
    "gold", "silver", "jewellery", "jewelry", "platinum",
    "consumption", "consumer demand", "consumer spending",
    "appeal", "campaign", "import duty", "export duty", "gst on",
    "festive demand", "wedding season", "rural demand", "urban demand",
    "rupee falls", "rupee weakens", "rupee depreciates", "rupee declines",
    "rupee gains", "rupee strengthens", "rupee appreciates",
    "dollar index", "dxy",
    "block deal", "bulk deal", "insider", "promoter",
    "stake sale", "stake purchase", "open offer",
    "preferential allotment", "rights issue", "warrant",
    "investigation", "probe", "raid", "penalty",
    "ban", "approval", "license", "tax", "duty", "levy",
    "subsidy", "scheme", "psu",
}


def _parse_pubdate(raw: str):
    if not raw:
        return None
    raw = raw.strip()
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def _is_market_relevant(title: str, summary: str) -> bool:
    blob = f"{title} {summary}".lower()
    return any(k in blob for k in _PULSE_RELEVANCE_HITS)


def get_pulse_headlines(max_age_hours: int = 12, limit: int = 12) -> list:
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
            if pub_dt.tzinfo is None:
                pub_dt = pub_dt.replace(tzinfo=timezone.utc)
            if pub_dt < cutoff:
                continue
            if not _is_market_relevant(title, summary):
                continue

            tkey = title.lower()[:80]
            if tkey in seen_titles:
                continue
            seen_titles.add(tkey)

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

    packet["technicals"] = {
        "NIFTY 50":   _compute_index_technicals("^NSEI"),
        "NIFTY BANK": _compute_index_technicals("^NSEBANK"),
        "NIFTY IT":   _compute_index_technicals("^CNXIT"),
    }
    packet["india_vix"] = _compute_index_technicals("^INDIAVIX")
    prior = get_prior_intraday_context(packet["date"], "00:00")
    packet["yesterday_post_text"] = prior.get("yesterday_post_text")
    packet["news"] = get_pulse_headlines(max_age_hours=36, limit=18)

    for key in packet:
        if isinstance(packet[key], list):
            packet[key] = [t for t in packet[key] if t]
    return packet


def build_intraday_packet(slot: str):
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

    if slot < "13:30":
        world = fetch_market_data("world")
        if world:
            packet["asia_pacific"] = [t for t in (find_ticker(world, l) for l in
                                       ["NIKKEI 225", "HANG SENG", "KOSPI"]) if t]

    packet["technicals"] = {
        "NIFTY 50":   _compute_index_technicals("^NSEI"),
        "NIFTY BANK": _compute_index_technicals("^NSEBANK"),
        "NIFTY IT":   _compute_index_technicals("^CNXIT"),
    }
    packet["india_vix"] = _compute_index_technicals("^INDIAVIX")
    packet["breadth"]   = get_market_breadth()
    packet["news"]      = get_pulse_headlines(max_age_hours=6, limit=10)
    packet["prior"]     = get_prior_intraday_context(today, slot)
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

    packet["technicals"] = {
        "NIFTY 50":   _compute_index_technicals("^NSEI"),
        "NIFTY BANK": _compute_index_technicals("^NSEBANK"),
        "NIFTY IT":   _compute_index_technicals("^CNXIT"),
    }
    packet["india_vix"] = _compute_index_technicals("^INDIAVIX")
    packet["breadth"]   = get_market_breadth()
    packet["news"]      = get_pulse_headlines(max_age_hours=12, limit=15)
    packet["prior"]     = get_prior_intraday_context(packet["date"], "23:59")
    packet["filings"]   = get_todays_filings()
    return packet


# ─────────────────────────────────────────────────────────────────────────────
# SHARED REASONING PRINCIPLES  (v2.1 — injected into every prompt)
# ─────────────────────────────────────────────────────────────────────────────
# This block is the core of v2.1. It shifts every prompt from "describe the
# market" to "interpret what the market is trying to do" — with explicit
# silent chain-of-thought, banned phrases, an interpreting-moves checklist,
# the market-ignoring-news rule, causal chains, and a non-obvious insight
# requirement. Injected via {shared_principles} placeholder.
SHARED_PRINCIPLES = """
SILENT REASONING (do this BEFORE writing — do NOT print these answers, do NOT label your output with them):
1. What is the dominant market force in the data right now?
2. What CHANGED since the previous slot/session?
3. Is the move broad-based or narrow / index-heavy?
4. Is institutional conviction visible in breadth + volume + sector dispersion?
5. Which sector leadership matters most today?
6. Is the market confirming or rejecting the pre-market / prior expectation?
7. What significant news is the market IGNORING? (non-reaction = signal)
8. What would invalidate the current trend?

Pick the strongest 2-3 of these and let them shape the commentary. The reasoning is silent; the OUTPUT shows interpretation.

CORE FRAMING — what is the market TRYING TO DO?
Frame your commentary around what the market is trying to do this session:
  - defend a support level
  - sustain a breakout
  - rotate into defensives / out of defensives
  - absorb bad news
  - fade an opening gap
  - maintain risk appetite despite headwinds
  - test a key technical level
Not "what it did" — "what it's attempting, and whether it's succeeding."

BANNED FILLER PHRASES (use ONLY if the specific data point explicitly proves them):
  "profit booking", "cautious sentiment", "mixed cues", "selective buying",
  "volatile trade", "rangebound action", "investors remained cautious",
  "market participants awaited cues", "in a holding pattern",
  "consolidation" (if you mean consolidation, prove it: cite the range, days, volume).
If you cannot replace one of these with a specific observation grounded in numbers, OMIT the sentence entirely.

INTERPRETING MOVES (apply to every sector >0.8% or stock >2%):
  - Did BREADTH confirm? (broad participation or narrow heavyweight push?)
  - Did VOLUME confirm? (>1.5x 30D avg = institutional activity likely)
  - Did the related sector / peers confirm?
  - Did the move PERSIST or fade across the slot?
A move without confirmation is fragile — say so. A move with full confirmation is real — say that too, directly.

MARKET IGNORING NEWS (high-signal — call it out):
If a material headline appears in NEWS but the related sectors/stocks fail to react materially, FLAG IT EXPLICITLY. Non-reaction is itself a signal — either the news is already priced in, or conviction in the implied direction is weak. Example: "Crude up 2% overnight but OMCs flat — the market is treating today's spike as transient."

CAUSAL CHAINS (think second-order, not headline-level):
  - crude up → OMC margin pressure + inflation watch
  - rupee weak → IT positive (exporters), auto/durables negative (importers)
  - bond yields falling → bank NIM concern + rate-sensitive sectors helped
  - VIX spike → defensive rotation into FMCG/pharma
  - election certainty → cyclicals up, defensives lag
  - Fed dovish surprise → IT + financials up, gold up
Do not stop at the headline. State the chain.

EXPECTATION vs REACTION (markets move on surprise, not headlines):
  - Strong news + weak reaction = already priced in
  - Weak news + strong rally = excessive pessimism earlier
  - Good earnings + no upside = expectations were too high
  - Bad news + market holds = absorbed, buyers underneath
Apply this lens when news + price data are both available.

NON-OBVIOUS INSIGHT (REQUIRED — at least ONE per commentary):
Every commentary must contain at least one observation NOT derivable from a single ticker. A divergence, a quiet rotation, an inconsistency, a non-reaction. Examples of the right voice:
  - "Index stability despite weak breadth suggests heavyweight support — not real risk appetite."
  - "IT weakness no longer dragging banks indicates domestic-risk preference is holding."
  - "Broad participation fading while indices hold highs reduces sustainability of the rally."
  - "Auto's rally alongside FMCG weakness confirms defensive-to-cyclical rotation."
Surface-level summaries ("Nifty closed higher led by banks") are not enough.

PRIORITIZATION (focus, don't enumerate):
Pick the 2 most important sector moves, the strongest divergence, the key institutional signal, and the most important technical level. Ignore low-impact noise — five mediocre observations are worse than two sharp ones.
""".strip()


# ─────────────────────────────────────────────────────────────────────────────
# PROMPT TEMPLATES (v2.1 — strengthened role + shared principles injected)
# ─────────────────────────────────────────────────────────────────────────────
PRE_MARKET_PROMPT = """You are a senior equity strategist briefing the trading desk on Indian markets before the 9:15 AM IST open. You are NOT a news summarizer. You are NOT a TV anchor. You interpret price action, sector rotation, breadth, positioning, and conviction for retail investors using MoneyVeda — smart, time-pressed, want analysis not data.

{shared_principles}

YOUR TASK:
Write a structured 18-22 line strategist briefing in plain English. INTERPRETATION, not description. Identify 2-3 dominant themes; place today's setup against recent context (last week's range, last session's wrap); call out divergences worth watching; give a clear directional bias for the open and a clear view of what the market will be TRYING TO DO at open.

IMPORTANT: Today is {day_of_week} {date}. The most recent trading session was {india_session_label}. The most recent US close was {us_close_label}. Use these labels precisely — do NOT say "yesterday" or "overnight" if today is Monday or a post-holiday open. Use "Friday's" or "{india_session_label}" when that's the accurate reference.

STRUCTURE (use markdown headers exactly as shown — frontend renders them):

**Setup**
2-3 lines on the dominant narrative from {us_close_label} and what it means for today's open. Interpret US closes, don't just describe them. Note any major divergence from {india_session_label} domestic tone.

**Global Context**
3-4 lines covering US close (Dow/Nasdaq/S&P with one driver each), Asian markets this morning, USD/INR direction, and crude. Apply the CAUSAL CHAINS framework — connect movements where causally relevant.

**Technical Position**
3-4 lines on Nifty's recent range, where it sits vs 20D/50D MAs, support and resistance zones, India VIX level. Use specific levels: "Nifty closed {india_session_label} at X, with 23,950 having held twice last week as support."

**Themes to Watch**
3-4 lines on 2-3 themes likely to drive today's session — sector rotation continuation, an upcoming event, a divergence between sectors. Reference {india_session_label} wrap if relevant. Include at least one NON-OBVIOUS INSIGHT here.

**Bias**
2 lines: what the market will be TRYING TO DO at open (defend a level, follow through on yesterday's move, fade an overnight cue, etc.) and what would invalidate that view. Frame as expectation, not certainty.

**Takeaway**
One sentence — what should a retail investor watch in the first 30 minutes.

RULES:
1. USE ONLY data provided. Do not invent numbers, levels, news, or events.
2. Reference SPECIFIC LEVELS where the data supports it.
3. Frame predictions as expectation, not certainty ("likely to", "should test", "watch for").
4. NO buy/sell advice on individual stocks. Educational analysis only.
5. Use Rs. for currency.
6. If you don't have enough data for a section, do NOT confess the gap to the reader. Quietly omit, or use the data you DO have. Never write "data unavailable" or "while not explicitly provided".
7. Voice: confident, specific, professional. Desk strategist, not TV anchor.
8. NO INVENTION OF CAUSATION (CRITICAL): If a stock or sector is moving and the NEWS HEADLINES section does NOT contain a specific catalyst, do NOT invent one.
   - Don't say "X on results" unless an earnings/results headline for X today is visible
   - Don't say "X on profit-booking" unless multiple data points support that
   - Don't say "Y sector on ongoing concerns" — name the concern or omit
   - Acceptable when cause is unknown: "Titan -7% on heavy volume — driver not visible in today's news flow", or just state the move.
9. ANTI-HEDGING (only when you HAVE evidence): Avoid filler like "possibly", "appears to", "suggesting a potential" WHEN the data supports a direct claim.
   - EVIDENCE EXISTS — WEAK: "Auto outperformed, suggesting a potential rotation."
   - EVIDENCE EXISTS — STRONG: "Auto's 1.93% rally alongside FMCG weakness (HUL -1.94%, ITC -1.06%) confirms defensive-to-cyclical rotation."
   - EVIDENCE IS MISSING — say so: "Titan -7% — no specific catalyst visible in news; trigger isn't clear."

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

RECENT MARKET NEWS HEADLINES (last 36 hours, Indian financial press via Pulse):
{news_block}

These headlines are CONTEXT. Material categories worth citing: election results, RBI/SEBI moves, named-company news (results, M&A, regulatory), brokerage upgrades/downgrades, macro data (CPI/IIP/GDP/Fed), geopolitical events affecting crude/USD. Noise to ignore: sports, lifestyle, IPL, entertainment.

Rules: Do NOT cite headlines verbatim. Do NOT invent causation. DO connect material headlines to themes when data confirms the connection.

Now write the strategist pre-market briefing:"""


INTRADAY_OPENING_PROMPT = """You are a senior equity strategist writing the FIRST INTRADAY UPDATE of the day for MoneyVeda. You are NOT a news summarizer. NSE opened at 9:15 AM IST. It is now {timestamp}, slot 09:30 IST.

{shared_principles}

IMPORTANT: Today is {day_of_week} {date}. The most recent prior trading session was {india_session_label} (NOT "yesterday" if today is Monday or post-holiday). Use "{india_session_label}" or "Friday's" precisely — never substitute "yesterday" when that's inaccurate.

YOUR TASK:
Write a structured 10-12 line briefing on how the opening 15 minutes played out. The KEY angle: did the market open as the pre-market expected, or is reality diverging? AND what is the market TRYING TO DO in the first 15 minutes — confirm yesterday's trend, fade an overnight gap, defend a level? Use markdown headers.

STRUCTURE:

**Open**
2 lines on Nifty/Sensex opening level and direction vs {india_session_label} close. Specific number, no fluff.

**Vs Pre-Market**
2-3 lines comparing actual vs expected. Where confirmed? Where diverging? Most important section — interpret, don't describe.

**Sectors & Movers**
2-3 lines on sector behavior + 1-2 individual names worth flagging. Apply the INTERPRETING MOVES checklist: is the move confirmed by breadth, volume, peers? Use technicals — e.g. "Bank Nifty opening below 20D MA confirms the weakness pre-market flagged."

**Levels in Play**
1-2 lines: the key support/resistance the market is testing, and what a break would signal. This is where you say what the market is TRYING TO DO.

**Watch**
1 line on what to monitor in the next 30 minutes.

RULES:
1. Use only provided data. No invented numbers or events.
2. Reference SPECIFIC LEVELS — distance from MAs, support/resistance touches, breadth ratios.
3. NO buy/sell advice. Frame as expectation, not certainty.
4. Senior strategist voice, not TV anchor.
5. NEVER confess data gaps to the reader. Quietly omit or use alternative signals.
6. NO INVENTION OF CAUSATION (CRITICAL): If a stock is moving sharply and NEWS doesn't contain a specific catalyst for THAT stock, do NOT invent one. When cause is unclear: "X moved Y% — driver not visible in available news" or just state the move.
7. ANTI-HEDGING (only when you HAVE evidence):
   - EVIDENCE EXISTS — STRONG: "Bank Nifty +0.8% leads sectors after RBI rate-cut headline this morning."
   - EVIDENCE MISSING — HONEST: "Titan -7% on no specific visible catalyst — connection to today's gold-consumption headlines isn't explicit in the data."

=== DATA AT 09:30 IST ({date}) ===
Timestamp: {timestamp}

PRE-MARKET BRIEFING (this morning's expectation — compare against it):
{pre_context}

INDEX (live now):
  Sensex: {sensex}
  Nifty 50: {nifty}

TECHNICAL POSITION:
{technicals_block}

INDIA VIX:
{vix_line}

MARKET BREADTH:
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

RECENT MARKET NEWS HEADLINES (last 6 hours, Indian financial press via Pulse):
{news_block}

Material categories: election results, RBI/SEBI moves, named-stock news (results/M&A/regulatory), brokerage calls, macro data, geopolitics affecting crude/USD. Noise to ignore: sports/lifestyle/IPL.

Rules: Do NOT cite verbatim. Do NOT invent causation. DO connect material headlines to today's open when data confirms.

Now write the 10-12 line opening update:"""


INTRADAY_UPDATE_PROMPT = """You are a senior equity strategist writing an INTRADAY UPDATE for MoneyVeda. You are NOT a news summarizer. The session is in progress. Current time: {timestamp}, slot: {slot} IST.

{shared_principles}

YOUR TASK:
Write a 10-12 line delta update on what has CHANGED since the last slot — and connect to the day's overall arc. This is a continuation, not a recap. What is the market TRYING TO DO right now — extend a move, reverse one, defend a level, rotate? Use markdown headers.

STRUCTURE:

**The Move**
2 lines: where is Nifty now vs {prev_slot} reading? Up/down how much in this 30 minutes? Specific.

**What Changed**
2-3 lines: the most important shift since {prev_slot}. Sector rotation? A name suddenly leading or lagging? Breadth deterioration? Volume spike? Be specific. Apply the INTERPRETING MOVES checklist.

**Day's Arc**
2-3 lines: where does this slot fit in today's story so far? Reference the day-so-far summary. If open expected one thing and we're seeing another, say so. State what the market is TRYING TO DO.

**Levels & Breadth**
1-2 lines: which level is being tested or held? What does breadth tell us about conviction? Include at least one NON-OBVIOUS INSIGHT here if not earlier.

**Watch**
1 line on what to monitor in the next 30 minutes.

RULES:
1. Treat this as continuation. Reference earlier slots and themes by their data.
2. If the market is essentially flat from {prev_slot}, say so plainly — don't manufacture drama. Use it as a signal of indecision, then pivot to what's developing under the surface.
3. Use specific numbers and levels. No vague "the market is mixed."
4. Use only provided data. No buy/sell advice. Professional voice.
5. NEVER confess data gaps. If breadth unavailable, infer conviction from sector dispersion. Do NOT write "breadth data unavailable".
6. NO INVENTION OF CAUSATION (CRITICAL): If a stock is moving sharply and NEWS doesn't contain a specific catalyst for THAT stock, do NOT fabricate one. When cause is unknown: "X moved Y% on no specific visible catalyst" is FAR better than inventing one.
7. NO SELF-REFERENCE: You are writing the commentary, not narrating writing it. Phrases like "this slot represents...", "our analysis suggests" break immersion.
8. ANTI-HEDGING (only when you HAVE evidence):
   - EVIDENCE EXISTS — STRONG: "Auto giving back 0.4% of the morning's 1.5% gain — profit-taking after the upgrade-driven rally."
   - EVIDENCE MISSING — HONEST: "Auto down 0.4% in the last 30 min on no specific news visible — possibly position trimming, trigger isn't clear."
9. ANTI-REPETITION: Don't reuse phrases or framings from prior slots. If three slots in a row say "consolidating", you're not reading the data hard enough.

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

SECTOR PERFORMANCE (live now):
{sectors}

TOP MOVERS (live now):
{top_stocks}

CURRENCIES:
{currencies}

COMMODITIES:
{commodities}

ASIA-PACIFIC (if still trading):
{asia_pacific}

RECENT MARKET NEWS HEADLINES (last 6 hours, Indian financial press via Pulse):
{news_block}

Material categories driving intraday: named-stock news, election counting, RBI/SEBI, brokerage calls, macro data. Noise: sports/lifestyle/IPL.

Rules: Do NOT cite verbatim. Do NOT invent causation. DO connect material headlines to specific moves when price action and headline align.

Now write the {slot} IST intraday update:"""


POST_MARKET_PROMPT = """You are a senior equity strategist writing the POST-MARKET WRAP for MoneyVeda. You are NOT a news summarizer. NSE closed at 3:30 PM IST today. Your audience is retail investors who want to understand the day they just lived through.

{shared_principles}

YOUR TASK:
Write a structured 20-24 line wrap. This is the day's THESIS — pull together pre-market setup, how the day actually unfolded across 13 intraday slots, the close, and implications for tomorrow. The central question: WHAT WAS THE MARKET TRYING TO DO TODAY, and did it succeed? Use markdown headers.

STRUCTURE:

**The Close**
2-3 lines on Nifty/Sensex close — direction, magnitude, where on the day's range we settled. Specific levels.

**The Story**
4-5 lines on how the day unfolded. Reference the pre-market expectation: did it play out, or did the day reject the setup? Walk through the arc: open, mid-morning, midday, close. Identify inflection points using the slot summaries. State what the market was TRYING TO DO and whether it succeeded.

**Sector & Stock Highlights**
4-5 lines on which sectors led/lagged AND why. Apply the INTERPRETING MOVES checklist. Name 2-3 individual stocks with context — what the move means, not just the magnitude. Apply CAUSAL CHAINS where the data supports them.

**Technical Read**
3-4 lines on where the close leaves Nifty technically: above/below 20D and 50D MAs, position vs 52W high/low, distance from recent support/resistance. India VIX direction. What does the technical setup imply for tomorrow?

**Filings & Flows**
2-3 lines on the day's NSE filings if any were market-moving; note breadth (advance/decline) and what it says about institutional conviction. Apply the MARKET IGNORING NEWS rule — was there material news the market ignored?

**Tomorrow**
2 lines on what matters {next_session_label} — a level being tested, a global event, a sector to watch. Frame as expectation. State what the market will likely be TRYING TO DO.

**Bottom Line**
One sentence — the day in a single insight a retail investor can take home. This MUST be a NON-OBVIOUS INSIGHT, not a recap.

RULES:
1. USE ONLY provided data. No invented numbers, news, or events.
2. Reference SPECIFIC LEVELS in the technical section.
3. Connect dots — what THEME explains today's price action?
4. NO buy/sell advice. Use Rs. for currency.
5. Professional desk voice.
6. NEVER confess data gaps. If a section's input is missing, quietly omit. Do NOT write "data unavailable", "while not explicitly provided", or similar.
7. NO INVENTION OF CAUSATION (CRITICAL): If a stock or sector had a big move and NEWS/FILINGS don't contain a specific catalyst, do NOT fabricate one. When cause is unknown but the move is real: "Titan's -6% decline was the day's most notable outlier — no specific catalyst visible in today's news or filings."
8. NO SELF-REFERENCE: Just write the analysis.
9. ANTI-HEDGING (only when you HAVE evidence):
   - EVIDENCE EXISTS — STRONG: "Auto's 1.93% rally alongside FMCG weakness (HUL -1.94%, ITC -1.06%) confirms defensive-to-cyclical rotation — likely election-driven."
   - EVIDENCE MISSING — HONEST: "Titan's -6% decline was the day's most striking move; no specific catalyst surfaced in available news flow."
10. Calibrate certainty: when interpretation is genuinely uncertain, say so once. Don't hedge every sentence.

=== DATA FOR TODAY ({date}) ===
Timestamp: {timestamp}

PRE-MARKET BRIEFING (today's setup):
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

TOP STOCK MOVERS (by % change magnitude):
{top_stocks}

CURRENCIES:
{currencies}

COMMODITIES:
{commodities}

US MARKET STATUS (pre-open in New York):
{us_status}

TODAY'S NSE FILINGS (first 10):
{filings}

RECENT MARKET NEWS HEADLINES (last 12 hours, Indian financial press via Pulse):
{news_block}

Material categories: election results, RBI/SEBI moves, named-company news, brokerage calls, macro data, geopolitical flashpoints. Noise: sports/lifestyle/IPL.

Rules: Do NOT cite verbatim. DO connect headlines to themes when price action confirms. Apply MARKET IGNORING NEWS rule — explicit non-reactions are signal.

Now write the strategist post-market wrap:"""


# ─────────────────────────────────────────────────────────────────────────────
# PROMPT BUILDERS — wire packet data + shared principles into prompt templates
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
    sess_lbl = _last_session_label()
    return PRE_MARKET_PROMPT.format(
        shared_principles        = SHARED_PRINCIPLES,
        date                     = packet["date"],
        timestamp                = packet["timestamp_ist"],
        day_of_week              = _day_of_week_ist(),
        india_session_label      = sess_lbl,
        india_session_label_caps = sess_lbl.upper(),
        us_close_label           = _overnight_label(),
        last_session_wrap_label  = sess_lbl.upper().replace("'S", "'S"),
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
        shared_principles   = SHARED_PRINCIPLES,
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
        pre_context         = (prior.get("pre_text") or "[INSTRUCTION TO MODEL: No pre-market briefing on file. SKIP all 'compare to pre-market' comparisons. Do NOT mention pre-market is missing. Describe today's session on its own terms.]")[:1200],
        day_arc             = (prior.get("all_slots_compact") or "  [INSTRUCTION: No intraday slots recorded today. Skip the 'arc' walkthrough; describe the day from open to close using close-of-day data only.]"),
        news_block          = _format_pulse_headlines(packet.get("news") or []),
    )


def build_intraday_prompt(packet: dict) -> str:
    prior = packet.get("prior", {}) or {}
    sess_lbl = _last_session_label()
    if packet.get("is_opening"):
        pre_ctx = prior.get("pre_text") or "[INSTRUCTION TO MODEL: No pre-market briefing exists for today. SKIP all 'vs pre-market' comparisons. Describe the opening on its own merits. Do NOT mention pre-market is missing.]"
        return INTRADAY_OPENING_PROMPT.format(
            shared_principles   = SHARED_PRINCIPLES,
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
    prev_ctx  = prior.get("prev_text") or "[INSTRUCTION: No prior intraday slot found. Write as a fresh update for this time. Do not mention prior context is missing.]"
    prev_pct  = prior.get("prev_nifty_pct")
    prev_summary = (f"{prev_pct:+.2f}% vs {sess_lbl} close" if isinstance(prev_pct, (int, float))
                    else "not recorded")
    pre_ctx_short = (prior.get("pre_text") or "[INSTRUCTION TO MODEL: No pre-market briefing on file. SKIP 'vs pre-market' framing. Do NOT mention pre-market is missing.]")[:900]
    day_arc = prior.get("all_slots_compact") or "  [INSTRUCTION: This is the first intraday update of the day; no earlier slots to reference.]"
    return INTRADAY_UPDATE_PROMPT.format(
        shared_principles  = SHARED_PRINCIPLES,
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
# MODEL SELECTION (v2.1 — hybrid strategy)
# ─────────────────────────────────────────────────────────────────────────────
# Post-market always uses Pro (best wrap quality, once per day).
# Event days route intraday through Pro too — big moves, VIX spikes, extreme
# breadth all signal a session where the cost premium pays back in quality.
# Routine intraday and pre-market stay on Flash-Lite to control costs.
def _is_event_day(packet: dict) -> bool:
    """Detect whether today warrants stronger model for intraday."""
    # 1. Nifty move >= 1.5% (absolute)
    nifty = packet.get("nifty")
    if not nifty and packet.get("india_prev"):
        # Fallback for pre-market packet
        for t in packet["india_prev"]:
            if t and t.get("label") == "NIFTY 50":
                nifty = t
                break
    if isinstance(nifty, dict) and nifty.get("pct") is not None:
        if abs(nifty.get("pct", 0)) >= 1.5:
            return True

    # 2. India VIX moved >= 15% over 5D
    vix = packet.get("india_vix") or {}
    if vix.get("trend_5d_pct") is not None:
        if abs(vix["trend_5d_pct"]) >= 15:
            return True

    # 3. Breadth extreme (>= 3:1 either way)
    breadth = packet.get("breadth") or {}
    ratio = breadth.get("ad_ratio")
    if ratio is not None and ratio > 0:
        if ratio >= 3.0 or ratio <= 0.33:
            return True

    return False


def _select_model(mode: str, packet: dict) -> tuple:
    """
    Returns (model_name, max_output_tokens).
    Post-market always Pro. Intraday/pre-market upgrade to Pro on event days.
    """
    if mode == "post":
        return (GEMINI_MODEL_STRONG, 8000)
    if mode == "pre":
        # Pre-market on Monday or after major event yesterday — upgrade.
        if _is_event_day(packet):
            return (GEMINI_MODEL_STRONG, 8000)
        return (GEMINI_MODEL_FAST, 900)
    # Intraday
    if _is_event_day(packet):
        return (GEMINI_MODEL_STRONG, 6000)
    return (GEMINI_MODEL_FAST, 500)


# ─────────────────────────────────────────────────────────────────────────────
# GEMINI CALL (v2.1 — accepts model parameter)
# ─────────────────────────────────────────────────────────────────────────────
def call_gemini(prompt: str, model: str = None, max_tokens: int = 900):
    if not GEMINI_AVAILABLE:
        _log("⚠️", "google-generativeai package not installed")
        return None, "error"
    if not GEMINI_API_KEY:
        _log("⚠️", "GEMINI_API_KEY not set")
        return None, "error"
    model = model or GEMINI_MODEL_FAST
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gen_model = genai.GenerativeModel(model)
        _log("🧠", f"Calling Gemini ({model}, max_tokens={max_tokens})...")
        response = gen_model.generate_content(
            prompt,
            generation_config={
                "temperature":       0.5,
                "max_output_tokens": max_tokens,
                "top_p":             0.9,
            },
            request_options={"timeout": 45},   # Pro is slower than flash-lite
        )
        if response and response.text:
            text = response.text.strip()
            if len(text) < 80:
                _log("⚠️", f"Gemini returned too-short text ({len(text)} chars)")
                return None, "error"
            _log("✅", f"Gemini returned {len(text)} characters ({model})")
            # source tag: "gemini_pro" or "gemini_flash" — useful for audit
            source_tag = "gemini_pro" if "pro" in model else "gemini_flash"
            return text, source_tag
        _log("⚠️", "Gemini returned empty response")
        return None, "error"
    except Exception as e:
        _log("⚠️", f"Gemini API error: {e}")
        return None, "error"


# ─────────────────────────────────────────────────────────────────────────────
# RULE-BASED FALLBACKS (unchanged from v2.0)
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
# SUPABASE CACHE WRITE
# ─────────────────────────────────────────────────────────────────────────────
def save_commentary(commentary_type: str, slot: str, text: str, source: str, packet: dict) -> bool:
    if not supabase:
        _log("⚠️", "Supabase not configured — skipping save")
        return False
    try:
        date = _today_ist()
        slot_full = f"{slot}:00"
        supabase.table("market_commentary").upsert(
            {
                "commentary_type": commentary_type,
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
# ORCHESTRATION (v2.1 — uses _select_model)
# ─────────────────────────────────────────────────────────────────────────────
def generate_commentary(mode: str, slot: str = None, dry_run: bool = False):
    _log("🚀", f"Starting {mode.upper()} commentary generation (slot={slot})")
    _log("📅", f"IST now: {_now_ist_str()}")

    if mode == "pre":
        slot   = slot or PRE_SLOT
        packet = build_pre_market_packet()
        prompt = build_pre_market_prompt(packet)
    elif mode == "post":
        slot   = slot or POST_SLOT
        packet = build_post_market_packet()
        prompt = build_post_market_prompt(packet)
    elif mode == "intraday":
        if slot is None:
            now = datetime.now(IST)
            slot = _snap_to_intraday_slot(now.hour, now.minute)
        elif slot not in INTRADAY_SLOTS:
            _log("⚠️", f"Slot {slot} not in canonical list — snapping")
            sh, sm = map(int, slot.split(":"))
            slot = _snap_to_intraday_slot(sh, sm)
        packet = build_intraday_packet(slot)
        prompt = build_intraday_prompt(packet)
    else:
        _log("❌", f"Unknown mode: {mode}")
        return None

    # v2.1: model + token limit chosen by hybrid strategy
    model, max_tokens = _select_model(mode, packet)
    is_event = _is_event_day(packet)
    if is_event and mode != "post":
        _log("⚡", f"EVENT DAY detected — routing {mode} to {model}")

    # Sanity check
    total_datapoints = sum(
        len(v) if isinstance(v, list) else (1 if v and not isinstance(v, dict) else 0)
        for v in packet.values()
    )
    if total_datapoints < 4:
        _log("❌", f"Data packet too thin ({total_datapoints} items). Skipping.")
        return None

    if dry_run:
        print("\n" + "=" * 70)
        print(f"DRY RUN — prompt for {mode} {slot} (model={model}):")
        print("=" * 70)
        print(prompt)
        print("=" * 70)

    text, source = call_gemini(prompt, model=model, max_tokens=max_tokens)

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
        return {"text": text, "source": source, "saved": False, "slot": slot, "model": model}

    saved = save_commentary(mode, slot, text, source, packet)
    return {"text": text, "source": source, "saved": saved, "slot": slot, "model": model}


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="MoneyVeda Market Commentary v2.1")
    parser.add_argument("--mode", choices=["pre", "intraday", "post", "auto"], default="auto",
                        help="'auto' detects from current IST time (default)")
    parser.add_argument("--slot", default=None,
                        help="Intraday slot HH:MM (e.g. 10:30). Optional.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print prompt and output but do not save to Supabase")
    parser.add_argument("--force-pro", action="store_true",
                        help="Override model selection — use Gemini Pro for this run")
    args = parser.parse_args()

    mode = args.mode
    slot = args.slot
    if mode == "auto":
        detected_mode, auto_slot = detect_mode_and_slot()
        if detected_mode is None:
            _log("⏭️", f"Current IST time ({_now_ist_str()}) is outside any "
                       f"scheduled slot window. Exiting cleanly — no commentary generated.")
            sys.exit(0)
        mode = detected_mode
        slot = slot or auto_slot
        _log("🤖", f"Auto-detected: mode={mode}, slot={slot}")

    # Optional manual override of model selection
    if args.force_pro:
        global _select_model
        _orig = _select_model
        def _select_model(m, p):
            base_tokens = _orig(m, p)[1]
            return (GEMINI_MODEL_STRONG, base_tokens)
        _log("⚡", "FORCE-PRO override active — Gemini Pro for this run")

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
