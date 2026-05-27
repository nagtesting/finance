"""
video_publisher.py  ─  MoneyVeda Market Pulse video Shorts (v1.0)
====================================================================
Generates a 60-second vertical (1080x1920) video Short from a
just-saved pre-market or post-market commentary. Designed to bolt onto
the existing market_commentary.py cron — same Render dyno, no extra
service.

PIPELINE:
  1. Read the latest commentary for (today, mode) from Supabase
  2. Ask Gemini Flash-Lite to compress it into a 6-slide JSON script
     (cover + 4 content slides + outro). Cheap, ~$0.0001/call.
  3. Render each slide as a 1080x1920 PNG via render_frames module
  4. Stitch with ffmpeg — crossfades + bundled royalty-free MP3
     (looped/trimmed to ~57s) — output H.264 yuv420p MP4
  5. Upload to Vercel Blob storage at videos/{date}/{mode}.mp4
  6. Insert/upsert a row in `market_videos` for the moneyveda.org
     download page to find it

INVOCATION:
  Called from market_commentary.py AFTER a successful save:

      from video_publisher import publish_video
      try:
          publish_video(mode="pre", date_str="2026-05-21")
      except Exception as e:
          _log("⚠️", f"Video pipeline failed (non-fatal): {e}")

  Also runnable standalone for testing:

      python video_publisher.py --mode pre
      python video_publisher.py --mode post --date 2026-05-21
      python video_publisher.py --mode pre --dry-run    # build but don't upload

ENV VARS REQUIRED (in addition to the ones market_commentary.py already needs):
  BLOB_READ_WRITE_TOKEN  — Vercel Blob read-write token (create the store in
                           Vercel dashboard, it auto-adds this env var to the
                           project; then set it on the Render service too)
  PUBLIC_SITE_URL        — optional, defaults to https://www.moneyveda.org

FAILURE PHILOSOPHY:
  This module NEVER raises into the caller's success path. Every error is
  logged and swallowed so a video-pipeline issue can't break the commentary
  save the user paid Gemini to generate. The caller wraps the entry point
  in try/except as a second defence.

DEPENDENCIES (add to requirements.txt):
  Pillow>=10.0.0
  qrcode>=7.4
  vercel_blob>=0.4.0
  (Pillow, requests, supabase, google-generativeai, python-dotenv already
   present from market_commentary.py)

RENDER DEPLOYMENT:
  - ffmpeg must be available. The default Render Python runtime image
    ships with it. Verify with `which ffmpeg` in a shell session.
  - Bundle ./fonts/*.ttf in the repo (committed). ~870 KB total, fine.
  - Bundle ./music/track.mp3 (you download once from YouTube Audio
    Library, commit, never touch again). The pipeline picks the first
    MP3 it finds in ./music/.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv
from supabase import create_client

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    import vercel_blob
    VERCEL_BLOB_AVAILABLE = True
except ImportError:
    VERCEL_BLOB_AVAILABLE = False

from render_frames import (
    render_cover, render_section, render_bullets, render_outro,
)

load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────────────
SUPABASE_URL          = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY   = os.getenv("SUPABASE_SECRET_KEY")
GEMINI_API_KEY        = os.getenv("GEMINI_API_KEY")
BLOB_READ_WRITE_TOKEN = os.getenv("BLOB_READ_WRITE_TOKEN")
PUBLIC_SITE_URL       = os.getenv("PUBLIC_SITE_URL", "https://www.moneyveda.org")

GEMINI_MODEL = "gemini-2.5-flash-lite"  # cheap, fast — perfect for script extraction

IST = timezone(timedelta(hours=5, minutes=30))

# Retention: keep this many TRADING days of videos. Older ones are deleted
# from Vercel Blob + the market_videos table on each publish run.
# Trading days = Mon-Fri only, so a setting of 4 means today + previous 3
# trading days survive (Friday's videos remain accessible through Wednesday).
RETENTION_TRADING_DAYS = 4

BASE_DIR  = Path(__file__).parent
MUSIC_DIR = BASE_DIR / "music"
FONTS_DIR = BASE_DIR / "fonts"

# Slide timing — six slides, ~9.5s each = 57s with 0.5s crossfades
SLIDE_DURATIONS = [9.0, 10.0, 11.0, 10.0, 11.0, 9.0]   # cover, sec, bul, sec, bul, outro
CROSSFADE_S     = 0.5

supabase = None
if SUPABASE_URL and SUPABASE_SECRET_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)


def _log(emoji: str, msg: str) -> None:
    print(f"{emoji}  [video][{datetime.now(IST).strftime('%H:%M:%S')}]  {msg}")


# ═════════════════════════════════════════════════════════════════════════════
# 1) Read the latest commentary for (date, mode) from Supabase
# ═════════════════════════════════════════════════════════════════════════════
def _fetch_commentary(mode: str, date_str: str) -> dict | None:
    """Return the most recent saved commentary row for (mode, date)."""
    if not supabase:
        raise RuntimeError("Supabase client not configured (missing env vars)")
    res = (
        supabase.table("market_commentary")
        .select("commentary_text, slot_time, source, data_snapshot")
        .eq("commentary_type", mode)
        .eq("commentary_date", date_str)
        .order("slot_time", desc=True)
        .limit(1)
        .execute()
    )
    if not res.data:
        return None
    return res.data[0]


# ═════════════════════════════════════════════════════════════════════════════
# 2) Compress full commentary into a 6-slide video script via Gemini
# ═════════════════════════════════════════════════════════════════════════════
SCRIPT_PROMPT = """You are converting a long-form market commentary into a 6-slide video script for an Indian retail-investor audience. Output STRICT JSON only — no markdown fences, no preamble.

