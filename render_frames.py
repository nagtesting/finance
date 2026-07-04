"""
Frame renderer for MoneyVeda Market Pulse video shorts.

Produces 1080x1920 PNG frames matching the moneyveda.org editorial aesthetic:
- Dark background (#0A0A0F base) with subtle gold radial gradient (top-left)
- Playfair Display for titles (display/editorial)
- DM Sans for body (refined sans)
- DM Mono for eyebrows, slot labels, footer URL (precise/technical)
- Gold (#C9A84C) accents, cream (#F5F0E8) primary text, muted (#9090A8) secondary
- Decorative gold hairlines top + bottom with faded ends
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ─────────────────────────────────────────────────────────────────────────────
# Design tokens — mirror the website's CSS variables
# ─────────────────────────────────────────────────────────────────────────────
W, H = 1080, 1920

COL_DARK       = (10, 10, 15)
COL_DARK2      = (17, 17, 24)
COL_GOLD       = (201, 168, 76)
COL_GOLD_LIGHT = (232, 201, 122)
COL_CREAM      = (245, 240, 232)
COL_CREAM_DIM  = (216, 210, 197)
COL_MUTED      = (144, 144, 168)
COL_MUTED_SOFT = (110, 110, 128)
COL_GREEN      = (74, 222, 128)
COL_RED        = (248, 113, 113)

FONTS_DIR = Path(__file__).parent / "fonts"

# Side margin & safe zones (YouTube Shorts UI overlays bottom ~250px and right ~150px,
# so we keep all critical content inside a generous safe area)
MARGIN_X      = 80
SAFE_TOP      = 180
SAFE_BOTTOM   = H - 280   # leave space for YT Shorts UI overlay
CONTENT_W     = W - 2 * MARGIN_X


# ─────────────────────────────────────────────────────────────────────────────
# Font cache (loading TTFs is expensive — cache by size)
# ─────────────────────────────────────────────────────────────────────────────
_FONT_CACHE = {}


def _font(name: str, size: int):
    key = (name, size)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    path = FONTS_DIR / name
    f = ImageFont.truetype(str(path), size=size)
    _FONT_CACHE[key] = f
    return f


def font_playfair(size: int):        return _font("PlayfairDisplay.ttf", size)
def font_playfair_italic(size: int): return _font("PlayfairDisplay-Italic.ttf", size)
def font_dmsans(size: int):          return _font("DMSans.ttf", size)
def font_dmmono(size: int):          return _font("DMMono-Medium.ttf", size)


# ─────────────────────────────────────────────────────────────────────────────
# Background — dark base with soft gold radial glow (top-left) + secondary glow
# (right side, very subtle). Same effect as the website's body background.
# ─────────────────────────────────────────────────────────────────────────────
def _build_background() -> Image.Image:
    """Compose the canvas background. Cached per-process so we don't re-render
    the gradient for every frame (it's identical across all slides)."""
    bg = Image.new("RGB", (W, H), COL_DARK)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Primary glow — top-left, gold (warm editorial atmosphere)
    cx, cy, r_max = int(W * 0.2), int(H * 0.05), int(W * 1.1)
    for r in range(r_max, 0, -6):
        a = max(0, int(58 * (1 - r / r_max) ** 1.4))
        if a <= 0:
            continue
        draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                     fill=(201, 168, 76, a))

    # Secondary glow — bottom-right, even softer, balances the composition
    cx2, cy2, r_max2 = int(W * 0.95), int(H * 0.95), int(W * 0.9)
    for r in range(r_max2, 0, -8):
        a = max(0, int(28 * (1 - r / r_max2) ** 1.6))
        if a <= 0:
            continue
        draw.ellipse([cx2 - r, cy2 - r, cx2 + r, cy2 + r],
                     fill=(201, 168, 76, a))

    # Heavy blur to dissolve any banding into a smooth ambient wash
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=40))
    bg.paste(overlay, (0, 0), overlay)
    return bg


_BG_CACHE = None


def background() -> Image.Image:
    global _BG_CACHE
    if _BG_CACHE is None:
        _BG_CACHE = _build_background()
    return _BG_CACHE.copy()


