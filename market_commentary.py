"""
market_commentary.py  ─  MoneyVeda Market Commentary (v3.0)
====================================================================
Generates daily AI-powered market commentary for Indian retail investors.

v3.0 CHANGES (grounded close slot + post-market reschedule + Nifty 100 movers):
  • POST-MARKET RESCHEDULED 16:00 IST → 17:00 IST. POST_SLOT, the
    detect_mode_and_slot() post window, the _is_pre_market_time-style
    timing docs, and the documented Render cron all updated. The cron
    schedule must now extend one UTC hour (0,30 2-10 → 0,30 2-11) so the
    11:30 UTC tick (= 17:00 IST) actually fires post-market. 17:00 gives
    today's provisional FII/DII figures more time to publish before the
    wrap is written.
  • 15:30 IST INTRADAY SLOT IS NOW GOOGLE-GROUNDED, exactly like pre and
    post. New GROUNDED_INTRADAY_SLOTS set drives this. The close-of-
    session 15:30 update now routes to Gemini Pro + google_search,
    inherits the GROUNDING DISCIPLINE block, and falls back to a
    rebuilt non-grounded prompt on grounded failure (same pattern as
    pre/post). All other intraday slots are UNCHANGED (Flash-Lite /
    Pro on event days, Pulse only, no grounding).
  • NIFTY 100 TOP-5 GAINERS / TOP-5 LOSERS added to every commentary
    EXCEPT pre-market (intraday slots + post-market). get_nifty100_movers()
    is yfinance-only (batched download of the Nifty 100 universe) — the
    same trusted code path as technicals / sector rotation, NO NSE/broker
    sourcing risk. The prompt requires a NAMED reason per mover (grounded
    search where active, Pulse headlines otherwise) and falls back to the
    existing NO-INVENTION-OF-CAUSATION rule when no catalyst surfaces.
    Pre-market deliberately excluded (movers are a session read, not a
    pre-open input). Graceful degradation as usual: {} on total failure,
    partial on per-symbol failure, model-instruction placeholder on empty.
  • NIFTY_100_SYMBOLS is a maintained static constituent list (Nifty 50 +
    Nifty Next 50). Refresh it when the index reconstitutes; yfinance
    silently skips any symbol that errors so a stale entry never blocks.

v2.9 CHANGES (10-day sector rotation / satellite view — pre & post only):
  • get_sector_rotation(): 10-session relative-strength rotation across an
    11-sector set (Bank, IT, Auto, Pharma, FMCG, Metal, Energy, Realty,
    Infra, PSU Bank, Cons Durables) vs Nifty 50. Per sector: period %,
    relative-to-Nifty %, 1st-half vs 2nd-half split, trend shape
    (accelerating / fading / steady), stance (accumulation / under
    distribution / tracking market). yfinance only — same trusted path
    as technicals; NO NSE/broker sourcing risk.
  • CRITICAL FRAMING: this is a RELATIVE-STRENGTH PROXY, not measured
    rupee flow. Formatter + prompt language explicitly forbid the LLM
    from claiming "Rs. X cr flowed from sector A to B" — it must phrase
    as relative strength / rotation only. Prevents invented-attribution.
  • PRESENTATION: all 11 sectors are computed and ranked by strength vs
    Nifty under the hood, but only TOP 3 inflow / BOTTOM 3 outflow are
    shown (one tight line each + NET READ) — simple satellite scan, not
    an 11-line table. Ranking stays on relative-to-Nifty (not raw %) so
    a broad rally doesn't just surface high-beta sectors.
  • Wired into PRE_MARKET_PROMPT (block + Themes to Watch now anchors a
    theme in the period rotation) and POST_MARKET_PROMPT (block + Sector
    & Stock Highlights now places today against the 10d satellite view:
    extending or reversing the period rotation).
  • Graceful degradation as usual: {} on total failure, partial on
    per-symbol failure, model-instruction placeholder on empty, never
    blocks commentary.
  • INTRADAY untouched (period view is a pre/post satellite read; the
    10d window barely moves intraday).

v2.8 CHANGES (pre-market FII/DII exact-figure grounded search — pre only):
  • PRE_EVENT_ATTRIBUTION_GROUNDED gains an explicit clause (g): if the
    structured FII/DII block is empty, Gemini MUST grounded-search the
    PREVIOUS session's provisional figures (Moneycontrol/NSE/ET/Mint —
    public ~16h by 08:00) and state the EXACT Rs.-crore net for FII and
    DII separately, each tagged with the trading date. Anti-staleness
    guard: if only an older figure is found it must be labelled, never
    presented as latest; no rounding a precise net to "over Rs. 3,000cr".
  • Overnight Catalysts FII/DII clause hardened to demand exact net cash
    figures + date, not a vague "net sellers".
  • POST-market deliberately UNCHANGED: today's provisional figure is
    often not yet published at 16:00, so post stays on the structured
    fetch + descriptor (no grounded exact-figure mandate there).
  • Pre-only, prompt-only change. No new data dependency, no sourcing
    risk. INTRADAY untouched.

v2.7 CHANGES (global macro telemetry — pre & post only):
  • get_global_macro_telemetry(): DXY, US 10Y yield, Brent crude as
    STRUCTURED numeric fields (value + day move; bps change for the
    yield). yfinance only (DX-Y.NYB / ^TNX / BZ=F) — same trusted path
    as technicals; NO NSE/broker sourcing risk. ^TNX yield/10 normalised.
  • _format_global_macro(): regime annotations (strong-dollar, elevated
    risk-free rate, high-crude CPI/OMC pressure) and the standard
    graceful-degradation model-instruction placeholder on empty.
  • Wired into PRE_MARKET_PROMPT (GLOBAL MACRO TELEMETRY block + Overnight
    Catalysts now told to quote DXY/US10Y/Brent and trace each through
    its inter-market chain) and POST_MARKET_PROMPT (block + Technical
    Read now folds macro into the forward setup).
  • Derivatives layer (PCR/Max-Pain/FII-futures/OI build-up) deliberately
    NOT implemented: option-chain data has an unresolved source decision
    (NSE-direct IP-block risk vs broker non-redistribution vs paid
    vendor). Code is feasible; the source is a business decision and
    must be settled before writing a fetcher that may not resolve in
    production. Tracked for a later version.
  • Semantic news filtering and stateful intraday velocity intentionally
    deferred (low marginal return / reopens frozen intraday).
  • INTRADAY remains untouched.

v2.6 CHANGES (new structured data inputs — pre & post only):
  • get_gift_nifty(): GIFT/SGX Nifty gap-direction indicator. In-house
    market API first, yfinance fallback (delayed is fine for 08:00).
    Returns implied_gap classification. Pre-market packet only.
  • get_fii_dii(): provisional FII/DII net cash flow. In-house API first,
    then NSE's own once-daily provisional report (cookie-primed Session,
    authoritative — NOT intraday scraping). Pre packet (prev session) +
    post packet (today's). Includes FII-vs-DII pattern descriptor.
  • get_market_breadth() now also feeds the PRE-MARKET packet/prompt
    (previously intraday + post only) for prev-session participation.
  • All three fetchers degrade gracefully exactly like get_market_breadth:
    {} on total failure, model-instruction placeholders in the formatter,
    commentary is NEVER blocked.
  • Wired into PRE_MARKET_PROMPT (GIFT/FII-DII/breadth blocks +
    Overnight Catalysts now explicitly told to lead with GIFT and cite
    FII/DII) and POST_MARKET_PROMPT (FII/DII block + Filings & Flows now
    told to state provisional FII/DII figures).
  • INTRADAY remains untouched (still breadth-only, no GIFT/FII-DII).

v2.5 CHANGES (pre-market event attribution + timing hardening):
  • PRE_MARKET_PROMPT gains a MANDATORY **Overnight Catalysts** section
    directly after **Setup** — names the concrete overnight/pre-open
    events as a [event] -> [mechanism] -> [expected effect on open]
    list, killing generic "global cues look mixed" framing.
  • Pre-market news-guidance block replaced with a grounding-conditional
    directive:
      - PRE_EVENT_ATTRIBUTION_GROUNDED   (search ACTIVE → search mandated)
      - PRE_EVENT_ATTRIBUTION_UNGROUNDED (search OFF → Pulse is primary)
  • Pre-market line budget raised 18-22 → 20-24 for the new section.
  • TIMING FIX: pre-market detection window tightened from 08:00 ±15
    (07:45–08:15) to 08:00 ±8 (07:52–08:08). The Render cron's earliest
    tick (02:00 UTC = 07:30 IST) can no longer drift into the window
    even under scheduler jitter.
  • New hard guard in main(): an explicit `--mode pre` invoked outside
    the 08:00 IST window exits cleanly (protects against a misconfigured
    cron calling `--mode pre` at 07:30). --dry-run and new --force bypass.
  • INTRADAY is untouched in this version.

v2.4 CHANGES (event attribution made structural — post-market):
  • POST_MARKET_PROMPT gains a MANDATORY **Catalysts** section directly
    after **The Close** — names the concrete events/prints/developments
    that drove the session as a [catalyst] -> [mechanism] -> [effect]
    list, instead of letting attribution dissolve into prose.
  • News-guidance block replaced with a grounding-conditional directive:
      - EVENT_ATTRIBUTION_GROUNDED   (search ACTIVE → search mandated)
      - EVENT_ATTRIBUTION_UNGROUNDED (search OFF → Pulse is primary)
    Burden of proof flipped: every material move must be matched to a
    NAMED catalyst or explicitly flagged as unexplained. "Price action
    with no named cause" is now a failure, not an acceptable default.
  • Post-market line budget raised 20-24 → 24-28 so the new section
    doesn't starve The Story / Sector & Stock Highlights.
  • generate_commentary(): when a grounded call fails and we fall back to
    a non-grounded call, the prompt is now REBUILT with use_grounding=False
    so we never tell a non-grounded model "Google Search is ACTIVE".

v2.3 CHANGES (Google Search grounding for pre/post-market):
  • call_gemini_grounded() added — uses Gemini's built-in google_search tool
    to fetch live web context. Used ONLY for pre-market and post-market slots,
    where depth matters more than latency/cost.
  • Intraday remains on Pulse RSS + Flash-Lite (unchanged) — preserves the
    sub-second response budget and per-slot cost discipline.
  • Pulse headlines are still passed to pre/post prompts as a curated baseline;
    grounding adds depth on top, not replacement.
  • SHARED_PRINCIPLES extended with a GROUNDING DISCIPLINE block (only injected
    on grounded calls) — keeps the strategist voice, prevents drift into
    "news summary" mode.
  • grounding_sources persisted into data_snapshot for audit / debugging.
  • Tool name auto-negotiates between 'google_search' (Gemini 2.0+) and
    'google_search_retrieval' (legacy) depending on SDK version.

v2.2 CHANGES (Render scheduling fix) — unchanged:
  • detect_mode_and_slot() returns (None, None) for off-schedule fires.
  • main() exits cleanly when off-schedule.

THREE MODES:
  1. PRE-MARKET   (08:00 IST)  — Gemini Pro + Google Search grounding
  2. INTRADAY     (09:30–15:30, 13 slots) — Flash-Lite / Pro (event days),
                   Pulse only. EXCEPTION: the 15:30 IST close slot is
                   Gemini Pro + Google Search grounding (v3.0).
  3. POST-MARKET  (17:00 IST)  — Gemini Pro + Google Search grounding

USAGE:
  python market_commentary.py                     # auto-detect from IST time
  python market_commentary.py --mode pre
  python market_commentary.py --mode intraday --slot 10:30
  python market_commentary.py --mode pre --dry-run
  python market_commentary.py --mode pre --force  # bypass 08:00 IST guard
  python market_commentary.py --no-grounding      # disable grounding for this run

RENDER CRON SCHEDULE (Settings → Deploy → Schedule):
  0,30 2-11 * * 1-5

  Render cron runs in UTC. This schedule fires at :00 and :30 of UTC
  hours 02–11. Auto-detection maps them to IST as:
    02:00 UTC = 07:30 IST  → clean exit (intentional no-op)
    02:30 UTC = 08:00 IST  → PRE-MARKET   ← the only pre-market tick
    03:00 UTC = 08:30 IST  → clean exit
    03:30 UTC = 09:00 IST  → clean exit
    04:00 UTC = 09:30 IST  → INTRADAY (first slot)
    …                       → INTRADAY
    10:00 UTC = 15:30 IST  → INTRADAY (last slot, GROUNDED — v3.0)
    10:30 UTC = 16:00 IST  → clean exit (post moved to 17:00)
    11:00 UTC = 16:30 IST  → clean exit
    11:30 UTC = 17:00 IST  → POST-MARKET  ← the only post-market tick
  Pre-market therefore runs ONLY at 08:00 IST (02:30 UTC). The 07:30 IST
  tick is a deliberate no-op; the tightened ±8 window stops scheduler
  jitter from leaking it into pre-market. Do NOT add a separate
  `--mode pre` cron — auto-detection already handles the timing, and a
  fixed `--mode pre` cron is exactly what produced the early-07:30 firing.
  v3.0: the cron now extends to UTC hour 11 so the 11:30 UTC tick
  (= 17:00 IST) reaches post-market; the old 10:30 UTC (= 16:00 IST)
  tick is now a clean exit since post-market moved to 17:00. The 15:30
  IST intraday tick is unchanged in timing but now runs grounded.

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

GEMINI_MODEL_FAST   = "gemini-2.5-flash-lite"   # cheap, fast — default intraday
GEMINI_MODEL_STRONG = "gemini-2.5-pro"          # post-market + event days + grounded

IST = timezone(timedelta(hours=5, minutes=30))

INTRADAY_SLOTS = [
    "09:30", "10:00", "10:30", "11:00", "11:30", "12:00", "12:30",
    "13:00", "13:30", "14:00", "14:30", "15:00", "15:30",
]
PRE_SLOT  = "08:00"
POST_SLOT = "17:00"          # v3.0: was 16:00 — moved to 17:00 IST

# v3.0: intraday slots that run Google-grounded (Gemini Pro + google_search)
# exactly like pre/post. The close-of-session 15:30 read benefits most from
# live event attribution, so it is grounded; all other intraday slots stay
# on the cheap non-grounded path.
GROUNDED_INTRADAY_SLOTS = {"15:30"}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (MoneyVeda/3.0 MarketCommentary) "
        "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
    )
}

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
    Returns (None, None) for off-schedule fires (caller exits cleanly).

    Render cron runs in UTC. The documented schedule '0,30 2-11 * * 1-5'
    produces ticks at :00 and :30 of UTC hours 02-11, i.e. IST:
      02:00 UTC = 07:30 IST  -> off-schedule, clean exit (intentional no-op)
      02:30 UTC = 08:00 IST  -> PRE-MARKET
      03:00 UTC = 08:30 IST  -> off-schedule, clean exit
      03:30 UTC = 09:00 IST  -> off-schedule, clean exit
      04:00 UTC = 09:30 IST  -> INTRADAY (first slot)
      ...      ...           -> INTRADAY
      10:00 UTC = 15:30 IST  -> INTRADAY (last slot, grounded — v3.0)
      10:30 UTC = 16:00 IST  -> off-schedule, clean exit (post moved)
      11:00 UTC = 16:30 IST  -> off-schedule, clean exit
      11:30 UTC = 17:00 IST  -> POST-MARKET

    Valid windows:
      - Pre-market: 08:00 IST  (07:52 – 08:08, ±8 — tight, so a delayed
                                07:30-IST tick can NEVER drift into it)
      - Intraday:   09:30, 10:00, ... 15:30 IST (each ±15 min)
      - Post-market: 17:00 IST (16:45 – 17:15)   ← v3.0: was 16:00 IST
    """
    now = datetime.now(IST)
    cur_min = now.hour * 60 + now.minute

    if 472 <= cur_min <= 488:        # Pre-market 08:00 ± 8 (480 = 08:00)
        return "pre", PRE_SLOT

    if 1005 <= cur_min <= 1035:      # Post-market 17:00 ± 15 (1020 = 17:00)
        return "post", POST_SLOT

    for slot in INTRADAY_SLOTS:
        sh, sm = map(int, slot.split(":"))
        slot_min = sh * 60 + sm
        if abs(cur_min - slot_min) <= 15:
            return "intraday", slot

    return None, None


