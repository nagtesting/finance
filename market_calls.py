"""MoneyVeda continuity + scorecard engine.

Turns each commentary's forward-looking CALLS into structured, gradeable rows,
grades them against the actual close, and feeds the running track record back
into future prompts. This is what converts isolated daily posts into one
serialized, accountable voice — the part readers come back for.

No Gemini calls of its own. Calls are emitted by the commentary model inside a
fenced ===CALLS=== JSON block (zero extra cost), parsed here, and graded
deterministically against index levels the post-market packet already holds.

Integration (all in market_commentary.py, which owns `supabase`):

    import market_calls

    # after the model returns `text`, before printing/saving:
    text, _raw_calls = market_calls.parse_calls_block(text)

    # after save_commentary() returns True:
    if saved and _raw_calls:
        market_calls.insert_calls(supabase, _raw_calls,
                                  _today_ist(), mode, f"{slot}:00")

    # post-market only, after build_post_market_packet(): grade, then inject.
    # pre-market: just inject the scorecard block (read-only).

See the wiring notes in the chat for exact placement.
"""

import json
import re
from datetime import datetime, timezone

CALLS_DELIM = "===CALLS==="

# Subjects we can name and (for index subjects) machine-grade.
SUBJECTS = {"NIFTY", "SENSEX", "BANKNIFTY", "CRUDE", "GOLD", "USDINR", "BROAD", "MARKET"}
_DIRECTIONS = {"up", "down", "flat", "range", "hold", "break"}
_COMPARATORS = {"above", "below", "holds", "breaks"}
_HORIZONS = {"intraday", "today_close", "next_session"}

# Drop this into the end of each prompt (format with the horizon label).
CALLS_EMISSION_INSTRUCTION = (
    "\n\nAFTER your commentary, on a new line, output EXACTLY this token:\n"
    f"{CALLS_DELIM}\n"
    "followed by a JSON array of 1-3 SPECIFIC, FALSIFIABLE calls you are making "
    "for {horizon_label}. Shape of each call:\n"
    '{{"subject":"NIFTY","claim":"Nifty\'s gap-up fades and it closes below 23,600",'
    '"direction":"down","level":23600,"comparator":"below","horizon":"today_close",'
    '"confidence":"med"}}\n'
    "Rules: subject in [NIFTY, SENSEX, BANKNIFTY, CRUDE, GOLD, USDINR, BROAD]; "
    "direction in [up, down, flat, range, hold, break]; ALWAYS include a numeric "
    "`level` and a `comparator` whenever you name a level in the prose; only make "
    "calls you would publicly stand behind. If you genuinely have no falsifiable "
    "call, output an empty array []. This block is machine-read and is STRIPPED "
    "from what readers see — do not reference it in the prose."
)


# ── Capture ──────────────────────────────────────────────────────────────────

def parse_calls_block(text: str):
    """Split model output into (clean_prose, [raw_call_dicts]).

    The model appends, after its prose:
        ===CALLS===
        [ {...}, {...} ]
    Robust to ```json fences. Returns prose with the block removed.
    """
    if not text or CALLS_DELIM not in text:
        return (text or "").strip(), []
    prose, _, tail = text.partition(CALLS_DELIM)
    match = re.search(r"\[.*\]", tail, re.DOTALL)
    calls = []
    if match:
        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, list):
                calls = parsed
        except Exception:
            calls = []
    return prose.strip(), calls


def _norm_call(c, call_date, commentary_type, slot_time):
    if not isinstance(c, dict):
        return None
    claim = (c.get("claim") or "").strip()
    if not claim:
        return None

    subject = (c.get("subject") or "MARKET").strip().upper()[:32]
    if subject not in SUBJECTS:
        subject = "MARKET"

    direction = (c.get("direction") or "").strip().lower() or None
    if direction not in _DIRECTIONS:
        direction = None

    comparator = (c.get("comparator") or "").strip().lower() or None
    if comparator not in _COMPARATORS:
        comparator = None

    horizon = (c.get("horizon") or "next_session").strip().lower()
    if horizon not in _HORIZONS:
        horizon = "next_session"

    confidence = (c.get("confidence") or "med").strip().lower()
    if confidence not in {"low", "med", "high"}:
        confidence = "med"

    level = c.get("level")
    try:
        level = float(level) if level is not None else None
    except (TypeError, ValueError):
        level = None

    return {
        "call_date": call_date,
        "commentary_type": commentary_type,
        "slot_time": slot_time,
        "subject": subject,
        "claim_text": claim[:300],
        "direction": direction,
        "level": level,
        "comparator": comparator,
        "horizon": horizon,
        "confidence": confidence,
        "status": "open",
    }


def insert_calls(db, raw_calls, call_date, commentary_type, slot_time, max_calls=3):
    """Validate + persist the calls a commentary just made. Returns count inserted."""
    if not db or not raw_calls:
        return 0
    rows = []
    for c in raw_calls[:max_calls]:
        r = _norm_call(c, call_date, commentary_type, slot_time)
        if r:
            rows.append(r)
    if not rows:
        return 0
    try:
        db.table("market_calls").insert(rows).execute()
        print(f"[calls] inserted {len(rows)} call(s) for "
              f"{call_date} {commentary_type} {slot_time}")
        return len(rows)
    except Exception as exc:
        print(f"[calls] insert failed: {exc}")
        return 0