The video is a 60-second vertical Short. Six slides. Total reading budget is tight — every line must earn its place.

EXPECTED JSON SHAPE (output exactly this structure — `headline` and `tagline` are top-level fields; the `slides` array contains EXACTLY the 4 MIDDLE slides, NOT the cover or outro):

{
  "headline":   "<cover headline — 5-9 words>",
  "slides": [
    { "kind": "section", "eyebrow": "Setup",                       "accent_value": "<Nifty level>", "accent_change": "<+/-pct>", "body": "<22-28 words>" },
    { "kind": "bullets", "eyebrow": "<Catalysts label>",           "bullets": [ {"label": "<5-7 words>", "detail": "<6-10 words>"}, {"label": "...", "detail": "..."}, {"label": "...", "detail": "..."} ] },
    { "kind": "section", "eyebrow": "<Technical Position/Read>",   "body": "<22-28 words>" },
    { "kind": "bullets", "eyebrow": "<Themes/Highlights label>",   "bullets": [ {"label": "...", "detail": "..."}, {"label": "...", "detail": "..."}, {"label": "...", "detail": "..."} ] }
  ],
  "tagline":    "<outro tagline — 6-10 words in Playfair italic voice>"
}

The commentary is provided below. Extract the most important content and structure it as follows:

COVER (top-level "headline" field, NOT inside slides[]):
   - A 5-9 word hook capturing the day's central thesis. No filler.
   - Example: "Defending 24,200 — banks hold the line."

SLIDE 1 of slides[] — SECTION (Setup — where we are right now):
   - "kind": "section"
   - "eyebrow": "Setup" (literal, do not change)
   - "accent_value": Nifty 50 level (e.g. "24,247")
   - "accent_change": Nifty 50 % change with sign (e.g. "-0.34%" or "+1.20%")
   - "body": 22-28 words on the dominant setup / context