def _is_pre_market_time() -> bool:
    """True only if current IST is inside the 08:00 pre-market window
    (480 ± 8 min). Used to guard explicit `--mode pre` runs so a
    misconfigured cron firing at 07:30 IST cannot produce a pre-market
    briefing. Single source of truth shared with detect_mode_and_slot()."""
    now = datetime.now(IST)
    cur_min = now.hour * 60 + now.minute
    return 472 <= cur_min <= 488


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
        r = requests.get(cache_url, headers=HEADERS, timeout=30)
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


# ─────────────────────────────────────────────────────────────────────────────
# GIFT NIFTY (formerly SGX Nifty) — primary gap-direction indicator for
# pre-market. Best-effort: tries the in-house market API first (label may be
# "GIFT NIFTY" or legacy "SGX NIFTY"), then yfinance as fallback. Never blocks
# commentary — returns {} on total failure exactly like get_market_breadth().
# ─────────────────────────────────────────────────────────────────────────────
def get_gift_nifty() -> dict:
    """
    Returns {} on failure, else:
      {"value": float, "pct": float, "source": str,
       "implied_gap": "gap-up|gap-down|flat", "ref_close": float|None}
    pct is GIFT Nifty's move vs its own prior reference (proxy for the
    implied gap vs yesterday's Nifty close).
    """
    out = {}

    # 1) In-house market API (already authorized for our display) ----------
    for mode in ("world", "india"):
        try:
            data = fetch_market_data(mode)
            if not data:
                continue
            t = (find_ticker(data, "GIFT NIFTY")
                 or find_ticker(data, "SGX NIFTY")
                 or find_ticker(data, "GIFT NIFTY 50"))
            if t and t.get("value") is not None:
                pct = t.get("pct", 0) or 0
                out = {
                    "value":  t.get("value"),
                    "pct":    round(pct, 2),
                    "source": "market_api",
                    "ref_close": None,
                }
                break
        except Exception as e:
            _log("⚠️", f"GIFT Nifty via {mode} API failed: {e}")

    # 2) yfinance fallback (delayed, fine for an 08:00 briefing) -----------
    if not out and YFINANCE_AVAILABLE:
        # Common Yahoo symbols seen for GIFT Nifty futures; try in order.
        for sym in ("GIFTNIFTY.NS", "^NSEI"):  # ^NSEI = last Nifty close as ref only
            try:
                tk = _yf.Ticker(sym)
                h = tk.history(period="5d", interval="1d")
                if h is None or h.empty or len(h) < 2:
                    continue
                last = float(h["Close"].iloc[-1])
                prev = float(h["Close"].iloc[-2])
                pct  = ((last - prev) / prev) * 100 if prev else 0
                out = {
                    "value":  round(last, 2),
                    "pct":    round(pct, 2),
                    "source": ("gift_yf" if sym.startswith("GIFT")
                               else "nifty_close_proxy"),
                    "ref_close": round(prev, 2),
                }
                break
            except Exception as e:
                _log("⚠️", f"GIFT Nifty yfinance {sym} failed: {e}")

    if out:
        p = out.get("pct", 0)
        if   p >=  0.25: out["implied_gap"] = "gap-up"
        elif p <= -0.25: out["implied_gap"] = "gap-down"
        else:            out["implied_gap"] = "flat / muted"
        _log("📶", f"GIFT Nifty: {out.get('value')} ({p:+.2f}%) "
                   f"[{out.get('implied_gap')}, src={out.get('source')}]")
    else:
        _log("⚠️", "GIFT Nifty unavailable from all sources")
    return out


# ─────────────────────────────────────────────────────────────────────────────
# FII / DII net cash-market activity (provisional). Source priority:
#   1) in-house market API (if it exposes an fii_dii payload)
#   2) NSE's own published provisional report (authoritative, once-daily,
#      low-rate — NOT intraday quote scraping)
# Provisional figures in Rs. crore; net = buy - sell. Never blocks; {} on fail.
# ─────────────────────────────────────────────────────────────────────────────
NSE_FII_DII_URL = "https://www.nseindia.com/api/fiidiiTradeReact"
NSE_BROWSER_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/120.0.0.0 Safari/537.36"),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/reports/fii-dii",
}


def get_fii_dii() -> dict:
    """
    Returns {} on failure, else:
      {"fii_net": float, "dii_net": float, "date": str|None,
       "fii_buy": float|None, "fii_sell": float|None,
       "dii_buy": float|None, "dii_sell": float|None,
       "source": str, "net_combined": float, "descriptor": str}
    Figures in Rs. crore (provisional cash-market).
    """
    out = {}

    # 1) In-house market API, if it surfaces fii_dii ----------------------
    try:
        url = f"{MARKET_API_BASE}?mode=fii_dii"
        r = requests.get(url, headers=HEADERS, timeout=12)
        if r.ok:
            j = r.json()
            blob = j.get("fii_dii") or j.get("data") or j
            if isinstance(blob, dict) and (
                blob.get("fii_net") is not None or blob.get("fiiNet") is not None
            ):
                fii = blob.get("fii_net", blob.get("fiiNet"))
                dii = blob.get("dii_net", blob.get("diiNet"))
                out = {
                    "fii_net": float(fii), "dii_net": float(dii),
                    "fii_buy": blob.get("fii_buy"), "fii_sell": blob.get("fii_sell"),
                    "dii_buy": blob.get("dii_buy"), "dii_sell": blob.get("dii_sell"),
                    "date": blob.get("date"), "source": "market_api",
                }
    except Exception as e:
        _log("⚠️", f"FII/DII via market API failed: {e}")

    # 2) NSE provisional report (once-daily, authoritative) ---------------
    if not out:
        try:
            with requests.Session() as s:
                s.headers.update(NSE_BROWSER_HEADERS)
                # Prime cookies — NSE rejects direct API hits without a prior
                # homepage visit. Single extra GET, once per run, not per-tick.
                s.get("https://www.nseindia.com", timeout=12)
                resp = s.get(NSE_FII_DII_URL, timeout=15)
                resp.raise_for_status()
                rows = resp.json()
                fii_row = dii_row = None
                for row in rows if isinstance(rows, list) else []:
                    cat = (row.get("category") or "").upper()
                    if "FII" in cat or "FPI" in cat:
                        fii_row = row
                    elif "DII" in cat:
                        dii_row = row
                if fii_row and dii_row:
                    def _f(v):
                        try:    return float(str(v).replace(",", ""))
                        except Exception: return None
                    out = {
                        "fii_net": _f(fii_row.get("netValue")),
                        "dii_net": _f(dii_row.get("netValue")),
                        "fii_buy": _f(fii_row.get("buyValue")),
                        "fii_sell": _f(fii_row.get("sellValue")),
                        "dii_buy": _f(dii_row.get("buyValue")),
                        "dii_sell": _f(dii_row.get("sellValue")),
                        "date": fii_row.get("date") or dii_row.get("date"),
                        "source": "nse_report",
                    }
        except Exception as e:
            _log("⚠️", f"FII/DII via NSE report failed: {e}")

    if out and out.get("fii_net") is not None and out.get("dii_net") is not None:
        fn, dn = out["fii_net"], out["dii_net"]
        out["net_combined"] = round(fn + dn, 2)
        if   fn < 0 and dn > 0: desc = "FII selling absorbed by DII buying (domestic support)"
        elif fn > 0 and dn < 0: desc = "FII buying while DII books profit"
        elif fn > 0 and dn > 0: desc = "both FII and DII net buyers (broad institutional support)"
        elif fn < 0 and dn < 0: desc = "both FII and DII net sellers (institutional risk-off)"
        else:                   desc = "mixed/neutral institutional flow"
        out["descriptor"] = desc
        _log("🏦", f"FII/DII: FII {fn:+,.0f} | DII {dn:+,.0f} Rs.cr "
                   f"[{out.get('source')}] — {desc}")
        return out

    _log("⚠️", "FII/DII unavailable from all sources")
    return {}