# ── Grading ──────────────────────────────────────────────────────────────────

def _grade_one(call, vals):
    """Return (status, note, value). status is None when not machine-gradeable.

    `vals` maps SUBJECT -> {"value": close, "pct": day_pct}.
    Level calls grade on the close; direction calls grade on the day %.
    """
    v = vals.get(call.get("subject"))
    if not v:
        return None, "no data for subject", None

    actual_val = v.get("value")
    actual_pct = v.get("pct")
    level = call.get("level")
    comp = call.get("comparator")
    direction = call.get("direction")

    # Level-based call (most specific, grade first).
    if level is not None and actual_val is not None:
        if comp in {"holds", "above"}:
            hit = actual_val >= level
        elif comp in {"breaks", "below"}:
            hit = actual_val < level
        else:  # bare level -> read as "reaches/holds at or above"
            hit = actual_val >= level
        note = f"{call['subject']} {actual_val:,.0f} vs {comp or 'level'} {level:,.0f}"
        return ("hit" if hit else "miss"), note, actual_val

    # Direction-based call.
    if direction and actual_pct is not None:
        if direction == "up":
            hit = actual_pct > 0.1
        elif direction == "down":
            hit = actual_pct < -0.1
        elif direction == "flat":
            hit = abs(actual_pct) <= 0.3
        else:  # range / hold / break without a level -> needs a human
            return None, "needs manual grade", None
        note = f"{call['subject']} closed {actual_pct:+.2f}%"
        return ("hit" if hit else "miss"), note, actual_pct

    return None, "not machine-gradeable", None


def grade_open_calls(db, vals, call_date, horizons):
    """Grade open calls made on `call_date` with the given horizons against `vals`.

    Returns (hit, miss, skipped). Ungradeable calls are left open (a later run,
    or a human, can resolve them). Caller builds `vals` from the post packet.
    """
    if not db:
        return (0, 0, 0)
    try:
        res = (db.table("market_calls").select("*")
               .eq("status", "open")
               .eq("call_date", call_date)
               .in_("horizon", list(horizons))
               .execute())
    except Exception as exc:
        print(f"[calls] grade fetch failed: {exc}")
        return (0, 0, 0)

    hit = miss = skipped = 0
    for call in (res.data or []):
        status, note, value = _grade_one(call, vals)
        if status is None:
            skipped += 1
            continue
        try:
            (db.table("market_calls").update({
                "status": status,
                "outcome_note": note,
                "outcome_value": value,
                "graded_at": datetime.now(timezone.utc).isoformat(),
            }).eq("id", call["id"]).execute())
            hit += (status == "hit")
            miss += (status == "miss")
        except Exception as exc:
            print(f"[calls] grade update failed for {call.get('id')}: {exc}")
    print(f"[calls] graded {call_date} {tuple(horizons)}: "
          f"hit={hit} miss={miss} skipped={skipped}")
    return (hit, miss, skipped)


def build_index_vals(packet, mapping=None):
    """Convenience: turn the post packet into the `vals` grading dict.

    Default maps the confirmed packet keys nifty/sensex. Extend `mapping` with
    more once you confirm the packet keys (e.g. ("banknifty","BANKNIFTY")).
    """
    mapping = mapping or [("nifty", "NIFTY"), ("sensex", "SENSEX")]
    vals = {}
    for key, subject in mapping:
        d = packet.get(key) if isinstance(packet, dict) else None
        if isinstance(d, dict) and d.get("value") is not None:
            vals[subject] = {"value": d.get("value"), "pct": d.get("pct")}
    return vals


# ── Continuity injection ─────────────────────────────────────────────────────

def get_scorecard_block(db, recent_n=6, window=60):
    """Prompt-ready track record + recent graded calls. '' if nothing graded yet."""
    if not db:
        return ""
    try:
        res = (db.table("market_calls")
               .select("call_date,commentary_type,subject,claim_text,status,outcome_note")
               .in_("status", ["hit", "miss"])
               .order("graded_at", desc=True)
               .limit(window)
               .execute())
    except Exception as exc:
        print(f"[calls] scorecard fetch failed: {exc}")
        return ""

    rows = res.data or []
    if not rows:
        return ""

    hits = sum(1 for r in rows if r["status"] == "hit")
    total = len(rows)
    pct = round(100 * hits / total) if total else 0

    lines = [f"TRACK RECORD (last {total} graded calls): {hits}/{total} hit ({pct}%)."]
    lines.append("Most recent graded calls:")
    for r in rows[:recent_n]:
        mark = "HIT " if r["status"] == "hit" else "MISS"
        note = r.get("outcome_note") or ""
        lines.append(f"  [{mark}] {r['call_date']} {r['subject']}: "
                     f"{r['claim_text']}{(' — ' + note) if note else ''}")
    return "\n".join(lines)


def scorecard_directive(block):
    """Wrap the scorecard block with the open-by-settling-your-last-call rule."""
    if not block:
        return ""
    return (
        "YOUR RUNNING TRACK RECORD (this is real, persisted, and shown to readers):\n"
        f"{block}\n\n"
        "OPEN this commentary by settling your most recent call(s): if a recent "
        "call HIT, say so once with quiet confidence; if it MISSED, OWN it plainly "
        "in a single honest line before moving on. Never bury or spin a miss — the "
        "honesty is the entire reason a reader trusts this voice over a tip channel."
    )
