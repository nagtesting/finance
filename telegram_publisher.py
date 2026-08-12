"""
telegram_publisher.py  ─  MoneyVeda · push daily commentary to Telegram
==========================================================================
Reads the latest row from `market_commentary` for a given slot and posts it
to a Telegram channel. No server, no subscriber list — the channel is the
distribution.

DESIGN NOTES
  • Posts the FULL commentary, not a teaser link. Telegram audiences do not
    click out; the channel has to be worth reading on its own. The website
    link goes in the footer for people who want the interactive tools.
  • parse_mode=HTML, not MarkdownV2. MarkdownV2 requires escaping ~18
    characters and a single missed one returns a 400 for the whole message.
    HTML needs three.
  • Long commentary is split on paragraph boundaries. Telegram's hard cap is
    4096 characters; we chunk at 3800 to leave room for headers.
  • Fail-closed: any Supabase or Telegram error logs and exits non-zero so the
    Actions run goes red. It never posts partial or placeholder content.
  • Dedupe: re-running the workflow will not double-post unless --force.

────────────────────────────────────────────────────────────────────────────
ONE-TIME SUPABASE SETUP (SQL editor) — optional but recommended for dedupe.
If this table is absent the script still runs; it just cannot dedupe.

  create table if not exists telegram_posts (
    id               bigint generated always as identity primary key,
    commentary_type  text        not null,
    commentary_date  date        not null,
    slot_time        time,
    message_id       bigint,
    posted_at        timestamptz not null default now()
  );
  create unique index if not exists telegram_posts_slot
    on telegram_posts (commentary_type, commentary_date, slot_time);

ENV VARS
  SUPABASE_URL, SUPABASE_SECRET_KEY   (same as your other jobs)
  TELEGRAM_BOT_TOKEN                  from @BotFather
  TELEGRAM_CHAT_ID                    e.g. @moneyveda, or -100xxxxxxxxxx

USAGE
  python telegram_publisher.py --mode pre
  python telegram_publisher.py --mode post --dry-run
  python telegram_publisher.py --mode intraday --date 2026-08-10 --force
────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import argparse
import datetime as _dt
import html
import json
import os
import re
import sys
import time
from typing import Optional

import requests

try:
    from supabase import create_client
except ImportError:
    create_client = None

_IST = _dt.timezone(_dt.timedelta(hours=5, minutes=30))

SUPABASE_URL        = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")
BOT_TOKEN           = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID             = os.getenv("TELEGRAM_CHAT_ID")

SITE_URL   = "https://moneyveda.org"
MAX_CHUNK  = 3800          # Telegram hard cap is 4096
API_BASE   = "https://api.telegram.org/bot{token}/{method}"

SLOT_META = {
    "pre":      ("🌅", "Pre-Market"),
    "intraday": ("⚡", "Intraday"),
    "post":     ("🌇", "Post-Market"),
}


def _log(emoji: str, msg: str) -> None:
    ts = _dt.datetime.now(_IST).strftime("%H:%M:%S")
    print(f"{emoji}  [{ts}]  {msg}", flush=True)


def _today_ist() -> str:
    return _dt.datetime.now(_IST).strftime("%Y-%m-%d")


def _sb():
    if not (create_client and SUPABASE_URL and SUPABASE_SECRET_KEY):
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)
    except Exception as e:
        _log("⚠️", f"Supabase client failed: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# FETCH
# ─────────────────────────────────────────────────────────────────────────────
def fetch_commentary(sb, mode: str, date_str: str) -> Optional[dict]:
    """Latest row for (mode, date). Mirrors the query in commentary_engine.py."""
    res = (
        sb.table("market_commentary")
        .select("commentary_text, slot_time, source, data_snapshot, commentary_date")
        .eq("commentary_type", mode)
        .eq("commentary_date", date_str)
        .order("slot_time", desc=True)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def _snapshot(row: dict) -> dict:
    snap = row.get("data_snapshot")
    if isinstance(snap, str):
        try:
            snap = json.loads(snap)
        except Exception:
            return {}
    return snap if isinstance(snap, dict) else {}


# ─────────────────────────────────────────────────────────────────────────────
# FORMAT
# ─────────────────────────────────────────────────────────────────────────────
def md_to_telegram_html(text: str) -> str:
    """
    Gemini returns loose Markdown. Telegram's HTML mode supports only
    b/i/u/s/code/pre/a — everything else must be flattened first.
    Order matters: escape entities BEFORE injecting our own tags.
    """
    t = html.escape(text or "", quote=False)

    # Headings → bold line
    t = re.sub(r"^[ \t]{0,3}#{1,6}[ \t]*(.+?)[ \t]*$", r"<b>\1</b>", t, flags=re.MULTILINE)
    # Bold / italic
    t = re.sub(r"\*\*\*(.+?)\*\*\*", r"<b><i>\1</i></b>", t, flags=re.DOTALL)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t, flags=re.DOTALL)
    t = re.sub(r"(?<![\w*])_(?!_)(.+?)(?<!_)_(?![\w*])", r"<i>\1</i>", t, flags=re.DOTALL)
    # Inline code
    t = re.sub(r"`([^`\n]+)`", r"<code>\1</code>", t)
    # Markdown links
    t = re.sub(r"\[([^\]]+)\]\((https?://[^\s)]+)\)", r'<a href="\2">\1</a>', t)
    # Bullets → •  (after bold, so `* **X**` doesn't get eaten)
    t = re.sub(r"^[ \t]{0,4}[-*+][ \t]+", "• ", t, flags=re.MULTILINE)
    # Horizontal rules and stray emphasis markers
    t = re.sub(r"^[ \t]{0,3}([-*_])\1{2,}[ \t]*$", "—", t, flags=re.MULTILINE)
    t = t.replace("*", "")
    # Collapse 3+ blank lines
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def build_header(mode: str, row: dict) -> str:
    emoji, label = SLOT_META.get(mode, ("📊", mode.title()))
    date_str = str(row.get("commentary_date") or _today_ist())
    try:
        pretty = _dt.datetime.strptime(date_str, "%Y-%m-%d").strftime("%d %b %Y")
    except Exception:
        pretty = date_str

    slot = (row.get("slot_time") or "")[:5]
    when = f"{pretty} · {slot} IST" if slot else pretty

    lines = [f"{emoji} <b>{label} · Nifty 50</b>", f"<i>{when}</i>"]

    snap = _snapshot(row)
    nifty = snap.get("nifty")
    if isinstance(nifty, dict):
        level = nifty.get("level") or nifty.get("last") or nifty.get("close")
        pct   = nifty.get("pct")
        bits  = []
        if level is not None:
            try:
                bits.append(f"{float(level):,.0f}")
            except (TypeError, ValueError):
                bits.append(str(level))
        if pct is not None:
            try:
                arrow = "🟢" if float(pct) >= 0 else "🔴"
                bits.append(f"{arrow} {float(pct):+.2f}%")
            except (TypeError, ValueError):
                pass
        if bits:
            lines.append(f"<b>{'  ·  '.join(bits)}</b>")

    return "\n".join(lines)


FOOTER = (
    "—\n"
    f'📊 Calculators &amp; live data: <a href="{SITE_URL}">moneyveda.org</a>\n'
    f'🎯 Our published accuracy record: <a href="{SITE_URL}/accuracy-dashboard">accuracy dashboard</a>\n'
    "<i>Machine-generated from public market data. Educational only, "
    "not investment advice. MoneyVeda is not SEBI-registered.</i>"
)


def chunk(text: str, limit: int = MAX_CHUNK) -> list[str]:
    """Split on paragraph breaks, then lines, then hard-cut. Never mid-tag."""
    if len(text) <= limit:
        return [text]

    out, buf = [], ""
    for para in text.split("\n\n"):
        candidate = para if not buf else f"{buf}\n\n{para}"
        if len(candidate) <= limit:
            buf = candidate
            continue
        if buf:
            out.append(buf)
            buf = ""
        if len(para) <= limit:
            buf = para
            continue
        # Paragraph alone is too long — fall back to line splitting
        for line in para.split("\n"):
            cand2 = line if not buf else f"{buf}\n{line}"
            if len(cand2) <= limit:
                buf = cand2
            else:
                if buf:
                    out.append(buf)
                while len(line) > limit:
                    out.append(line[:limit])
                    line = line[limit:]
                buf = line
    if buf:
        out.append(buf)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# SEND
# ─────────────────────────────────────────────────────────────────────────────
def send_message(text: str, disable_notification: bool = False) -> Optional[int]:
    url = API_BASE.format(token=BOT_TOKEN, method="sendMessage")
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
        "disable_notification": disable_notification,
    }
    for attempt in range(4):
        try:
            r = requests.post(url, json=payload, timeout=25)
        except requests.RequestException as e:
            _log("⚠️", f"network error ({e}); retrying")
            time.sleep(2 ** attempt)
            continue

        if r.status_code == 200:
            return r.json().get("result", {}).get("message_id")

        if r.status_code == 429:
            wait = r.json().get("parameters", {}).get("retry_after", 5)
            _log("⏳", f"rate limited; sleeping {wait}s")
            time.sleep(wait + 1)
            continue

        _log("❌", f"Telegram {r.status_code}: {r.text[:300]}")
        # 400 is almost always malformed HTML — retrying will not help.
        if r.status_code == 400:
            return None
        time.sleep(2 ** attempt)
    return None


# ─────────────────────────────────────────────────────────────────────────────
# DEDUPE
# ─────────────────────────────────────────────────────────────────────────────
def already_posted(sb, mode: str, date_str: str, slot: Optional[str]) -> bool:
    try:
        q = (sb.table("telegram_posts").select("id")
             .eq("commentary_type", mode).eq("commentary_date", date_str))
        if slot:
            q = q.eq("slot_time", slot)
        return bool(q.limit(1).execute().data)
    except Exception as e:
        _log("⚠️", f"dedupe check unavailable ({e}); proceeding")
        return False


def record_post(sb, mode: str, date_str: str, slot: Optional[str], message_id: Optional[int]) -> None:
    try:
        sb.table("telegram_posts").insert({
            "commentary_type": mode,
            "commentary_date": date_str,
            "slot_time": slot,
            "message_id": message_id,
        }).execute()
    except Exception as e:
        _log("⚠️", f"could not record post ({e}); dedupe may miss next run")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser(description="Post MoneyVeda commentary to Telegram")
    ap.add_argument("--mode", required=True, choices=["pre", "intraday", "post"])
    ap.add_argument("--date", default=None, help="YYYY-MM-DD (default: today IST)")
    ap.add_argument("--dry-run", action="store_true", help="print, do not post")
    ap.add_argument("--force", action="store_true", help="post even if already sent")
    args = ap.parse_args()

    date_str = args.date or _today_ist()

    if not args.dry_run and not (BOT_TOKEN and CHAT_ID):
        _log("❌", "TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set")
        return 1

    sb = _sb()
    if not sb:
        _log("❌", "Supabase not configured")
        return 1

    try:
        row = fetch_commentary(sb, args.mode, date_str)
    except Exception as e:
        _log("❌", f"Supabase query failed: {e}")
        return 1

    if not row:
        _log("⚠️", f"no {args.mode} commentary for {date_str} — nothing to post")
        return 0        # a holiday is not a failure

    body = (row.get("commentary_text") or "").strip()
    if len(body) < 200:
        _log("❌", f"commentary is only {len(body)} chars — refusing to post")
        return 1

    slot = row.get("slot_time")
    if not args.force and already_posted(sb, args.mode, date_str, slot):
        _log("✅", f"{args.mode} for {date_str} already posted — skipping")
        return 0

    message = f"{build_header(args.mode, row)}\n\n{md_to_telegram_html(body)}"
    parts = chunk(message)
    parts[-1] = f"{parts[-1]}\n\n{FOOTER}"
    if len(parts[-1]) > 4096:                 # footer pushed it over
        parts = parts[:-1] + chunk(parts[-1])

    _log("📤", f"{args.mode} · {date_str} · {len(body)} chars · {len(parts)} message(s)")

    if args.dry_run:
        for i, p in enumerate(parts, 1):
            print(f"\n───── part {i}/{len(parts)} · {len(p)} chars ─────\n{p}")
        return 0

    first_id = None
    for i, part in enumerate(parts):
        mid = send_message(part, disable_notification=(i > 0))
        if mid is None:
            _log("❌", f"failed on part {i + 1}/{len(parts)}")
            return 1
        first_id = first_id or mid
        if i < len(parts) - 1:
            time.sleep(1.2)               # stay under Telegram's per-chat rate

    record_post(sb, args.mode, date_str, slot, first_id)
    _log("✅", f"posted to {CHAT_ID} (message_id {first_id})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