def _format_gift_nifty(g: dict) -> str:
    if not g or g.get("value") is None:
        return ("  GIFT Nifty: [INSTRUCTION TO MODEL: GIFT/SGX Nifty not "
                "available this run. Infer likely open direction from US close "
                "+ Asia + USD/INR instead. Do NOT state GIFT Nifty is "
                "unavailable to the reader.]")
    p = g.get("pct", 0)
    src = g.get("source", "")
    src_note = ""
    if src == "nifty_close_proxy":
        src_note = " (proxy: last Nifty close move — true GIFT feed unavailable)"
    return (f"  GIFT Nifty: {g.get('value'):,.2f} ({p:+.2f}%) — "
            f"implied open: {g.get('implied_gap', 'n/a')}{src_note}")


def _format_fii_dii(f: dict) -> str:
    if not f or f.get("fii_net") is None:
        return ("  FII/DII (provisional): [INSTRUCTION TO MODEL: Provisional "
                "FII/DII figures not available this run. If grounded search is "
                "active, search for today's/yesterday's provisional FII-DII "
                "cash figures; otherwise omit institutional-flow attribution "
                "rather than guessing. Do NOT tell the reader the data is "
                "missing.]")
    d = f.get("date")
    dstr = f" [{d}]" if d else ""
    return (f"  FII/DII net (provisional, Rs. cr){dstr}: "
            f"FII {f['fii_net']:+,.0f} | DII {f['dii_net']:+,.0f} | "
            f"combined {f.get('net_combined', 0):+,.0f} — {f.get('descriptor','')}")


# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL MACRO TELEMETRY — DXY, US 10Y yield, Brent crude as STRUCTURED
# numeric fields (not text). These are mathematical inter-market inputs that
# drive algorithmic EM capital shifts; the prompt ties them to Indian sector
# rotation via the CAUSAL CHAINS framework. yfinance only — same trusted code
# path as _compute_index_technicals/GIFT fallback. No NSE/broker sourcing
# risk. Never blocks: {} on total failure, per-symbol best-effort.
# ─────────────────────────────────────────────────────────────────────────────
_MACRO_SYMBOLS = {
    # key            (yahoo symbol, label,                     unit)
    "dxy":      ("DX-Y.NYB", "US Dollar Index (DXY)",          "idx"),
    "us10y":    ("^TNX",     "US 10-Year Treasury Yield",      "yield"),
    "brent":    ("BZ=F",     "Brent Crude (front-month)",      "usd"),
}


def get_global_macro_telemetry() -> dict:
    """
    Returns {} on total failure, else a dict keyed by dxy/us10y/brent, each:
      {"value": float, "day_change_pct": float, "label": str, "unit": str,
       "bps_change": float|None}   # bps_change only meaningful for us10y
    ^TNX is quoted as yield*10 on Yahoo (e.g. 42.2 == 4.22%); we normalise.
    """
    if not YFINANCE_AVAILABLE:
        _log("⚠️", "yfinance unavailable — skipping global macro telemetry")
        return {}

    out = {}
    for key, (sym, label, unit) in _MACRO_SYMBOLS.items():
        try:
            tk = _yf.Ticker(sym)
            h = tk.history(period="6d", interval="1d")
            if h is None or h.empty or len(h) < 2:
                continue
            last = float(h["Close"].iloc[-1])
            prev = float(h["Close"].iloc[-2])

            # Yahoo quotes ^TNX as yield * 10 (42.20 -> 4.220%)
            if key == "us10y":
                last /= 10.0
                prev /= 10.0

            day_chg_pct = ((last - prev) / prev) * 100 if prev else 0.0
            rec = {
                "value":          round(last, 3 if key == "us10y" else 2),
                "day_change_pct": round(day_chg_pct, 2),
                "label":          label,
                "unit":           unit,
                "bps_change":     (round((last - prev) * 100, 1)
                                   if key == "us10y" else None),
            }
            out[key] = rec
        except Exception as e:
            _log("⚠️", f"Macro telemetry {sym} failed: {e}")

    if out:
        bits = []
        if "dxy" in out:
            bits.append(f"DXY {out['dxy']['value']} "
                        f"({out['dxy']['day_change_pct']:+.2f}%)")
        if "us10y" in out:
            bits.append(f"US10Y {out['us10y']['value']}% "
                        f"({out['us10y']['bps_change']:+.0f}bps)")
        if "brent" in out:
            bits.append(f"Brent {out['brent']['value']} "
                        f"({out['brent']['day_change_pct']:+.2f}%)")
        _log("🌐", "Global macro: " + " | ".join(bits))
    else:
        _log("⚠️", "Global macro telemetry unavailable from all symbols")
    return out


def _format_global_macro(g: dict) -> str:
    if not g:
        return ("  Global macro: [INSTRUCTION TO MODEL: DXY / US10Y / Brent "
                "structured telemetry not available this run. If grounded "
                "search is active, fetch latest DXY level, US 10Y yield, and "
                "Brent and apply the same inter-market causal chains; "
                "otherwise lean on the qualitative global cues. Do NOT tell "
                "the reader this data is missing.]")
    lines = []
    if "dxy" in g:
        d = g["dxy"]
        regime = ""
        v = d["value"]
        if   v >= 105:   regime = " — strong-dollar regime, acute EM/INR pressure"
        elif v >= 103.5: regime = " — firm dollar, INR & FII-flow headwind"
        elif v < 100:    regime = " — soft dollar, EM-supportive"
        lines.append(f"  DXY: {v} ({d['day_change_pct']:+.2f}% day){regime}")
    if "us10y" in g:
        y = g["us10y"]
        regime = ""
        v = y["value"]
        if   v >= 4.5:  regime = " — elevated risk-free rate, high-beta/growth headwind"
        elif v <= 3.5:  regime = " — low yields, growth-supportive"
        lines.append(f"  US 10Y yield: {v}% ({y['bps_change']:+.0f}bps day){regime}")
    if "brent" in g:
        b = g["brent"]
        regime = ""
        v = b["value"]
        if   v >= 90:  regime = " — high crude: CPI/fiscal/OMC-margin pressure"
        elif v <= 65:  regime = " — soft crude: importer & margin tailwind"
        lines.append(f"  Brent crude: {v} ({b['day_change_pct']:+.2f}% day){regime}")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# 10-DAY SECTOR ROTATION — "satellite view" of where capital is rotating over
# a period. yfinance only (same trusted path as _compute_index_technicals).
# NO NSE/broker sourcing risk. Never blocks: {} on failure, partial on
# per-symbol failure.
#
# IMPORTANT — this is a ROTATION / RELATIVE-STRENGTH PROXY, not measured
# rupee flow. 10-day index performance shows which sectors are being bid up
# vs sold down and how that compares to the Nifty; it does NOT measure
# actual money moved. The formatter and prompt language label it as such so
# the LLM never claims "Rs. X cr flowed from Auto to Pharma".
# ─────────────────────────────────────────────────────────────────────────────
_ROTATION_LOOKBACK_DAYS = 10

# Broader 11-sector set (rotation shows best across cyclical/defensive/
# rate-sensitive spread). To trim to the intraday 7, delete the last 4 rows.
_ROTATION_SECTORS = {
    "Nifty Bank":       "^NSEBANK",
    "Nifty IT":         "^CNXIT",
    "Nifty Auto":       "^CNXAUTO",
    "Nifty Pharma":     "^CNXPHARMA",
    "Nifty FMCG":       "^CNXFMCG",
    "Nifty Metal":      "^CNXMETAL",
    "Nifty Energy":     "^CNXENERGY",
    "Nifty Realty":     "^CNXREALTY",
    "Nifty Infra":      "^CNXINFRA",
    "Nifty PSU Bank":   "^CNXPSUBANK",
    "Nifty Cons Durables": "^CNXCONSUMER",
}
_ROTATION_BENCHMARK = ("Nifty 50", "^NSEI")


def _pct_change_window(closes, lookback: int):
    """Return (pct_full, pct_first_half, pct_second_half) over the last
    `lookback` sessions, or None if insufficient history."""
    if closes is None or len(closes) < lookback + 1:
        return None
    window = [float(x) for x in closes.tail(lookback + 1).tolist()]
    start, end = window[0], window[-1]
    if not start:
        return None
    pct_full = (end - start) / start * 100.0
    mid_idx = len(window) // 2
    s1, e1 = window[0], window[mid_idx]
    s2, e2 = window[mid_idx], window[-1]
    pct_h1 = ((e1 - s1) / s1 * 100.0) if s1 else 0.0
    pct_h2 = ((e2 - s2) / s2 * 100.0) if s2 else 0.0
    return round(pct_full, 2), round(pct_h1, 2), round(pct_h2, 2)