SLIDE 2 of slides[] — BULLETS (3 key drivers / catalysts):
   - "kind": "bullets"
   - "eyebrow": "Overnight Catalysts" for pre-market, "Today's Catalysts" for post-market
   - "bullets": array of EXACTLY 3 items, each {"label": "<5-7 words>", "detail": "<6-10 word context>"}
   - Examples of good labels: "GIFT Nifty -0.4%", "FII -₹2,140 cr · DII +₹3,890 cr", "Brent +1.8%, DXY 104.6"

SLIDE 3 of slides[] — SECTION (Technical Position or Technical Read):
   - "kind": "section"
   - "eyebrow": "Technical Position" for pre-market, "Technical Read" for post-market
   - "body": 22-28 words on key levels / MAs / VIX

SLIDE 4 of slides[] — BULLETS (Themes / Sector highlights):
   - "kind": "bullets"
   - "eyebrow": "Themes to Watch" for pre-market, "Sector Highlights" for post-market
   - "bullets": array of EXACTLY 3 items, each {"label": "<5-7 words>", "detail": "<6-10 word context>"}

OUTRO (top-level "tagline" field, NOT inside slides[]):
   - Punchy 6-10 word takeaway in Playfair italic voice. Examples:
     "Defend the support · let the breadth lead."
     "Banks led · IT lagged · breadth confirmed."
     "Domestic absorption holds · global cues still soft."

RULES:
- Use exact figures from the commentary — never invent numbers, levels, or news.
- If the commentary explicitly says no catalyst was found for a move, reflect that honestly (label: "Cause unclear", detail: "no specific driver in available news").
- No buy/sell advice. No hype words ("explosive", "huge", "must-buy").
- Use Rs. or ₹ for currency consistently.
- Short, sharp, financial-press tone.
- OUTPUT MUST BE VALID JSON. No trailing commas, no comments, no markdown.

COMMENTARY MODE: __MODE__
COMMENTARY DATE: __DATE__

FULL COMMENTARY:
__COMMENTARY__