# ─────────────────────────────────────────────────────────────────────────────
# Decorative gold hairlines (top + bottom) with faded ends — matches the
# `.gold-rule` element on the website (linear-gradient transparent→gold→transparent).
# ─────────────────────────────────────────────────────────────────────────────
def _draw_hairline(img: Image.Image, y: int, max_alpha: int = 230):
    line_w = int(W * 0.72)
    x0 = (W - line_w) // 2
    # Use a 6px-tall overlay so the line has visible weight (3px stroke)
    overlay = Image.new("RGBA", (W, 6), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for i in range(line_w):
        t = i / line_w
        env = 1 - abs(2 * t - 1)
        a = int(env * max_alpha)
        od.rectangle([(x0 + i, 2), (x0 + i, 4)], fill=(*COL_GOLD, a))
    img.paste(overlay, (0, y - 3), overlay)


# ─────────────────────────────────────────────────────────────────────────────
# Text helpers — wrapping, measurement
# ─────────────────────────────────────────────────────────────────────────────
def _measure(draw: ImageDraw.ImageDraw, txt: str, font) -> tuple:
    """Return (width, height) of a string."""
    bbox = draw.textbbox((0, 0), txt, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_w: int) -> list:
    """Greedy word-wrap. Returns list of lines."""
    words = text.split()
    if not words:
        return []
    lines, cur = [], words[0]
    for word in words[1:]:
        candidate = cur + " " + word
        w, _ = _measure(draw, candidate, font)
        if w <= max_w:
            cur = candidate
        else:
            lines.append(cur)
            cur = word
    lines.append(cur)
    return lines


def _draw_letter_spaced(draw: ImageDraw.ImageDraw, xy, text, font, fill, spacing: int):
    """Draw text with extra letter-spacing (PIL has no built-in tracking)."""
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        w, _ = _measure(draw, ch, font)
        x += w + spacing


# ─────────────────────────────────────────────────────────────────────────────
# Universal frame chrome — gold hairlines top + bottom, brand footer
# ─────────────────────────────────────────────────────────────────────────────
def _draw_chrome(img: Image.Image, slot_label: str, slide_idx: int, slide_total: int):
    d = ImageDraw.Draw(img)

    # Top hairline
    _draw_hairline(img, 110)

    # Top eyebrow row: slot label (gold, mono) + slide counter (muted, mono)
    eyebrow_f = font_dmmono(26)
    slot_disp = slot_label.upper()
    _draw_letter_spaced(d, (MARGIN_X, 70), slot_disp, eyebrow_f, COL_GOLD, spacing=4)

    counter = f"{slide_idx + 1:02d} / {slide_total:02d}"
    cw, _ = _measure(d, counter, eyebrow_f)
    d.text((W - MARGIN_X - cw, 70), counter, font=eyebrow_f, fill=COL_MUTED)

    # Bottom hairline
    _draw_hairline(img, H - 200)

    # Brand footer — MONEYVEDA wordmark (Playfair) + URL (DM Mono)
    # URL is bumped to gold-light + larger so it reads clearly during scroll
    brand_f = font_playfair(40)
    url_f = font_dmmono(26)
    bx = MARGIN_X
    by = H - 135
    d.text((bx, by), "MONEY", font=brand_f, fill=COL_CREAM)
    money_w, _ = _measure(d, "MONEY", brand_f)
    d.text((bx + money_w, by), "VEDA", font=brand_f, fill=COL_GOLD)

    # URL bottom-right — promoted from muted to gold-light for visibility
    url = "moneyveda.org"
    uw, _ = _measure(d, url, url_f)
    d.text((W - MARGIN_X - uw, H - 125), url, font=url_f, fill=COL_GOLD_LIGHT)


# ─────────────────────────────────────────────────────────────────────────────
# Decorative side accent — a faint vertical gold tick on the right edge.
# Reads as a typographic ornament; matches the "editorial" tone.
# ─────────────────────────────────────────────────────────────────────────────
def _draw_side_accent(img: Image.Image, y: int, h: int = 80):
    overlay = Image.new("RGBA", (4, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for i in range(h):
        t = i / h
        env = 1 - abs(2 * t - 1)
        a = int(env * 200)
        od.rectangle([(0, i), (3, i + 1)], fill=(*COL_GOLD, a))
    img.paste(overlay, (W - 50, y), overlay)


# ─────────────────────────────────────────────────────────────────────────────
# Slide types — each measures its total content height first, then centers
# the block vertically in the available safe zone for a balanced layout
# ─────────────────────────────────────────────────────────────────────────────
SAFE_AREA_TOP    = 220     # below top hairline + eyebrow row
SAFE_AREA_BOTTOM = H - 280 # above bottom hairline + brand footer


def _vcenter_start(content_height: int) -> int:
    """Return the Y at which to start drawing a block of `content_height`
    so it ends up vertically centered in the safe area."""
    available = SAFE_AREA_BOTTOM - SAFE_AREA_TOP
    return SAFE_AREA_TOP + max(0, (available - content_height) // 2)


def render_cover(slot_label: str, date_label: str, headline: str,
                 slide_idx: int, slide_total: int) -> Image.Image:
    """Cover slide — large Playfair title, date, slot context."""
    img = background()
    d = ImageDraw.Draw(img)
    _draw_chrome(img, slot_label, slide_idx, slide_total)

    # Pre-measure to find a title size that fits ≤3 lines
    for size in (138, 124, 110, 96, 86):
        title_f = font_playfair(size)
        lines = _wrap(d, headline, title_f, CONTENT_W)
        if len(lines) <= 3:
            break
    line_h = int(size * 1.08)

    # Total block: date eyebrow (28+50 gap) + title lines + tagline (50 gap + 56)
    date_h = 28 + 50
    title_h = len(lines) * line_h
    tagline_h = 50 + 56
    block_h = date_h + title_h + tagline_h

    y = _vcenter_start(block_h)

    # Date eyebrow
    date_f = font_dmmono(28)
    _draw_letter_spaced(d, (MARGIN_X, y), date_label.upper(), date_f, COL_GOLD, spacing=5)
    y += date_h

    # Title lines
    for line in lines:
        d.text((MARGIN_X, y), line, font=title_f, fill=COL_CREAM)
        y += line_h

    # Tagline (Playfair italic, gold-light)
    tag_f = font_playfair_italic(50)
    d.text((MARGIN_X, y + 30), "Market Pulse", font=tag_f, fill=COL_GOLD_LIGHT)

    # Side accent
    _draw_side_accent(img, _vcenter_start(160), h=160)

    return img


def render_section(slot_label: str, eyebrow: str, body: str,
                   slide_idx: int, slide_total: int,
                   accent_value: str = None,
                   accent_change: str = None) -> Image.Image:
    """Standard content slide — eyebrow + body text. Optional accent value
    (e.g. an index level + change pct) shown above the body."""
    img = background()
    d = ImageDraw.Draw(img)
    _draw_chrome(img, slot_label, slide_idx, slide_total)

    # Pre-measure all elements
    eb_h = 32 + 50  # eyebrow + gap
    accent_h = 170 if accent_value else 0

    for size in (60, 56, 52, 48, 44):
        body_f = font_dmsans(size)
        lines = _wrap(d, body, body_f, CONTENT_W)
        line_h = int(size * 1.45)
        body_h_test = len(lines) * line_h
        if eb_h + accent_h + body_h_test <= (SAFE_AREA_BOTTOM - SAFE_AREA_TOP):
            break

    body_h = len(lines) * line_h
    block_h = eb_h + accent_h + body_h

    y = _vcenter_start(block_h)

    # Eyebrow
    eb_f = font_dmmono(32)
    _draw_letter_spaced(d, (MARGIN_X, y), eyebrow.upper(), eb_f, COL_GOLD, spacing=6)
    y += eb_h

    # Accent value
    if accent_value:
        val_f = font_playfair(110)
        d.text((MARGIN_X, y), accent_value, font=val_f, fill=COL_CREAM)
        if accent_change:
            vw, _ = _measure(d, accent_value, val_f)
            change_f = font_dmmono(54)
            chg_color = COL_GREEN if accent_change.startswith("+") else COL_RED
            d.text((MARGIN_X + vw + 28, y + 36), accent_change, font=change_f, fill=chg_color)
        y += accent_h

    # Body
    for line in lines:
        d.text((MARGIN_X, y), line, font=body_f, fill=COL_CREAM_DIM)
        y += line_h

    _draw_side_accent(img, _vcenter_start(160), h=160)
    return img


def render_bullets(slot_label: str, eyebrow: str, bullets: list,
                   slide_idx: int, slide_total: int) -> Image.Image:
    """Slide with a list of short bullets (e.g. catalysts). Each bullet is
    a {label, detail} dict — label in cream Playfair, detail in muted DM Sans."""
    img = background()
    d = ImageDraw.Draw(img)
    _draw_chrome(img, slot_label, slide_idx, slide_total)

    eb_h = 32 + 50
    label_f  = font_playfair(54)
    detail_f = font_dmsans(36)
    bullet_gap = 56
    label_lh = int(54 * 1.15)
    detail_lh = int(36 * 1.4)

    # Pre-measure all bullets to compute total block height
    bullet_blocks = []
    for b in bullets:
        ll = _wrap(d, b["label"], label_f, CONTENT_W - 50)
        dl = _wrap(d, b.get("detail", ""), detail_f, CONTENT_W - 50) if b.get("detail") else []
        h = len(ll) * label_lh + (len(dl) * detail_lh if dl else 0)
        bullet_blocks.append((ll, dl, h))

    bullets_h = sum(b[2] for b in bullet_blocks) + bullet_gap * (len(bullet_blocks) - 1)
    block_h = eb_h + bullets_h

    y = _vcenter_start(block_h)

    # Eyebrow
    eb_f = font_dmmono(32)
    _draw_letter_spaced(d, (MARGIN_X, y), eyebrow.upper(), eb_f, COL_GOLD, spacing=6)
    y += eb_h

    # Bullets
    for ll, dl, _ in bullet_blocks:
        # Gold bullet dot
        d.ellipse([MARGIN_X, y + 28, MARGIN_X + 16, y + 44], fill=COL_GOLD)
        label_x = MARGIN_X + 44

        for line in ll:
            d.text((label_x, y), line, font=label_f, fill=COL_CREAM)
            y += label_lh

        for line in dl:
            d.text((label_x, y), line, font=detail_f, fill=COL_CREAM_DIM)
            y += detail_lh

        y += bullet_gap

    _draw_side_accent(img, _vcenter_start(160), h=160)
    return img


def _make_qr_code(url: str, size_px: int = 280) -> Image.Image:
    """Render a QR code as gold-on-dark, sized to size_px on the long edge.
    Uses ERROR_CORRECT_M (~15% redundancy) — enough to scan reliably even if
    a phone screen has glare or motion blur during a Short loop."""
    import qrcode
    from qrcode.constants import ERROR_CORRECT_M
    qr = qrcode.QRCode(version=None, error_correction=ERROR_CORRECT_M,
                       box_size=10, border=2)
    qr.add_data(url); qr.make(fit=True)
    img = qr.make_image(fill_color=COL_GOLD_LIGHT,
                        back_color=COL_DARK2).convert("RGB")
    img = img.resize((size_px, size_px), Image.Resampling.LANCZOS)
    return img


def render_outro(slot_label: str, tagline: str,
                 slide_idx: int, slide_total: int,
                 qr_url: str = "https://www.moneyveda.org/") -> Image.Image:
    """Outro — centered Playfair italic tagline + QR code + CTA + URL + disclaimer."""
    img = background()
    d = ImageDraw.Draw(img)
    _draw_chrome(img, slot_label, slide_idx, slide_total)

    for size in (96, 84, 72, 64):
        tag_f = font_playfair_italic(size)
        lines = _wrap(d, tagline, tag_f, CONTENT_W)
        if len(lines) <= 3:
            break

    line_h = int(size * 1.12)
    tagline_h = len(lines) * line_h

    qr_size = 280
    qr_gap_above = 60
    qr_caption_h = 40 + 20  # "Scan to read full briefing" caption
    url_h = 50 + 30
    disc_h = 30

    block_h = tagline_h + qr_gap_above + qr_size + qr_caption_h + url_h + disc_h
    y = _vcenter_start(block_h)

    # Italic tagline
    for line in lines:
        w, _ = _measure(d, line, tag_f)
        x = (W - w) // 2
        d.text((x, y), line, font=tag_f, fill=COL_CREAM)
        y += line_h

    # Underline accent below tagline
    accent_w = 140
    ax = (W - accent_w) // 2
    d.line([(ax, y + 18), (ax + accent_w, y + 18)], fill=COL_GOLD, width=3)
    y += qr_gap_above

    # QR code — centered, gold on dark background, scans to moneyveda.org
    qr_img = _make_qr_code(qr_url, size_px=qr_size)
    qr_x = (W - qr_size) // 2
    # Soft outline around the QR for visual containment
    pad = 14
    d.rounded_rectangle(
        [qr_x - pad, y - pad, qr_x + qr_size + pad, y + qr_size + pad],
        radius=18, outline=COL_GOLD, width=2,
    )
    img.paste(qr_img, (qr_x, y))
    y += qr_size + 10

    # QR caption
    cap_f = font_dmsans(28)
    cap = "Scan to read the full briefing"
    cw, _ = _measure(d, cap, cap_f)
    d.text(((W - cw) // 2, y + 8), cap, font=cap_f, fill=COL_GOLD_LIGHT)
    y += qr_caption_h

    # URL — DM Mono, prominent
    url_f = font_dmmono(44)
    url_text = "moneyveda.org"
    uw, _ = _measure(d, url_text, url_f)
    d.text(((W - uw) // 2, y), url_text, font=url_f, fill=COL_CREAM)
    y += url_h

    # Disclaimer
    disc_f = font_dmsans(22)
    disc = "Educational only · Not SEBI-registered investment advice"
    dw, _ = _measure(d, disc, disc_f)
    d.text(((W - dw) // 2, y), disc, font=disc_f, fill=COL_MUTED)

    return img