def get_sector_rotation(lookback: int = _ROTATION_LOOKBACK_DAYS) -> dict:
    """
    Returns {} on total failure, else:
      {"lookback": int, "benchmark_pct": float|None,
       "sectors": [ {name, pct, rel_to_nifty, half1_pct, half2_pct,
                     trend_shape, stance}, ... sorted by rel_to_nifty desc ]}
    stance ∈ accumulation / under distribution / neutral (relative).
    trend_shape ∈ accelerating / fading / steady (2nd half vs 1st half).
    """
    if not YFINANCE_AVAILABLE:
        _log("⚠️", "yfinance unavailable — skipping sector rotation")
        return {}

    # period buffer: need lookback+1 sessions; fetch ~3x calendar to be safe
    period = f"{max(30, (lookback + 1) * 3)}d"

    bench_pct = None
    try:
        bh = _yf.Ticker(_ROTATION_BENCHMARK[1]).history(period=period, interval="1d")
        if bh is not None and not bh.empty:
            r = _pct_change_window(bh["Close"], lookback)
            if r:
                bench_pct = r[0]
    except Exception as e:
        _log("⚠️", f"Rotation benchmark fetch failed: {e}")

    rows = []
    for name, sym in _ROTATION_SECTORS.items():
        try:
            h = _yf.Ticker(sym).history(period=period, interval="1d")
            if h is None or h.empty:
                continue
            r = _pct_change_window(h["Close"], lookback)
            if not r:
                continue
            pct_full, pct_h1, pct_h2 = r
            rel = round(pct_full - bench_pct, 2) if bench_pct is not None else None

            # trend shape: is the move accelerating or fading across the window?
            if   pct_h2 > pct_h1 + 0.75: shape = "accelerating"
            elif pct_h2 < pct_h1 - 0.75: shape = "fading"
            else:                        shape = "steady"

            # stance is RELATIVE to Nifty (true rotation, not market beta)
            if rel is None:
                stance = ("accumulation" if pct_full > 1.0
                          else "under distribution" if pct_full < -1.0
                          else "neutral")
            elif rel >= 1.0:   stance = "accumulation (outperforming Nifty)"
            elif rel <= -1.0:  stance = "under distribution (lagging Nifty)"
            else:              stance = "tracking the market (no clear rotation)"

            rows.append({
                "name": name, "pct": pct_full, "rel_to_nifty": rel,
                "half1_pct": pct_h1, "half2_pct": pct_h2,
                "trend_shape": shape, "stance": stance,
            })
        except Exception as e:
            _log("⚠️", f"Rotation fetch {sym} failed: {e}")

    if not rows:
        _log("⚠️", "Sector rotation unavailable from all symbols")
        return {}

    rows.sort(key=lambda x: (x["rel_to_nifty"] if x["rel_to_nifty"] is not None
                             else x["pct"]), reverse=True)
    _log("🛰️", f"Sector rotation ({lookback}d): "
               f"into [{rows[0]['name']}] / out of [{rows[-1]['name']}], "
               f"Nifty {bench_pct if bench_pct is not None else 'n/a'}%")
    return {"lookback": lookback, "benchmark_pct": bench_pct, "sectors": rows}