Output the JSON now:"""


def _generate_script(mode: str, date_str: str, commentary_text: str) -> dict:
    """Call Gemini to compress the commentary into the 6-slide structure.
    Returns a dict with `headline`, `slides` (list), `tagline`."""
    if not GEMINI_AVAILABLE or not GEMINI_API_KEY:
        raise RuntimeError("Gemini not configured — cannot generate video script")

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)

    # CRITICAL: do NOT use str.format() here. The prompt template contains
    # literal JSON examples with `{"label": ...}` curly braces, which
    # str.format() interprets as placeholders and crashes with
    # KeyError: '"label"'. Use plain .replace() against unique sentinels
    # that never appear elsewhere in the template.
    prompt = (SCRIPT_PROMPT
              .replace("__MODE__", mode)
              .replace("__DATE__", date_str)
              .replace("__COMMENTARY__", commentary_text))

    _log("🧠", f"Calling Gemini ({GEMINI_MODEL}) for slide extraction…")
    resp = model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.3,           # lower than commentary — we want deterministic structure
            "max_output_tokens": 1500,
            "response_mime_type": "application/json",
        },
        request_options={"timeout": 45},
    )

    if not resp or not resp.text:
        raise RuntimeError("Gemini returned empty script response")

    raw = resp.text.strip()
    # Strip markdown fences just in case (response_mime_type usually prevents them)
    if raw.startswith("```"):
        raw = raw.split("```")[1] if "```" in raw[3:] else raw[3:]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        _log("⚠️", f"JSON parse failed: {e}. First 500 chars:\n{raw[:500]}")
        raise


# ═════════════════════════════════════════════════════════════════════════════
# 3) Render frames using render_frames module
# ═════════════════════════════════════════════════════════════════════════════
def _normalize_script(script: dict) -> dict:
    """Normalize Gemini's response shape into the canonical form we render
    from: a dict with `headline`, `tagline`, and `slides` (a list of EXACTLY
    4 middle slides, no cover, no outro).

    Gemini sometimes returns the 4 middle slides in `slides[]` (the shape
    documented in the prompt's JSON schema), and sometimes returns all 6
    slides including cover & outro inside `slides[]` (because the prompt
    described "6 slides" numerically). Both shapes are valid interpretations
    of the instructions, so this function accepts both and converts to the
    canonical form rather than fighting the model. Returns a shallow copy
    so the caller can keep using `script` for top-level fields it added."""
    s = dict(script or {})
    slides = list(s.get("slides") or [])

    # Detect cover / outro entries by their distinctive keys, regardless of
    # position. A 'cover' slide has 'headline' (the only one that does);
    # an 'outro' slide has 'tagline'.
    cover_idx  = next((i for i, sl in enumerate(slides) if isinstance(sl, dict) and "headline" in sl), None)
    outro_idx  = next((i for i, sl in enumerate(slides) if isinstance(sl, dict) and "tagline"  in sl), None)

    if cover_idx is not None and not s.get("headline"):
        s["headline"] = slides[cover_idx].get("headline") or "Today's Market Pulse"
    if outro_idx is not None and not s.get("tagline"):
        s["tagline"] = slides[outro_idx].get("tagline") or "Read the full briefing on moneyveda.org"

    # Strip cover / outro entries from the middle-slide list
    middle = [sl for i, sl in enumerate(slides)
              if i != cover_idx and i != outro_idx]
    s["slides"] = middle
    return s


def _render_all_frames(script: dict, slot_label: str, date_label: str,
                       frames_dir: Path) -> list[Path]:
    frames_dir.mkdir(parents=True, exist_ok=True)
    script = _normalize_script(script)
    slides_data = script.get("slides", [])
    if len(slides_data) != 4:
        # Helpful diagnostic — show what we actually got so debugging is
        # easier when Gemini occasionally returns an off-count list.
        kinds = [sl.get("eyebrow") or list(sl.keys())[:3] for sl in slides_data
                 if isinstance(sl, dict)]
        raise ValueError(
            f"Expected 4 middle slides after normalization, got "
            f"{len(slides_data)}. Slide shapes: {kinds}"
        )

    total = 6
    paths = []

    # Slide 1 — Cover
    img = render_cover(
        slot_label=slot_label,
        date_label=date_label,
        headline=script.get("headline", "Today's Market Pulse"),
        slide_idx=0, slide_total=total,
    )
    p = frames_dir / "slide_00.png"; img.save(p, "PNG", optimize=True); paths.append(p)

    # Slides 2-5 — middle content
    for i, s in enumerate(slides_data, start=1):
        kind = s.get("kind") or (
            "bullets" if "bullets" in s else "section"
        )
        if kind == "section":
            img = render_section(
                slot_label=slot_label,
                eyebrow=s["eyebrow"],
                body=s["body"],
                slide_idx=i, slide_total=total,
                accent_value=s.get("accent_value"),
                accent_change=s.get("accent_change"),
            )
        elif kind == "bullets":
            img = render_bullets(
                slot_label=slot_label,
                eyebrow=s["eyebrow"],
                bullets=s["bullets"],
                slide_idx=i, slide_total=total,
            )
        else:
            raise ValueError(f"Unknown slide kind: {kind}")
        p = frames_dir / f"slide_{i:02d}.png"
        img.save(p, "PNG", optimize=True)
        paths.append(p)

    # Slide 6 — Outro with QR code → market-pulse.html
    qr_target = f"{PUBLIC_SITE_URL.rstrip('/')}/market-pulse.html"
    img = render_outro(
        slot_label=slot_label,
        tagline=script.get("tagline", "Read the full briefing on moneyveda.org"),
        slide_idx=5, slide_total=total,
        qr_url=qr_target,
    )
    p = frames_dir / "slide_05.png"; img.save(p, "PNG", optimize=True); paths.append(p)

    return paths


# ═════════════════════════════════════════════════════════════════════════════
# 4) Stitch with ffmpeg
# ═════════════════════════════════════════════════════════════════════════════
def _find_music_track() -> Path | None:
    """Pick the first .mp3 in ./music/. Returns None if no track is bundled —
    in that case ffmpeg uses synthesized silence and the user knows to add one."""
    if not MUSIC_DIR.exists():
        return None
    candidates = sorted(MUSIC_DIR.glob("*.mp3")) + sorted(MUSIC_DIR.glob("*.m4a")) + sorted(MUSIC_DIR.glob("*.wav"))
    return candidates[0] if candidates else None


def _stitch_video(frame_paths: list[Path], durations: list[float],
                  output_path: Path) -> None:
    total_duration = sum(durations) - CROSSFADE_S * (len(frame_paths) - 1)
    music_track = _find_music_track()

    # Build inputs: one looped PNG per slide
    inputs = []
    for p, dur in zip(frame_paths, durations):
        inputs += ["-loop", "1", "-t", f"{dur}", "-i", str(p)]

    # Video filter: full 1080×1920 output. GitHub Actions runners have 7GB
    # RAM so memory is not a constraint; we use the original sharp resolution.
    # (Earlier 720×1280 + ultrafast preset was a workaround for Render
    # Starter's 512MB ceiling — no longer needed on GitHub Actions.)
    OUT_W, OUT_H = 1080, 1920
    filter_parts = []
    for i in range(len(frame_paths)):
        filter_parts.append(
            f"[{i}:v]format=yuv420p,fps=30,scale={OUT_W}:{OUT_H},setsar=1[v{i}]"
        )
    running_offset = durations[0] - CROSSFADE_S
    chain = "[v0]"
    for i in range(1, len(frame_paths)):
        out_label = f"[vx{i}]" if i < len(frame_paths) - 1 else "[vout]"
        filter_parts.append(
            f"{chain}[v{i}]xfade=transition=fade:duration={CROSSFADE_S}:"
            f"offset={running_offset:.3f}{out_label}"
        )
        chain = out_label
        if i < len(frame_paths) - 1:
            running_offset += durations[i] - CROSSFADE_S

    cmd = ["ffmpeg", "-y", *inputs]

    if music_track:
        # Real music — input it, loop+trim to total duration, fade in/out at edges
        n_inputs = len(frame_paths)
        music_idx = n_inputs
        cmd += ["-stream_loop", "-1", "-i", str(music_track)]
        audio_filter = (
            f"[{music_idx}:a]atrim=0:{total_duration},"
            f"asetpts=PTS-STARTPTS,"
            f"afade=t=in:st=0:d=1.5,"
            f"afade=t=out:st={total_duration-2}:d=2,"
            f"volume=0.5,"
            f"aformat=channel_layouts=stereo[aout]"
        )
        filter_complex = ";".join(filter_parts) + ";" + audio_filter
        _log("🎵", f"Using music: {music_track.name}")
    else:
        # No music bundled — synthesize a soft ambient pad as placeholder
        audio_filter = (
            f"sine=frequency=146.83:duration={total_duration},"
            f"volume=0.04,"
            f"afade=t=in:st=0:d=1.5,"
            f"afade=t=out:st={total_duration-2}:d=2,"
            f"aformat=channel_layouts=stereo[aout]"
        )
        filter_complex = ";".join(filter_parts) + ";" + audio_filter
        cmd += ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"]
        _log("⚠️", "No music track in ./music/ — using synthesized placeholder pad")

    cmd += [
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-map", "[aout]",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        # Quality settings — GitHub Actions has 7GB RAM so we can afford
        # 'medium' preset which encodes more efficiently (better file size
        # for the same visual quality).
        "-preset", "medium",
        "-crf", "20",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        "-movflags", "+faststart",
        str(output_path),
    ]

    _log("🎬", f"Stitching {total_duration:.1f}s video…")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        _log("❌", "ffmpeg failed. Last 40 lines of stderr:")
        for line in result.stderr.splitlines()[-40:]:
            _log("   ", line)
        raise RuntimeError(f"ffmpeg exit code {result.returncode}")
    size_mb = output_path.stat().st_size / 1024 / 1024
    _log("✅", f"Video stitched: {output_path.name} ({size_mb:.2f} MB)")


# ═════════════════════════════════════════════════════════════════════════════
# 5) Upload to Vercel Blob
# ═════════════════════════════════════════════════════════════════════════════
def _upload_to_vercel_blob(local_path: Path, blob_path: str) -> dict:
    """Upload an MP4 to Vercel Blob. Returns {url, downloadUrl, pathname, ...}."""
    if not VERCEL_BLOB_AVAILABLE:
        raise RuntimeError("vercel_blob package not installed (pip install vercel_blob)")
    if not BLOB_READ_WRITE_TOKEN:
        raise RuntimeError("BLOB_READ_WRITE_TOKEN env var not set")

    # The vercel_blob package reads BLOB_READ_WRITE_TOKEN from env automatically.
    with open(local_path, "rb") as f:
        data = f.read()

    _log("☁️", f"Uploading {len(data)/1024/1024:.2f} MB to Vercel Blob as '{blob_path}'…")
    resp = vercel_blob.put(
        blob_path,
        data,
        {
            "addRandomSuffix": "false",   # we control the path; deterministic URL
            "contentType": "video/mp4",
            "cacheControlMaxAge": "604800",  # 7 days CDN cache
        },
    )
    _log("✅", f"Uploaded → {resp.get('url')}")
    return resp


# ═════════════════════════════════════════════════════════════════════════════
# 6) Record in Supabase `market_videos` table
# ═════════════════════════════════════════════════════════════════════════════
def _save_video_metadata(mode: str, date_str: str, blob_url: str,
                         download_url: str | None,
                         duration_s: float, size_bytes: int) -> bool:
    if not supabase:
        _log("⚠️", "Supabase not configured — skipping metadata save")
        return False
    try:
        supabase.table("market_videos").upsert(
            {
                "video_type":    mode,            # 'pre' | 'post'
                "video_date":    date_str,
                "video_url":     blob_url,
                "download_url":  download_url or blob_url,
                "duration_s":    round(duration_s, 1),
                "size_bytes":    size_bytes,
                "generated_at":  datetime.now(IST).isoformat(),
            },
            on_conflict="video_type,video_date",
        ).execute()
        _log("💾", f"Saved metadata for {mode} / {date_str}")
        return True
    except Exception as e:
        _log("⚠️", f"Metadata save failed: {e}")
        return False


def _trading_days_back(today: datetime, n: int) -> datetime:
    """Return the date that is `n` TRADING DAYS before `today` (skipping
    weekends). Used to compute the retention cutoff."""
    d = today
    days_counted = 0
    while days_counted < n:
        d -= timedelta(days=1)
        if d.weekday() < 5:        # Mon=0 … Fri=4, Sat=5, Sun=6
            days_counted += 1
    return d


def _cleanup_old_videos() -> None:
    """Delete videos older than RETENTION_TRADING_DAYS trading days.

    Safety design:
      1. Query Supabase for old rows FIRST (read is safe)
      2. Delete each from Vercel Blob (idempotent — Blob's del() does not
         raise if the file is already gone)
      3. Only then delete the Supabase rows, so we never end up with a
         DB row pointing at a missing Blob (orphaned URL = broken
         download button on the site)
      4. Errors during cleanup NEVER raise — this runs after a successful
         publish, and a cleanup failure must not undo that success.
    """
    if not supabase:
        return
    try:
        today = datetime.now(IST).date()
        cutoff = _trading_days_back(datetime.now(IST), RETENTION_TRADING_DAYS).date()
        # Rows with video_date STRICTLY OLDER than the cutoff (today and the
        # previous RETENTION_TRADING_DAYS-1 trading days are KEPT).
        res = (
            supabase.table("market_videos")
            .select("id, video_type, video_date, video_url")
            .lt("video_date", cutoff.isoformat())
            .execute()
        )
        old_rows = res.data or []
        if not old_rows:
            _log("🧹", f"Cleanup: no videos older than {cutoff} to remove")
            return

        _log("🧹", f"Cleanup: removing {len(old_rows)} video(s) older than "
                   f"{cutoff} ({RETENTION_TRADING_DAYS} trading days back)")

        deleted_ids = []
        for row in old_rows:
            blob_url = row.get("video_url")
            try:
                if blob_url and VERCEL_BLOB_AVAILABLE:
                    # vercel_blob.delete() accepts the full URL OR the pathname.
                    # Idempotent — if the blob is already gone, this is a no-op.
                    vercel_blob.delete(blob_url)
                    _log("   ", f"   ↳ blob deleted: {row.get('video_type')} / {row.get('video_date')}")
                deleted_ids.append(row["id"])
            except Exception as e:
                # Blob deletion failed — log but DON'T delete the DB row, so
                # we'll retry on the next publish run. A row pointing at a
                # missing blob is worse than a row that gets retried.
                _log("⚠️", f"   ↳ blob delete failed for {blob_url}: {e}")

        # Now remove DB rows for the blobs we successfully deleted
        if deleted_ids:
            try:
                supabase.table("market_videos") \
                    .delete() \
                    .in_("id", deleted_ids) \
                    .execute()
                _log("🧹", f"Cleanup: removed {len(deleted_ids)} row(s) from market_videos")
            except Exception as e:
                _log("⚠️", f"Cleanup: DB row delete failed: {e}")
    except Exception as e:
        # Catch-all so a cleanup bug can never derail the publish
        _log("⚠️", f"Cleanup failed (non-fatal): {e}")


# ═════════════════════════════════════════════════════════════════════════════
# Public entry point
# ═════════════════════════════════════════════════════════════════════════════
def publish_video(mode: str, date_str: str | None = None,
                  dry_run: bool = False) -> dict | None:
    """Build and publish a video Short for the given mode/date.

    Returns:
        {"mode", "date", "url", "size_mb", "duration_s"} on success, or
        None if no commentary was found (caller should treat as no-op).
    Raises on hard errors so the caller (market_commentary.py) can decide
    whether to retry or just log.
    """
    if mode not in ("pre", "post"):
        raise ValueError(f"Only 'pre' and 'post' are video-able, got: {mode}")

    if date_str is None:
        date_str = datetime.now(IST).strftime("%Y-%m-%d")

    _log("🚀", f"Building video for {mode.upper()} / {date_str} (dry_run={dry_run})")

    # 1. Fetch commentary
    row = _fetch_commentary(mode, date_str)
    if not row:
        _log("⚠️", f"No {mode} commentary for {date_str} — nothing to publish")
        return None
    commentary_text = row.get("commentary_text", "")
    if len(commentary_text) < 200:
        _log("⚠️", f"Commentary too short ({len(commentary_text)} chars) — skipping")
        return None

    # 2. Generate slide script
    script = _generate_script(mode, date_str, commentary_text)

    # 3. Render frames (in temp dir to avoid littering the working tree)
    with tempfile.TemporaryDirectory(prefix="mvpulse-video-") as tmp:
        tmp_dir = Path(tmp)
        frames_dir = tmp_dir / "frames"

        # Slot label + date label for the chrome
        slot_label = "Pre-Market · 08:00 IST" if mode == "pre" else "Post-Market · 17:00 IST"
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            date_label = dt.strftime("%A · %d %b %Y")
        except ValueError:
            date_label = date_str

        frame_paths = _render_all_frames(script, slot_label, date_label, frames_dir)
        _log("🖼️", f"Rendered {len(frame_paths)} slides")

        # 4. Stitch
        out_mp4 = tmp_dir / f"moneyveda-{date_str}-{mode}.mp4"
        _stitch_video(frame_paths, SLIDE_DURATIONS, out_mp4)

        size_bytes = out_mp4.stat().st_size
        duration = sum(SLIDE_DURATIONS) - CROSSFADE_S * (len(SLIDE_DURATIONS) - 1)

        if dry_run:
            # Move the file to a stable location so the user can inspect it
            preserved = BASE_DIR / "output" / f"moneyveda-{date_str}-{mode}.mp4"
            preserved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(out_mp4, preserved)
            _log("🏁", f"Dry run — preserved at {preserved}")
            return {
                "mode": mode, "date": date_str,
                "url": f"file://{preserved}",
                "size_mb": round(size_bytes / 1024 / 1024, 2),
                "duration_s": round(duration, 1),
            }

        # 5. Upload to Vercel Blob — path is deterministic so the website
        # can construct the URL even before the DB row is written.
        blob_path = f"market-pulse/{date_str}/{mode}.mp4"
        blob_resp = _upload_to_vercel_blob(out_mp4, blob_path)

        # 6. Record in Supabase
        _save_video_metadata(
            mode=mode, date_str=date_str,
            blob_url=blob_resp.get("url"),
            download_url=blob_resp.get("downloadUrl"),
            duration_s=duration, size_bytes=size_bytes,
        )

        # 7. Retention cleanup — fires AFTER today's video is safely saved
        # so a cleanup bug can never erase the video we just published.
        # Errors are swallowed inside the function (publish must remain
        # the success/failure signal for the caller).
        _cleanup_old_videos()

        return {
            "mode": mode, "date": date_str,
            "url": blob_resp.get("url"),
            "size_mb": round(size_bytes / 1024 / 1024, 2),
            "duration_s": round(duration, 1),
        }


def _detect_mode_from_ist() -> str | None:
    """Auto-detect 'pre' or 'post' from current IST time.

    The companion 'market-video' Render cron is scheduled at 08:15 and 17:15
    IST (15 min after each commentary cron), so this function maps:
       08:00 IST ± 45 min  → 'pre'
       17:00 IST ± 45 min  → 'post'
    Returns None outside those windows (manual --mode arg required)."""
    now = datetime.now(IST)
    cur_min = now.hour * 60 + now.minute
    # Pre-market band: 07:15 – 08:45 IST  (435 – 525)
    if 435 <= cur_min <= 525:
        return "pre"
    # Post-market band: 16:15 – 17:45 IST  (975 – 1065)
    if 975 <= cur_min <= 1065:
        return "post"
    return None


# ═════════════════════════════════════════════════════════════════════════════
# CLI
# ═════════════════════════════════════════════════════════════════════════════
def _main():
    parser = argparse.ArgumentParser(description="MoneyVeda Market Pulse video publisher")
    parser.add_argument("--mode", choices=["pre", "post"], default=None,
                        help="Which commentary to render (auto-detected from IST time if omitted)")
    parser.add_argument("--date", default=None,
                        help="Commentary date YYYY-MM-DD (default: today IST)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Build the video locally but do NOT upload to Vercel Blob")
    args = parser.parse_args()

    mode = args.mode
    if mode is None:
        mode = _detect_mode_from_ist()
        if mode is None:
            _log("⏭️", f"Current IST time ({datetime.now(IST).strftime('%H:%M')}) "
                       f"is outside the pre/post auto-detect windows. "
                       f"Pass --mode pre or --mode post for manual runs. Exiting cleanly.")
            sys.exit(0)
        _log("🤖", f"Auto-detected mode={mode} from current IST time")

    try:
        result = publish_video(mode=mode, date_str=args.date, dry_run=args.dry_run)
        if result:
            print(f"\n✅ DONE: {json.dumps(result, indent=2)}")
            sys.exit(0)
        sys.exit(2)  # no commentary found
    except Exception as e:
        _log("❌", f"Fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    _main()