def _format_sector_rotation(r: dict) -> str:
    if not r or not r.get("sectors"):
        return ("  Sector rotation (10D): [INSTRUCTION TO MODEL: 10-day "
                "sector rotation data not available this run. If grounded "
                "search is active you may infer period rotation from recent "
                "sector commentary; otherwise omit the period/satellite view "
                "rather than guessing. Do NOT tell the reader it is missing.]")
    lb = r.get("lookback", 10)
    bench = r.get("benchmark_pct")
    secs = r["sectors"]            # already sorted by rel_to_nifty desc
    head = (f"  {lb}-session sector rotation "
            f"(RELATIVE-STRENGTH PROXY, not measured rupee flow; "
            f"Nifty 50 {bench:+.2f}% over the period; "
            f"ranked by strength vs Nifty across all 11 sectors, "
            f"top/bottom 3 shown):"
            if bench is not None else
            f"  {lb}-session sector rotation (relative-strength proxy, "
            f"top/bottom 3 of 11):")
    lines = [head]

    def _line(s, tag):
        rel = (f"{s['rel_to_nifty']:+.2f}% vs Nifty"
               if s['rel_to_nifty'] is not None
               else f"{s['pct']:+.2f}% abs")
        return (f"    {tag} {s['name']}: {rel} "
                f"({s['pct']:+.2f}% abs) [{s['trend_shape']}]")

    top3 = secs[:3]
    bot3 = list(reversed(secs[-3:])) if len(secs) >= 3 else []
    # Guard: if few sectors resolved (degraded fetch), top-3 and bottom-3 can
    # overlap and read as a sector being both 'in' and 'out'. Split disjointly.
    if len(secs) < 6:
        half = max(1, len(secs) // 2)
        top3 = secs[:half]
        bot3 = list(reversed(secs[-half:]))
        # drop any sector that still appears in both (odd-count middle)
        top_names = {s["name"] for s in top3}
        bot3 = [s for s in bot3 if s["name"] not in top_names]
    lines.append("  INFLOW (capital rotating in — strongest vs Nifty):")
    for s in top3:
        lines.append(_line(s, "▲"))
    lines.append("  OUTFLOW (capital rotating out — weakest vs Nifty):")
    for s in bot3:
        lines.append(_line(s, "▼"))

    top = secs[0]; bot = secs[-1]
    lines.append(
        f"    NET READ: over {lb} sessions capital favouring {top['name']} "
        f"({top['rel_to_nifty']:+.2f}% vs Nifty, {top['trend_shape']}); "
        f"rotating out of {bot['name']} "
        f"({bot['rel_to_nifty']:+.2f}% vs Nifty, {bot['trend_shape']}).")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# NIFTY 100 TOP-5 GAINERS / TOP-5 LOSERS (v3.0) — included in every commentary
# EXCEPT pre-market (intraday + post). yfinance only, ONE batched download for
# the whole universe — same trusted code path as technicals / sector rotation,
# NO NSE/broker sourcing risk. The day % is (latest close vs prior close);
# during market hours Yahoo's "latest" row tracks the (delayed) live price, so
# this reads as the day move, consistent with how _compute_index_technicals
# already uses yfinance intraday. Never blocks: {} on total failure, partial
# on per-symbol failure.
#
# NIFTY_100_SYMBOLS is a MAINTAINED static list (Nifty 50 + Nifty Next 50).
# Refresh on index reconstitution. yfinance silently skips a bad symbol so a
# stale entry degrades to "one fewer name", never an exception.
# ─────────────────────────────────────────────────────────────────────────────
NIFTY_100_SYMBOLS = {
    # ---- Nifty 50 ----
    "Reliance": "RELIANCE.NS", "TCS": "TCS.NS", "HDFC Bank": "HDFCBANK.NS",
    "ICICI Bank": "ICICIBANK.NS", "Infosys": "INFY.NS", "HUL": "HINDUNILVR.NS",
    "Bharti Airtel": "BHARTIARTL.NS", "ITC": "ITC.NS", "SBI": "SBIN.NS",
    "L&T": "LT.NS", "Kotak Bank": "KOTAKBANK.NS", "Axis Bank": "AXISBANK.NS",
    "Bajaj Finance": "BAJFINANCE.NS", "Asian Paints": "ASIANPAINT.NS",
    "Maruti Suzuki": "MARUTI.NS", "HCL Tech": "HCLTECH.NS",
    "Sun Pharma": "SUNPHARMA.NS", "Titan": "TITAN.NS",
    "UltraTech Cement": "ULTRACEMCO.NS", "NTPC": "NTPC.NS",
    "Power Grid": "POWERGRID.NS", "Tata Motors": "TATAMOTORS.NS",
    "Nestle India": "NESTLEIND.NS", "Bajaj Finserv": "BAJAJFINSV.NS",
    "Wipro": "WIPRO.NS", "Tata Steel": "TATASTEEL.NS",
    "JSW Steel": "JSWSTEEL.NS", "ONGC": "ONGC.NS",
    "Adani Enterprises": "ADANIENT.NS", "Adani Ports": "ADANIPORTS.NS",
    "Coal India": "COALINDIA.NS", "Hindalco": "HINDALCO.NS",
    "Tech Mahindra": "TECHM.NS", "Grasim": "GRASIM.NS",
    "Dr Reddy's": "DRREDDY.NS", "Cipla": "CIPLA.NS",
    "Eicher Motors": "EICHERMOT.NS", "Britannia": "BRITANNIA.NS",
    "Apollo Hospitals": "APOLLOHOSP.NS", "Tata Consumer": "TATACONSUM.NS",
    "Bajaj Auto": "BAJAJ-AUTO.NS", "Hero MotoCorp": "HEROMOTOCO.NS",
    "Divi's Labs": "DIVISLAB.NS", "SBI Life": "SBILIFE.NS",
    "HDFC Life": "HDFCLIFE.NS", "IndusInd Bank": "INDUSINDBK.NS",
    "Shriram Finance": "SHRIRAMFIN.NS", "BPCL": "BPCL.NS",
    "Trent": "TRENT.NS", "Jio Financial": "JIOFIN.NS",
    # ---- Nifty Next 50 ----
    "LTIMindtree": "LTIM.NS", "Adani Green": "ADANIGREEN.NS",
    "Adani Energy Sol": "ADANIENSOL.NS", "Adani Power": "ADANIPOWER.NS",
    "Ambuja Cements": "AMBUJACEM.NS", "ACC": "ACC.NS",
    "Bank of Baroda": "BANKBARODA.NS", "PNB": "PNB.NS",
    "Canara Bank": "CANBK.NS", "Union Bank": "UNIONBANK.NS",
    "DLF": "DLF.NS", "Godrej Consumer": "GODREJCP.NS", "Dabur": "DABUR.NS",
    "Marico": "MARICO.NS", "Colgate": "COLPAL.NS",
    "Pidilite": "PIDILITIND.NS", "Berger Paints": "BERGEPAINT.NS",
    "Havells": "HAVELLS.NS", "Siemens": "SIEMENS.NS", "ABB": "ABB.NS",
    "Bharat Electronics": "BEL.NS", "HAL": "HAL.NS",
    "Indian Oil": "IOC.NS", "GAIL": "GAIL.NS", "Vedanta": "VEDL.NS",
    "Jindal Steel": "JINDALSTEL.NS", "Tata Power": "TATAPOWER.NS",
    "Power Finance": "PFC.NS", "REC": "RECLTD.NS", "IRFC": "IRFC.NS",
    "LIC": "LICI.NS", "Eternal": "ETERNAL.NS", "Info Edge": "NAUKRI.NS",
    "DMart": "DMART.NS", "Varun Beverages": "VBL.NS",
    "United Spirits": "UNITDSPR.NS", "Mankind Pharma": "MANKIND.NS",
    "Zydus Life": "ZYDUSLIFE.NS", "Torrent Pharma": "TORNTPHARM.NS",
    "Lupin": "LUPIN.NS", "Aurobindo Pharma": "AUROPHARMA.NS",
    "Max Healthcare": "MAXHEALTH.NS", "Bosch": "BOSCHLTD.NS",
    "TVS Motor": "TVSMOTOR.NS", "Hyundai India": "HYUNDAI.NS",
    "InterGlobe (IndiGo)": "INDIGO.NS", "ICICI Pru Life": "ICICIPRULI.NS",
    "ICICI Lombard": "ICICIGI.NS", "Cholamandalam": "CHOLAFIN.NS",
    "Bajaj Holdings": "BAJAJHLDNG.NS",
}

_NIFTY100_TOP_N = 5


def get_nifty100_movers(top_n: int = _NIFTY100_TOP_N) -> dict:
    """
    Returns {} on total failure, else:
      {"asof": str|None,
       "gainers": [{"name", "symbol", "pct", "last"}, ... top_n],
       "losers":  [{"name", "symbol", "pct", "last"}, ... top_n]}
    Day % = (latest close - prior close) / prior close * 100.
    """
    if not YFINANCE_AVAILABLE:
        _log("⚠️", "yfinance unavailable — skipping Nifty 100 movers")
        return {}

    symbols = list(NIFTY_100_SYMBOLS.values())
    by_symbol = {v: k for k, v in NIFTY_100_SYMBOLS.items()}

    try:
        df = _yf.download(
            symbols, period="2d", interval="1d",
            group_by="ticker", progress=False, threads=True,
            auto_adjust=False,
        )
    except Exception as e:
        _log("⚠️", f"Nifty 100 batch download failed: {e}")
        return {}

    if df is None or len(df) == 0:
        _log("⚠️", "Nifty 100 download returned no data")
        return {}

    rows = []
    asof = None
    for sym in symbols:
        try:
            # group_by='ticker' → df[sym]['Close'] is a MultiIndex slice.
            # Missing/failed symbols raise KeyError here and are skipped.
            try:
                closes = df[sym]["Close"].dropna()
            except Exception:
                continue
            if closes is None or len(closes) < 2:
                continue
            last = float(closes.iloc[-1])
            prev = float(closes.iloc[-2])
            if not prev:
                continue
            pct = (last - prev) / prev * 100.0
            rows.append({
                "name":   by_symbol.get(sym, sym),
                "symbol": sym,
                "pct":    round(pct, 2),
                "last":   round(last, 2),
            })
            try:
                asof = closes.index[-1].strftime("%Y-%m-%d")
            except Exception:
                pass
        except Exception:
            continue

    if len(rows) < (top_n * 2):
        # Not necessarily fatal, but flag thin coverage.
        _log("⚠️", f"Nifty 100 movers thin coverage ({len(rows)} symbols resolved)")
    if not rows:
        _log("⚠️", "Nifty 100 movers unavailable from all symbols")
        return {}

    rows.sort(key=lambda r: r["pct"], reverse=True)
    gainers = rows[:top_n]
    losers  = list(reversed(rows[-top_n:]))  # most-negative first
    out = {"asof": asof, "gainers": gainers, "losers": losers}
    g0, l0 = gainers[0], losers[0]
    _log("📈", f"Nifty 100 movers: top {g0['name']} ({g0['pct']:+.2f}%) | "
               f"bottom {l0['name']} ({l0['pct']:+.2f}%) "
               f"[{len(rows)} symbols]")
    return out


def _format_nifty100_movers(m: dict) -> str:
    if not m or not m.get("gainers"):
        return ("  Nifty 100 movers: [INSTRUCTION TO MODEL: Top-5 Nifty 100 "
                "gainers/losers not available this run. Use the TOP MOVERS / "
                "SECTOR data already provided instead and do NOT tell the "
                "reader this list is missing.]")
    asof = m.get("asof")
    head = (f"  Nifty 100 — Top {len(m['gainers'])} gainers / "
            f"Top {len(m['losers'])} losers"
            + (f" (as of {asof})" if asof else "") + ":")
    lines = [head, "  GAINERS:"]
    for s in m["gainers"]:
        lines.append(f"    ▲ {s['name']}: {s['pct']:+.2f}% (last {s['last']:,.2f})")
    lines.append("  LOSERS:")
    for s in m["losers"]:
        lines.append(f"    ▼ {s['name']}: {s['pct']:+.2f}% (last {s['last']:,.2f})")
    return "\n".join(lines)


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
# NEWS HEADLINES (Pulse by Zerodha) — used for intraday + as Pulse baseline
# in pre/post (grounding adds depth on top)
# ─────────────────────────────────────────────────────────────────────────────
import xml.etree.ElementTree as _ET
from html import unescape as _html_unescape

PULSE_FEED_URL = "http://pulse.zerodha.com/feed.php"
PULSE_HEADERS = {
    "User-Agent": (
        "MoneyVeda/3.0 MarketCommentary "
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
    packet["gift_nifty"] = get_gift_nifty()          # gap-direction indicator
    packet["fii_dii"]    = get_fii_dii()             # prev session institutional flow
    packet["breadth"]    = get_market_breadth()      # prev session A/D context
    packet["global_macro"] = get_global_macro_telemetry()  # DXY/US10Y/Brent
    packet["sector_rotation"] = get_sector_rotation()      # 10d satellite view
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
    packet["nifty100_movers"] = get_nifty100_movers()   # v3.0 (not in pre)
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
    packet["fii_dii"]   = get_fii_dii()              # today's provisional cash flow
    packet["global_macro"] = get_global_macro_telemetry()  # DXY/US10Y/Brent
    packet["sector_rotation"] = get_sector_rotation()      # 10d satellite view
    packet["nifty100_movers"] = get_nifty100_movers()      # v3.0 (not in pre)
    packet["news"]      = get_pulse_headlines(max_age_hours=12, limit=15)
    packet["prior"]     = get_prior_intraday_context(packet["date"], "23:59")
    packet["filings"]   = get_todays_filings()
    return packet


# ─────────────────────────────────────────────────────────────────────────────
# SHARED REASONING PRINCIPLES
# ─────────────────────────────────────────────────────────────────────────────
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


# NEW in v2.3: extra block injected only on grounded calls (pre/post-market)
GROUNDING_DISCIPLINE = """
GROUNDING DISCIPLINE (Google Search is available to you — use it like a strategist, not a news aggregator):

WHEN TO SEARCH:
  - To verify a specific catalyst for a large stock move (>3%) when the news headlines in the data packet don't already explain it
  - To get precise wording of a central bank statement, election counting trend, brokerage call target, or macro data print
  - To confirm a global event (Fed speak, OPEC decision, geopolitical flashpoint) before connecting it to Indian sectors
  - To check whether a sector move has a fresh, specific driver (regulatory change, sector-wide downgrade, commodity print)

WHEN NOT TO SEARCH:
  - To pad commentary with "experts say" or "analysts believe" framing
  - To restate what the Pulse headlines already cover
  - To find generic background on a stock or sector
  - To paraphrase a Bloomberg/Reuters article — that's news-summary mode, not strategist mode

HARD RULES FOR USING GROUNDED INFORMATION:
  1. Cite ONLY sources dated within the last 48 hours for pre-market, last 24 hours for post-market.
  2. If two reputable sources disagree on a fact, state the uncertainty plainly. Do not pick one silently.
  3. Avoid retail-blog / SEO-farm sources. Stick to: Bloomberg, Reuters, ET, Mint, BS, MoneyControl, NDTV Profit, official RBI/SEBI/PIB/exchange statements, central bank wires.
  4. Do NOT quote articles verbatim. Synthesize the fact into the strategist voice.
  5. The data packet is still the SOURCE OF TRUTH for prices, levels, sectors, and breadth. Search is for CAUSATION and CONTEXT only — never to override the price data.
  6. If you searched and found nothing useful, say nothing about it. Do not write "I checked recent news and..."
  7. Keep your strategist voice — you are not summarizing what the press says, you are using it as one input among several.

CROSS-CHECK:
  - When the data packet's Pulse headlines and your search results agree: state the cause confidently.
  - When they disagree: trust the more recent / more authoritative source, and note the divergence briefly if material.
  - When data shows a move but no source explains it: say so honestly ("no specific catalyst surfaced in available news flow") — do NOT invent.
""".strip()


# NEW in v2.4: grounding-conditional event-attribution directive for the
# post-market news block. Flips the burden of proof — every material move
# must be matched to a NAMED catalyst or explicitly flagged as unexplained.
EVENT_ATTRIBUTION_GROUNDED = """
These Pulse headlines are a CONTEXT BASELINE, not the full event picture. Grounded Google Search is ACTIVE for this run and you are REQUIRED to use it for event identification BEFORE writing the Catalysts section. Search specifically for: (a) any India macro print released today (CPI / IIP / GDP / trade / PMI / fiscal) — get the actual figure and whether it beat or missed expectations; (b) RBI / SEBI / government policy actions or statements today; (c) the specific driver of EVERY stock that moved >3% and EVERY sector that moved >0.8%; (d) global wires that transmitted into Indian sectors today (Fed/ECB/BoJ speak, OPEC, sanctions, conflict, tariffs, crude/gold prints); (e) the day's provisional FII/DII flow figure if reported. HARD RULE: every material move in the price data must be matched to a NAMED catalyst, or explicitly flagged as having no identifiable catalyst AFTER searching. "Price action analysis with no named cause" is a failure of this task, not an acceptable outcome. Do NOT cite or paraphrase articles — synthesize the event into the strategist voice. Do NOT invent causation: if search genuinely yields nothing for a move, say so plainly. Apply the MARKET IGNORING NEWS rule — a material headline that produced no price reaction is itself a catalyst-level signal and must be named in Catalysts.
""".strip()

EVENT_ATTRIBUTION_UNGROUNDED = """
These Pulse headlines are your PRIMARY event source this run (grounded search is disabled). Mine them hard: every material move in the price data should be matched to a specific headline where one plausibly explains it, or explicitly flagged as unexplained by available news. Do NOT cite verbatim — synthesize into the strategist voice. Do NOT invent causation: if no headline explains a move, write "no specific catalyst surfaced in available news flow" rather than guessing. Apply the MARKET IGNORING NEWS rule — a material headline with no price reaction is itself a signal and must be named in Catalysts.
""".strip()


# NEW in v2.5: pre-market analog of the above. Pre-market is FORWARD-looking,
# so the burden of proof is on naming the concrete OVERNIGHT/MORNING events
# that set up today's open — not generic "global cues mixed" framing.
PRE_EVENT_ATTRIBUTION_GROUNDED = """
These Pulse headlines are a CONTEXT BASELINE, not the full overnight event picture. Grounded Google Search is ACTIVE for this run and you are REQUIRED to use it for event identification BEFORE writing the Overnight Catalysts section. Search specifically for: (a) overnight central-bank developments that set today's tone (Fed/FOMC speak or minutes, ECB, BoJ, RBI commentary) — get the specific message, not "dovish/hawkish" alone; (b) the actual driver of each major US index and US-tech move from the most recent close; (c) any macro print due or released in the last 24h relevant to India (US CPI/jobs, India CPI/IIP/trade, China data); (d) overnight moves in crude / gold / USD-INR / DXY and the specific trigger (OPEC, inventories, geopolitics, yields); (e) large brokerage calls or stock-specific news flagged for the Indian open this morning; (f) geopolitical flashpoints affecting risk appetite; (g) the PREVIOUS SESSION'S provisional FII/DII net cash figures — if the structured FII/DII data block above shows real numbers, use those verbatim; if it shows a model-instruction placeholder, you MUST search (Moneycontrol, NSE, ET, Mint all publish the previous day's provisional cash figures and they have been public ~16 hours by now) and state the EXACT net figures in Rs. crore (e.g. "FIIs net sold Rs. 3,245 cr, DIIs net bought Rs. 4,110 cr in the cash market"), each tagged with the trading date you are quoting. If the only figure you can find is older than the previous trading session, label it as such and do NOT present it as the latest; never round a precise published net to a vague "over Rs. 3,000 cr" when the exact number is available. HARD RULE: every cue you cite as setting up the open must be tied to a NAMED event/print, or explicitly flagged as "no specific trigger — drift only". "Global cues look mixed/positive/negative" with no named driver is a failure of this task, not an acceptable opening. Do NOT cite or paraphrase articles — synthesize into the strategist voice. Do NOT invent causation or numbers: if search yields nothing for a move or figure, say so plainly. Restrict grounded sources to the last 48 hours for pre-market.
""".strip()

PRE_EVENT_ATTRIBUTION_UNGROUNDED = """
These Pulse headlines are your PRIMARY overnight event source this run (grounded search is disabled). Mine them hard: every cue you cite as shaping today's open must be tied to a specific headline (overnight Fed/ECB/BoJ commentary, US close drivers, crude/USD triggers, brokerage calls), or explicitly flagged as drift with no named trigger. Do NOT cite verbatim — synthesize into the strategist voice. Do NOT invent causation: if no headline explains a move, write "no specific overnight trigger — positioning/drift only" rather than guessing. "Global cues look mixed" with no named driver is not acceptable.
""".strip()


# ─────────────────────────────────────────────────────────────────────────────
# PROMPT TEMPLATES
# ─────────────────────────────────────────────────────────────────────────────
PRE_MARKET_PROMPT = """You are a senior equity strategist briefing the trading desk on Indian markets before the 9:15 AM IST open. You are NOT a news summarizer. You are NOT a TV anchor. You interpret price action, sector rotation, breadth, positioning, and conviction for retail investors using MoneyVeda — smart, time-pressed, want analysis not data.

{shared_principles}

{grounding_block}

YOUR TASK:
Write a structured 20-24 line strategist briefing in plain English. INTERPRETATION, not description. Identify 2-3 dominant themes; place today's setup against recent context (last week's range, last session's wrap); call out divergences worth watching; give a clear directional bias for the open and a clear view of what the market will be TRYING TO DO at open.

IMPORTANT: Today is {day_of_week} {date}. The most recent trading session was {india_session_label}. The most recent US close was {us_close_label}. Use these labels precisely — do NOT say "yesterday" or "overnight" if today is Monday or a post-holiday open. Use "Friday's" or "{india_session_label}" when that's the accurate reference.

STRUCTURE (use markdown headers exactly as shown — frontend renders them):

**Setup**
2-3 lines on the dominant narrative from {us_close_label} and what it means for today's open. Interpret US closes, don't just describe them. Note any major divergence from {india_session_label} domestic tone.

**Overnight Catalysts**
This section is MANDATORY and is the spine of the briefing — it answers "WHY is today's open being set up the way it is", not "what futures/cues did". List the 2-4 concrete overnight or pre-open events that actually shape today's session, each on its own line, in the form: [named event/print] -> [transmission mechanism] -> [expected effect on the Indian open]. Draw from: GIFT NIFTY (lead with the implied gap direction and tie it to a cause — it is the single highest-signal input for the open), {india_session_label} FII/DII provisional flow (state the EXACT net cash figures in Rs. crore for FII and DII separately, with the trading date, then read what the FII-vs-DII pattern implies for today's positioning — never a vague "institutions were net sellers" when the precise number is available), Fed/FOMC/ECB/BoJ/RBI commentary (name the specific message), the actual driver of the US close and US-tech moves, macro prints in the last 24h (US CPI/jobs, India CPI/IIP/trade, China data — name the figure), the structured GLOBAL MACRO TELEMETRY (DXY level + day move, US 10Y yield + bps change, Brent + day move — quote the numbers and trace each through its inter-market chain: rising DXY/yields -> FII EM outflow + INR pressure; Brent -> CPI/OMC margins), overnight crude/gold/USD-INR moves and their trigger, large brokerage calls flagged for the open, and geopolitical flashpoints. Apply the CAUSAL CHAINS framework to every entry. If one dominant overnight catalyst is driving the setup, say so explicitly and trace it into the affected Indian sectors. A cue with no identifiable trigger even after grounded search must be stated honestly here ("no specific overnight trigger — positioning/drift only") — but this is a last resort AFTER searching, never the default. Do NOT relegate event attribution to a passing clause inside Global Context; it lives here, named and explicit.

**Global Context**
3-4 lines covering US close (Dow/Nasdaq/S&P with one driver each), Asian markets this morning, USD/INR direction, and crude. Apply the CAUSAL CHAINS framework — connect movements where causally relevant.

**Technical Position**
3-4 lines on Nifty's recent range, where it sits vs 20D/50D MAs, support and resistance zones, India VIX level. Use specific levels: "Nifty closed {india_session_label} at X, with 23,950 having held twice last week as support."

**Themes to Watch**
3-4 lines on 2-3 themes likely to drive today's session — sector rotation continuation, an upcoming event, a divergence between sectors. Anchor at least one theme in the 10-DAY SECTOR ROTATION block: state which sectors capital has been favouring vs exiting over the period and whether that rotation is accelerating or fading, framed explicitly as a relative-strength read (NOT "Rs. X flowed"), then say whether today's setup is likely to extend or break that period trend. Reference {india_session_label} wrap if relevant. Include at least one NON-OBVIOUS INSIGHT here.

**Bias**
2 lines: what the market will be TRYING TO DO at open (defend a level, follow through on yesterday's move, fade an overnight cue, etc.) and what would invalidate that view. Frame as expectation, not certainty.

**Takeaway**
One sentence — what should a retail investor watch in the first 30 minutes.

RULES:
1. USE the data provided + Google Search for verifying causation and context. Never invent numbers, levels, news, or events.
2. Reference SPECIFIC LEVELS where the data supports it.
3. Frame predictions as expectation, not certainty ("likely to", "should test", "watch for").
4. NO buy/sell advice on individual stocks. Educational analysis only.
5. Use Rs. for currency.
6. If you don't have enough data for a section, do NOT confess the gap to the reader. Quietly omit, or use the data you DO have. Never write "data unavailable" or "while not explicitly provided".
7. Voice: confident, specific, professional. Desk strategist, not TV anchor.
8. NO INVENTION OF CAUSATION (CRITICAL): If a stock or sector is moving and neither the NEWS HEADLINES section nor your grounded search yields a specific catalyst, do NOT invent one.
   - Don't say "X on results" unless an earnings/results headline for X today is visible OR confirmed via search
   - Don't say "X on profit-booking" unless multiple data points support that
   - Don't say "Y sector on ongoing concerns" — name the concern or omit
   - Acceptable when cause is unknown: "Titan -7% on heavy volume — driver not visible in today's news flow", or just state the move.
9. ANTI-HEDGING (only when you HAVE evidence): Avoid filler like "possibly", "appears to", "suggesting a potential" WHEN the data supports a direct claim.

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

GLOBAL MACRO TELEMETRY (structural inter-market inputs — tie these to Indian sectors via CAUSAL CHAINS):
{global_macro_line}

INDIA — {india_session_label_caps} CLOSE:
{india_prev}

10-DAY SECTOR ROTATION — PERIOD/SATELLITE VIEW (relative-strength proxy, NOT measured rupee flow):
{sector_rotation_line}

GIFT NIFTY (primary gap-direction indicator for today's open):
{gift_line}

FII / DII — {india_session_label_caps} PROVISIONAL CASH FLOW (institutional positioning into today):
{fii_dii_line}

MARKET BREADTH ({india_session_label} session — underlying participation):
{breadth_line}

INDIA TECHNICAL POSITION:
{technicals_block}

INDIA VIX (volatility regime):
{vix_line}

{last_session_wrap_label} POST-MARKET WRAP (for continuity):
{yesterday_wrap}

RECENT MARKET NEWS HEADLINES (last 36 hours, Indian financial press via Pulse — curated baseline):
{news_block}

{event_directive}

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
2-3 lines on sector behavior + 1-2 individual names worth flagging, drawing the names from the NIFTY 100 TOP-5 GAINERS / TOP-5 LOSERS block where they sharpen the picture. Apply the INTERPRETING MOVES checklist: is the move confirmed by breadth, volume, peers? Give any flagged mover a NAMED reason from the Pulse headlines, or state the move with "no specific catalyst visible" per the NO-INVENTION rule. Use technicals — e.g. "Bank Nifty opening below 20D MA confirms the weakness pre-market flagged."

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

NIFTY 100 — TOP 5 GAINERS / TOP 5 LOSERS (give each highlighted name a NAMED reason from Pulse, else honest "no catalyst"):
{nifty100_movers_block}

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

{grounding_block}

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

**Nifty 100 Movers**
2-3 lines on the day's standout names from the NIFTY 100 TOP-5 GAINERS / TOP-5 LOSERS block. Do NOT just list ten tickers — pick the 2-3 that actually matter (largest move, a name confirming/contradicting the sector story, an outlier vs its peers) and give each a NAMED reason: if grounding is active, search for the specific catalyst; otherwise use the Pulse headlines; if neither yields a cause, state the move with "no specific catalyst visible" per the NO-INVENTION rule. Tie at least one mover back to the sector rotation or breadth picture.

**Watch**
1 line on what to monitor in the next 30 minutes.

RULES:
1. Treat this as continuation. Reference earlier slots and themes by their data.
2. If the market is essentially flat from {prev_slot}, say so plainly — don't manufacture drama. Use it as a signal of indecision, then pivot to what's developing under the surface.
3. Use specific numbers and levels. No vague "the market is mixed."
4. Use only provided data. No buy/sell advice. Professional voice.
5. NEVER confess data gaps. If breadth unavailable, infer conviction from sector dispersion. Do NOT write "breadth data unavailable".
6. NO INVENTION OF CAUSATION (CRITICAL): If a stock (including a Nifty 100 mover) is moving sharply and NEWS / grounded search doesn't contain a specific catalyst for THAT stock, do NOT fabricate one. When cause is unknown: "X moved Y% on no specific visible catalyst" is FAR better than inventing one.
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

NIFTY 100 — TOP 5 GAINERS / TOP 5 LOSERS (give each highlighted name a NAMED reason; grounded search if active, else Pulse, else honest "no catalyst"):
{nifty100_movers_block}

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

{grounding_block}

YOUR TASK:
Write a structured 24-28 line wrap. This is the day's THESIS — pull together pre-market setup, how the day actually unfolded across 13 intraday slots, the close, and implications for tomorrow. The central question: WHAT WAS THE MARKET TRYING TO DO TODAY, and did it succeed? Use markdown headers.

STRUCTURE:

**The Close**
2-3 lines on Nifty/Sensex close — direction, magnitude, where on the day's range we settled. Specific levels.

**Catalysts**
This section is MANDATORY and is the spine of the wrap — it answers "WHY did the market do what it did", not "what it did". List the 2-4 concrete events, prints, or developments that actually drove today's session, each on its own line, in the form: [named catalyst] -> [transmission mechanism] -> [observed market effect]. Draw from: India macro prints (CPI/IIP/GDP/trade/PMI — name the actual figure), RBI/SEBI/government action or commentary, the USD/INR move (name the level or record), crude and gold moves, global wires (Fed/ECB/BoJ/OPEC/geopolitics/tariffs), large stock-specific news (results/M&A/regulatory/brokerage calls), and FII/DII provisional flow direction. Apply the CAUSAL CHAINS framework to every entry. If a single dominant catalyst drove the whole session, say so explicitly and trace its transmission across sectors. A material move with no identifiable trigger even after grounded search must be stated honestly here ("the X% move had no catalyst in today's news or filings") — but this is a last resort AFTER searching, never the default. Do NOT relegate event attribution to a passing clause inside The Story; it lives here, named and explicit.

**The Story**
4-5 lines on how the day unfolded. Reference the pre-market expectation: did it play out, or did the day reject the setup? Walk through the arc: open, mid-morning, midday, close. Identify inflection points using the slot summaries. State what the market was TRYING TO DO and whether it succeeded.

**Sector & Stock Highlights**
4-5 lines on which sectors led/lagged AND why. Apply the INTERPRETING MOVES checklist. Name 2-3 individual stocks with context — what the move means, not just the magnitude. Anchor at least two of these in the NIFTY 100 TOP-5 GAINERS / TOP-5 LOSERS block: take the standout gainer and standout loser of the Nifty 100 and give each a NAMED catalyst — use grounded search to identify the specific driver, fall back to the Pulse headlines/filings, and only if neither yields a cause state it honestly per the NO-INVENTION rule (do NOT just recite the ten percentages as a list). Apply CAUSAL CHAINS where the data supports them. Use grounded search if a large move needs a specific catalyst that Pulse didn't capture. Then place today's session against the 10-DAY SECTOR ROTATION block (the satellite/period view): did today extend the period's rotation (capital continuing into the favoured sectors) or reverse it? State the period read explicitly as relative strength, NOT measured rupee flow — e.g. "today's IT strength continues a 10-session rotation into exporters, accelerating; Metals remained under relative distribution".

**Technical Read**
3-4 lines on where the close leaves Nifty technically: above/below 20D and 50D MAs, position vs 52W high/low, distance from recent support/resistance. India VIX direction. Fold in the GLOBAL MACRO TELEMETRY where it shapes the forward setup — if DXY/US10Y are elevated or Brent is rising, state the specific headwind it imposes on tomorrow (FII-flow pressure, high-beta/growth drag, OMC-margin/CPI risk) rather than treating the technical picture in isolation. What does the combined technical + macro setup imply for tomorrow?

**Filings & Flows**
2-3 lines on the day's NSE filings if any were market-moving; state today's provisional FII/DII net cash figures and what the FII-vs-DII pattern reveals about who drove the session (e.g. FII selling absorbed by DII buying = domestic support under an FII-led decline), then read breadth (advance/decline) alongside it for conviction. Apply the MARKET IGNORING NEWS rule — was there material news the market ignored?

**Tomorrow**
2 lines on what matters {next_session_label} — a level being tested, a global event, a sector to watch. Frame as expectation. State what the market will likely be TRYING TO DO.

**Bottom Line**
One sentence — the day in a single insight a retail investor can take home. This MUST be a NON-OBVIOUS INSIGHT, not a recap.

RULES:
1. USE the data provided + Google Search for verifying catalysts and adding macro context. No invented numbers, news, or events.
2. Reference SPECIFIC LEVELS in the technical section.
3. Connect dots — what THEME explains today's price action?
4. NO buy/sell advice. Use Rs. for currency.
5. Professional desk voice.
6. NEVER confess data gaps. If a section's input is missing, quietly omit. Do NOT write "data unavailable", "while not explicitly provided", or similar.
7. NO INVENTION OF CAUSATION (CRITICAL): If a stock or sector had a big move and neither NEWS/FILINGS nor your grounded search yields a specific catalyst, do NOT fabricate one. When cause is unknown but the move is real: "Titan's -6% decline was the day's most notable outlier — no specific catalyst surfaced in today's news or filings."
8. NO SELF-REFERENCE: Just write the analysis.
9. ANTI-HEDGING (only when you HAVE evidence): direct claims when the evidence supports them; honest uncertainty when it doesn't.
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

FII / DII — TODAY'S PROVISIONAL CASH FLOW (institutional conviction):
{fii_dii_line}

GLOBAL MACRO TELEMETRY (structural inter-market inputs — tie to today's sector rotation via CAUSAL CHAINS):
{global_macro_line}

10-DAY SECTOR ROTATION — PERIOD/SATELLITE VIEW (relative-strength proxy, NOT measured rupee flow):
{sector_rotation_line}

SECTOR PERFORMANCE:
{sectors}

TOP STOCK MOVERS (by % change magnitude):
{top_stocks}

NIFTY 100 — TOP 5 GAINERS / TOP 5 LOSERS (anchor the Sector & Stock Highlights here; give the standout gainer and loser a NAMED catalyst via grounded search, else Pulse/filings, else honest "no catalyst"):
{nifty100_movers_block}

CURRENCIES:
{currencies}

COMMODITIES:
{commodities}

US MARKET STATUS (pre-open in New York):
{us_status}

TODAY'S NSE FILINGS (first 10):
{filings}

RECENT MARKET NEWS HEADLINES (last 12 hours, Indian financial press via Pulse — curated baseline):
{news_block}

{event_directive}

Now write the strategist post-market wrap:"""


# ─────────────────────────────────────────────────────────────────────────────
# PROMPT BUILDERS
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


def build_pre_market_prompt(packet: dict, use_grounding: bool = True) -> str:
    yest = packet.get("yesterday_post_text") or "(no recent post-market wrap on file)"
    sess_lbl = _last_session_label()
    # v2.5: pre-market event-attribution directive, grounding-conditional,
    # mirroring how grounding_block is gated.
    event_directive = (PRE_EVENT_ATTRIBUTION_GROUNDED if use_grounding
                       else PRE_EVENT_ATTRIBUTION_UNGROUNDED)
    return PRE_MARKET_PROMPT.format(
        shared_principles        = SHARED_PRINCIPLES,
        grounding_block          = GROUNDING_DISCIPLINE if use_grounding else "",
        event_directive          = event_directive,
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
        gift_line                = _format_gift_nifty(packet.get("gift_nifty") or {}),
        fii_dii_line             = _format_fii_dii(packet.get("fii_dii") or {}),
        breadth_line             = _format_breadth(packet.get("breadth") or {}),
        global_macro_line        = _format_global_macro(packet.get("global_macro") or {}),
        sector_rotation_line     = _format_sector_rotation(packet.get("sector_rotation") or {}),
        yesterday_wrap           = yest,
        news_block               = _format_pulse_headlines(packet.get("news") or []),
    )


def build_post_market_prompt(packet: dict, use_grounding: bool = True) -> str:
    prior = packet.get("prior") or {}
    # v2.4: event-attribution directive is grounding-conditional, mirroring
    # how grounding_block is gated. When grounding is live, search is mandated;
    # when off, Pulse is the primary event source.
    event_directive = EVENT_ATTRIBUTION_GROUNDED if use_grounding else EVENT_ATTRIBUTION_UNGROUNDED
    return POST_MARKET_PROMPT.format(
        shared_principles   = SHARED_PRINCIPLES,
        grounding_block     = GROUNDING_DISCIPLINE if use_grounding else "",
        event_directive     = event_directive,
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
        fii_dii_line        = _format_fii_dii(packet.get("fii_dii") or {}),
        global_macro_line   = _format_global_macro(packet.get("global_macro") or {}),
        sector_rotation_line = _format_sector_rotation(packet.get("sector_rotation") or {}),
        nifty100_movers_block = _format_nifty100_movers(packet.get("nifty100_movers") or {}),
        pre_context         = (prior.get("pre_text") or "[INSTRUCTION TO MODEL: No pre-market briefing on file. SKIP all 'compare to pre-market' comparisons. Do NOT mention pre-market is missing. Describe today's session on its own terms.]")[:1200],
        day_arc             = (prior.get("all_slots_compact") or "  [INSTRUCTION: No intraday slots recorded today. Skip the 'arc' walkthrough; describe the day from open to close using close-of-day data only.]"),
        news_block          = _format_pulse_headlines(packet.get("news") or []),
    )


def build_intraday_prompt(packet: dict, use_grounding: bool = False) -> str:
    prior = packet.get("prior", {}) or {}
    sess_lbl = _last_session_label()
    movers_block = _format_nifty100_movers(packet.get("nifty100_movers") or {})
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
            nifty100_movers_block = movers_block,
            asia_pacific        = _format_ticker_list(packet.get("asia_pacific", [])),
            currencies          = _format_ticker_list(packet.get("currencies",   [])),
            commodities         = _format_ticker_list(packet.get("commodities",  [])),
            technicals_block    = _build_technicals_block(packet),
            vix_line            = _build_vix_line(packet),
            breadth_line        = _format_breadth(packet.get("breadth") or {}),
            news_block          = _format_pulse_headlines(packet.get("news") or []),
        )
    prev_slot = prior.get("prev_slot") or "the prior slot"
    prev_ctx  = prior.get("prev_text") or "[INSTRUCTION: No prior intraday slot found. Write as a fresh update for this time. Do not mention prior context is missing.]"
    prev_pct  = prior.get("prev_nifty_pct")
    prev_summary = (f"{prev_pct:+.2f}% vs {sess_lbl} close" if isinstance(prev_pct, (int, float))
                    else "not recorded")
    pre_ctx_short = (prior.get("pre_text") or "[INSTRUCTION TO MODEL: No pre-market briefing on file. SKIP 'vs pre-market' framing. Do NOT mention pre-market is missing.]")[:900]
    day_arc = prior.get("all_slots_compact") or "  [INSTRUCTION: This is the first intraday update of the day; no earlier slots to reference.]"
    return INTRADAY_UPDATE_PROMPT.format(
        shared_principles  = SHARED_PRINCIPLES,
        grounding_block    = GROUNDING_DISCIPLINE if use_grounding else "",
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
        nifty100_movers_block = movers_block,
        currencies         = _format_ticker_list(packet.get("currencies",   [])),
        commodities        = _format_ticker_list(packet.get("commodities",  [])),
        asia_pacific       = _format_ticker_list(packet.get("asia_pacific", [])),
        technicals_block   = _build_technicals_block(packet),
        vix_line           = _build_vix_line(packet),
        breadth_line       = _format_breadth(packet.get("breadth") or {}),
        news_block         = _format_pulse_headlines(packet.get("news") or []),
    )


# ─────────────────────────────────────────────────────────────────────────────
# MODEL SELECTION
# ─────────────────────────────────────────────────────────────────────────────
def _is_event_day(packet: dict) -> bool:
    """Detect whether today warrants stronger model for intraday."""
    nifty = packet.get("nifty")
    if not nifty and packet.get("india_prev"):
        for t in packet["india_prev"]:
            if t and t.get("label") == "NIFTY 50":
                nifty = t
                break
    if isinstance(nifty, dict) and nifty.get("pct") is not None:
        if abs(nifty.get("pct", 0)) >= 1.5:
            return True

    vix = packet.get("india_vix") or {}
    if vix.get("trend_5d_pct") is not None:
        if abs(vix["trend_5d_pct"]) >= 15:
            return True

    breadth = packet.get("breadth") or {}
    ratio = breadth.get("ad_ratio")
    if ratio is not None and ratio > 0:
        if ratio >= 3.0 or ratio <= 0.33:
            return True

    return False


def _select_model(mode: str, packet: dict, will_ground: bool = False) -> tuple:
    """
    Returns (model_name, max_output_tokens).
    Post-market always Pro. Pre-market always Pro. Intraday upgrades to Pro
    on event days OR when grounded (v3.0: the 15:30 close slot is grounded
    and grounding works best on Pro, with a larger token budget than the
    cheap Flash-Lite intraday default).
    """
    if mode == "post":
        return (GEMINI_MODEL_STRONG, 8000)
    if mode == "pre":
        # pre-market also goes to Pro (grounding works best on Pro)
        return (GEMINI_MODEL_STRONG, 8000)
    # Intraday
    if will_ground:
        # grounded intraday (15:30 close) — Pro + room for the wrap-style read
        return (GEMINI_MODEL_STRONG, 6000)
    if _is_event_day(packet):
        return (GEMINI_MODEL_STRONG, 6000)
    return (GEMINI_MODEL_FAST, 500)


# ─────────────────────────────────────────────────────────────────────────────
# GEMINI CALLS — non-grounded (intraday) and grounded (pre/post)
# ─────────────────────────────────────────────────────────────────────────────
def call_gemini(prompt: str, model: str = None, max_tokens: int = 900):
    """Non-grounded Gemini call — used for intraday slots."""
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
        call_timeout = 180 if "pro" in model else 45
        response = gen_model.generate_content(
            prompt,
            generation_config={
                "temperature":       0.5,
                "max_output_tokens": max_tokens,
                "top_p":             0.9,
            },
            request_options={"timeout": call_timeout},
        )
        if response and response.text:
            text = response.text.strip()
            if len(text) < 80:
                _log("⚠️", f"Gemini returned too-short text ({len(text)} chars)")
                return None, "error"
            _log("✅", f"Gemini returned {len(text)} characters ({model})")
            source_tag = "gemini_pro" if "pro" in model else "gemini_flash"
            return text, source_tag
        _log("⚠️", "Gemini returned empty response")
        return None, "error"
    except Exception as e:
        _log("⚠️", f"Gemini API error: {e}")
        return None, "error"


def _extract_grounding_sources(response) -> list:
    """
    Pulls the list of grounding citations from a grounded response.
    Returns a list of {title, uri} dicts. Empty list if no grounding metadata
    or the model decided not to ground this call.
    """
    sources = []
    try:
        candidates = getattr(response, "candidates", None) or []
        if not candidates:
            return sources
        cand = candidates[0]
        gm = getattr(cand, "grounding_metadata", None)
        if gm is None:
            # Some SDK versions nest it inside the response prototype
            gm_dict = None
            try:
                gm_dict = response.to_dict().get("candidates", [{}])[0].get("grounding_metadata")
            except Exception:
                pass
            if not gm_dict:
                return sources
            chunks = gm_dict.get("grounding_chunks") or gm_dict.get("groundingChunks") or []
            for c in chunks:
                web = c.get("web") or {}
                title = web.get("title") or ""
                uri   = web.get("uri")   or ""
                if uri:
                    sources.append({"title": title[:200], "uri": uri[:500]})
            return sources

        # Object-form access
        chunks = getattr(gm, "grounding_chunks", None) or []
        for c in chunks:
            web = getattr(c, "web", None)
            if not web:
                continue
            title = getattr(web, "title", "") or ""
            uri   = getattr(web, "uri",   "") or ""
            if uri:
                sources.append({"title": title[:200], "uri": uri[:500]})
    except Exception as e:
        _log("⚠️", f"Could not parse grounding metadata: {e}")
    return sources


def call_gemini_grounded(prompt: str, model: str = None, max_tokens: int = 8000):
    """
    Grounded Gemini call — uses Google Search to fetch live web context.
    Used for pre-market and post-market slots only.

    Returns (text, source_tag, grounding_sources).
    grounding_sources is a list of {title, uri} dicts for audit/storage.
    """
    if not GEMINI_AVAILABLE:
        _log("⚠️", "google-generativeai package not installed")
        return None, "error", []
    if not GEMINI_API_KEY:
        _log("⚠️", "GEMINI_API_KEY not set")
        return None, "error", []

    model = model or GEMINI_MODEL_STRONG
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gen_model = genai.GenerativeModel(model)
        _log("🌐", f"Calling Gemini GROUNDED ({model}, max_tokens={max_tokens})...")

        # Grounded Pro calls can take 30-120s (search + thinking + generation).
        call_timeout = 240

        response = None
        last_err = None
        tools_used = None

        # Gemini 2.0+ uses 'google_search'. Legacy SDK / older models use 'google_search_retrieval'.
        # We try the modern form first and fall back if the SDK rejects it.
        for tool_spec in ("google_search", "google_search_retrieval"):
            try:
                response = gen_model.generate_content(
                    prompt,
                    generation_config={
                        "temperature":       0.5,
                        "max_output_tokens": max_tokens,
                        "top_p":             0.9,
                    },
                    tools=tool_spec,
                    request_options={"timeout": call_timeout},
                )
                tools_used = tool_spec
                _log("🔧", f"Grounding tool accepted: {tool_spec}")
                break
            except Exception as e:
                last_err = e
                msg = str(e).lower()
                # Only fall through if the SDK explicitly rejected this tool name
                if any(k in msg for k in ("tool", "unknown", "invalid", "not supported", "unsupported")):
                    _log("🔄", f"{tool_spec} rejected by SDK ({type(e).__name__}), trying alternate form...")
                    continue
                # Any other error (timeout, auth, quota) — don't retry, just raise
                raise

        if response is None:
            raise RuntimeError(f"Both grounding tool forms failed. Last error: {last_err}")

        if not response.text:
            _log("⚠️", "Gemini grounded call returned empty response")
            return None, "error", []

        text = response.text.strip()
        if len(text) < 80:
            _log("⚠️", f"Gemini grounded returned too-short text ({len(text)} chars)")
            return None, "error", []

        sources = _extract_grounding_sources(response)
        _log("✅", f"Gemini grounded returned {len(text)} chars with {len(sources)} source(s) "
                   f"[tool={tools_used}]")

        source_tag = "gemini_pro_grounded" if sources else "gemini_pro_grounded_nosrc"
        return text, source_tag, sources

    except Exception as e:
        _log("⚠️", f"Gemini grounded API error: {e}")
        # Caller will fall back to non-grounded call
        return None, "error", []


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
# SUPABASE CACHE WRITE
# ─────────────────────────────────────────────────────────────────────────────
def save_commentary(commentary_type: str, slot: str, text: str, source: str,
                    packet: dict, grounding_sources: list = None) -> bool:
    if not supabase:
        _log("⚠️", "Supabase not configured — skipping save")
        return False
    try:
        date = _today_ist()
        slot_full = f"{slot}:00"
        # Persist grounding sources inside data_snapshot for audit
        snapshot = dict(packet) if isinstance(packet, dict) else {}
        if grounding_sources:
            snapshot["_grounding_sources"] = grounding_sources
        supabase.table("market_commentary").upsert(
            {
                "commentary_type": commentary_type,
                "commentary_date": date,
                "slot_time":       slot_full,
                "commentary_text": text,
                "source":          source,
                "data_snapshot":   json.dumps(snapshot, default=str),
            },
            on_conflict="commentary_type,commentary_date,slot_time",
        ).execute()
        src_count = len(grounding_sources) if grounding_sources else 0
        _log("💾", f"Saved {commentary_type} commentary for {date} {slot} "
                   f"(source={source}, grounded_sources={src_count})")
        return True
    except Exception as e:
        _log("⚠️", f"Supabase save failed: {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# ORCHESTRATION
# ─────────────────────────────────────────────────────────────────────────────
def generate_commentary(mode: str, slot: str = None, dry_run: bool = False,
                        use_grounding: bool = True):
    _log("🚀", f"Starting {mode.upper()} commentary generation (slot={slot}, grounding={use_grounding})")
    _log("📅", f"IST now: {_now_ist_str()}")

    # Grounding is used for pre/post and for the grounded intraday slots
    # (v3.0: the 15:30 close slot). All other intraday slots stay non-grounded.
    grounded_modes = {"pre", "post"}
    will_ground = use_grounding and (mode in grounded_modes)

    if mode == "pre":
        slot   = slot or PRE_SLOT
        packet = build_pre_market_packet()
        prompt = build_pre_market_prompt(packet, use_grounding=will_ground)
    elif mode == "post":
        slot   = slot or POST_SLOT
        packet = build_post_market_packet()
        prompt = build_post_market_prompt(packet, use_grounding=will_ground)
    elif mode == "intraday":
        if slot is None:
            now = datetime.now(IST)
            slot = _snap_to_intraday_slot(now.hour, now.minute)
        elif slot not in INTRADAY_SLOTS:
            _log("⚠️", f"Slot {slot} not in canonical list — snapping")
            sh, sm = map(int, slot.split(":"))
            slot = _snap_to_intraday_slot(sh, sm)
        # v3.0: resolve grounding now that the intraday slot is known.
        will_ground = use_grounding and slot in GROUNDED_INTRADAY_SLOTS
        if will_ground:
            _log("🌐", f"Intraday slot {slot} is a GROUNDED slot — "
                       f"routing to grounded Pro path")
        packet = build_intraday_packet(slot)
        prompt = build_intraday_prompt(packet, use_grounding=will_ground)
    else:
        _log("❌", f"Unknown mode: {mode}")
        return None

    model, max_tokens = _select_model(mode, packet, will_ground=will_ground)
    is_event = _is_event_day(packet)
    if is_event and mode == "intraday":
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
        print(f"DRY RUN — prompt for {mode} {slot} (model={model}, grounded={will_ground}):")
        print("=" * 70)
        print(prompt)
        print("=" * 70)

    # Dispatch: grounded for pre/post and the grounded intraday slot,
    # non-grounded for all other intraday slots.
    grounding_sources = []
    if will_ground:
        text, source, grounding_sources = call_gemini_grounded(
            prompt, model=model, max_tokens=max_tokens
        )
        # Fallback: if grounded call fails entirely, try a non-grounded call
        # on the same model before falling all the way to rule-based.
        # v2.4: rebuild the prompt WITHOUT grounding directives first, so we
        # don't instruct a non-grounded model that "Google Search is ACTIVE".
        if not text:
            _log("🔁", "Grounded call failed — rebuilding prompt non-grounded and retrying")
            if mode == "pre":
                prompt = build_pre_market_prompt(packet, use_grounding=False)
            elif mode == "post":
                prompt = build_post_market_prompt(packet, use_grounding=False)
            elif mode == "intraday":
                prompt = build_intraday_prompt(packet, use_grounding=False)
            text, source = call_gemini(prompt, model=model, max_tokens=max_tokens)
    else:
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
    if grounding_sources:
        print("\n--- GROUNDING SOURCES ---")
        for i, s in enumerate(grounding_sources, 1):
            print(f"  [{i}] {s.get('title', '?')[:80]}")
            print(f"      {s.get('uri', '?')[:120]}")
    print("=" * 70 + "\n")

    if dry_run:
        _log("🏁", "Dry run complete — nothing saved")
        return {
            "text": text, "source": source, "saved": False,
            "slot": slot, "model": model,
            "grounding_sources": grounding_sources,
        }

    saved = save_commentary(mode, slot, text, source, packet,
                            grounding_sources=grounding_sources)
    return {
        "text": text, "source": source, "saved": saved,
        "slot": slot, "model": model,
        "grounding_sources": grounding_sources,
    }


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="MoneyVeda Market Commentary v3.0")
    parser.add_argument("--mode", choices=["pre", "intraday", "post", "auto"], default="auto",
                        help="'auto' detects from current IST time (default)")
    parser.add_argument("--slot", default=None,
                        help="Intraday slot HH:MM (e.g. 10:30). Optional.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print prompt and output but do not save to Supabase")
    parser.add_argument("--no-grounding", action="store_true",
                        help="Disable Google Search grounding for this run (pre/post only)")
    parser.add_argument("--force", action="store_true",
                        help="Bypass the pre-market 08:00 IST time guard "
                             "(use only for manual/ad-hoc regeneration)")
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

    # Hard guard: pre-market may ONLY run inside the 08:00 IST window.
    # This protects against a misconfigured cron invoking `--mode pre`
    # off-schedule (e.g. the 07:30 IST tick). --dry-run and --force bypass.
    if mode == "pre" and not args.dry_run and not args.force:
        if not _is_pre_market_time():
            _log("⏭️", f"`--mode pre` invoked at {_now_ist_str()}, outside the "
                       f"08:00 IST pre-market window (07:52–08:08). Exiting "
                       f"cleanly — no pre-market briefing generated. "
                       f"Use --force to override.")
            sys.exit(0)

    missing = []
    if not SUPABASE_URL:        missing.append("SUPABASE_URL")
    if not SUPABASE_SECRET_KEY: missing.append("SUPABASE_SECRET_KEY")
    if not GEMINI_API_KEY:      missing.append("GEMINI_API_KEY")
    if missing and not args.dry_run:
        print(f"❌ Missing env vars: {', '.join(missing)}")
        sys.exit(1)

    use_grounding = not args.no_grounding
    result = generate_commentary(mode, slot=slot, dry_run=args.dry_run,
                                 use_grounding=use_grounding)
    if not result:
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
