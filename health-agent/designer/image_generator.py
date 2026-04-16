"""
Professional Instagram image generator using Pillow.

4 post type layouts in a Magazine Editorial + Bold Data-Driven style:
  1. Stat Card    — giant stat number, gold block header, clean white bg
  2. Tip Carousel — numbered tip slides with bold headings + SWIPE cover
  3. Myth vs Fact — bold color-block headers (red myth / green fact)
  4. Quote Card   — large decorative quote mark, centered attribution

Canvas: 1080 x 1080 px
Fonts:  Poppins Bold / SemiBold / Regular (downloaded once to output/fonts/)
"""

import logging
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

import config

logger = logging.getLogger(__name__)

# ── Dimensions ────────────────────────────────────────────────────────────────
SIZE    = 1080
PAD     = 80      # left/right padding

# ── Colour palette ────────────────────────────────────────────────────────────
WHITE       = "#FFFFFF"
CREAM       = "#FDF6EC"
GOLD        = "#E8A84C"
ORANGE      = "#D4622A"
DARK        = "#1A1A1A"
MID         = "#4A4A4A"
MUTED       = "#888888"
MYTH_RED    = "#C0392B"
FACT_GREEN  = "#1E8449"
BLOCK_TEXT  = "#FFFFFF"   # white text on coloured blocks

# ── Font cache ────────────────────────────────────────────────────────────────
FONT_DIR = config.OUTPUT_DIR.parent / "fonts"

FONT_URLS = {
    "bold":     "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf",
    "semibold": "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-SemiBold.ttf",
    "regular":  "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Regular.ttf",
}


def _ensure_fonts() -> dict[str, Path]:
    FONT_DIR.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for name, url in FONT_URLS.items():
        dest = FONT_DIR / f"Poppins-{name}.ttf"
        if not dest.exists():
            logger.info("Downloading font: %s", dest.name)
            try:
                resp = requests.get(url, timeout=15)
                resp.raise_for_status()
                dest.write_bytes(resp.content)
            except Exception as exc:
                logger.warning("Font download failed (%s): %s", name, exc)
        paths[name] = dest
    return paths


def _font(paths: dict[str, Path], weight: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(str(paths[weight]), size)
    except Exception:
        return ImageFont.load_default()


def _wrap(text: str, font: ImageFont.FreeTypeFont, max_w: int, draw: ImageDraw.ImageDraw) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur = ""
    for word in words:
        test = f"{cur} {word}".strip()
        if draw.textbbox((0, 0), test, font=font)[2] <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def _draw_lines(draw, lines, font, x, y, fill, align="left", max_w=None, line_gap=14):
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        lw = bbox[2] - bbox[0]
        lh = bbox[3] - bbox[1]
        if align == "center" and max_w:
            lx = x + (max_w - lw) // 2
        else:
            lx = x
        draw.text((lx, y), line, font=font, fill=fill)
        y += lh + line_gap
    return y


def _block_height(lines, font, draw, gap=14):
    total = 0
    for line in lines:
        b = draw.textbbox((0, 0), line, font=font)
        total += (b[3] - b[1]) + gap
    return total - gap if total else 0


def _thin_bar(draw, y, color=GOLD, height=12):
    draw.rectangle([0, y, SIZE, y + height], fill=color)


def _brand_handle(draw, fonts, handle):
    font = _font(fonts, "regular", 32)
    text = handle if handle.startswith("@") else f"@{handle}"
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    x = (SIZE - w) // 2
    y = SIZE - 12 - 52
    draw.text((x, y), text, font=font, fill=MUTED)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. STAT CARD
# ═══════════════════════════════════════════════════════════════════════════════

def generate_stat_card(
    stat_number: str,
    stat_label: str,
    stat_context: str,
    stat_source: str,
    brand_handle: str,
    output_path: Path,
) -> Path:
    """
    Layout:
      [80px gold top block]
      huge bold stat number (centred)
      ── gold divider ──
      stat label (semibold, centred)
      stat context (regular, centred, muted)
      source (small, muted)
      @handle
      [12px gold bottom bar]
    """
    fonts = _ensure_fonts()
    img = Image.new("RGB", (SIZE, SIZE), WHITE)
    draw = ImageDraw.Draw(img)

    # Top gold block
    draw.rectangle([0, 0, SIZE, 80], fill=GOLD)
    # Bottom thin bar
    _thin_bar(draw, SIZE - 12)

    max_w = SIZE - PAD * 2

    # ── Giant stat number ──────────────────────────────────────────────────────
    num_font = _font(fonts, "bold", 220)
    num_lines = _wrap(stat_number, num_font, max_w, draw)[:1]
    num_h = _block_height(num_lines, num_font, draw, gap=10)

    # ── Label ──────────────────────────────────────────────────────────────────
    lbl_font = _font(fonts, "semibold", 52)
    lbl_lines = _wrap(stat_label.upper(), lbl_font, max_w, draw)[:2]
    lbl_h = _block_height(lbl_lines, lbl_font, draw, gap=12)

    # ── Context ────────────────────────────────────────────────────────────────
    ctx_font = _font(fonts, "regular", 38)
    ctx_lines = _wrap(stat_context, ctx_font, max_w, draw)[:3]
    ctx_h = _block_height(ctx_lines, ctx_font, draw, gap=12)

    # ── Source ─────────────────────────────────────────────────────────────────
    src_font = _font(fonts, "regular", 28)
    src_h = draw.textbbox((0, 0), stat_source, font=src_font)[3] if stat_source else 0

    divider_h = 8
    spacing = [40, 32, 28, 24, 40]  # gaps: after-block, after-num, after-div, after-lbl, after-ctx

    total_h = (num_h + spacing[1] + divider_h + spacing[2] +
               lbl_h + spacing[3] + ctx_h + spacing[4] + src_h)

    y = 80 + (SIZE - 80 - 12 - total_h) // 2

    # Draw number
    y = _draw_lines(draw, num_lines, num_font, PAD, y, DARK, align="center", max_w=max_w, line_gap=10)
    y += spacing[1]

    # Gold divider
    div_w = 160
    draw.rectangle([(SIZE - div_w) // 2, y, (SIZE + div_w) // 2, y + divider_h], fill=GOLD)
    y += divider_h + spacing[2]

    # Label
    y = _draw_lines(draw, lbl_lines, lbl_font, PAD, y, DARK, align="center", max_w=max_w, line_gap=12)
    y += spacing[3]

    # Context
    y = _draw_lines(draw, ctx_lines, ctx_font, PAD, y, MID, align="center", max_w=max_w, line_gap=12)
    y += spacing[4]

    # Source
    if stat_source:
        src_bbox = draw.textbbox((0, 0), stat_source, font=src_font)
        sw = src_bbox[2] - src_bbox[0]
        draw.text(((SIZE - sw) // 2, y), stat_source, font=src_font, fill=MUTED)

    _brand_handle(draw, fonts, brand_handle)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", quality=95)
    logger.info("Generated stat card: %s", output_path)
    return output_path


# ═══════════════════════════════════════════════════════════════════════════════
# 2. TIP CAROUSEL
# ═══════════════════════════════════════════════════════════════════════════════

def generate_tips_cover(
    tips_title: str,
    total_slides: int,
    brand_handle: str,
    output_path: Path,
) -> Path:
    """
    Cover slide: cream background, gold top block, large title, dots, SWIPE hint.
    """
    fonts = _ensure_fonts()
    img = Image.new("RGB", (SIZE, SIZE), CREAM)
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, SIZE, 60], fill=GOLD)
    _thin_bar(draw, SIZE - 12)

    max_w = SIZE - PAD * 2

    # SWIPE → hint top right
    sw_font = _font(fonts, "semibold", 30)
    hint = "SWIPE →"
    hint_bbox = draw.textbbox((0, 0), hint, font=sw_font)
    draw.text((SIZE - PAD - (hint_bbox[2] - hint_bbox[0]), 60 + 28), hint, font=sw_font, fill=GOLD)

    # Title
    title_font = _font(fonts, "bold", 84)
    title_lines = _wrap(tips_title.upper(), title_font, max_w, draw)[:4]
    title_h = _block_height(title_lines, title_font, draw, gap=20)

    y = 60 + (SIZE - 60 - 12 - title_h - 80) // 2
    y = _draw_lines(draw, title_lines, title_font, PAD, y, DARK, line_gap=20)

    # Progress dots
    dot_y = y + 48
    dot_r = 10
    gap = 14
    total_dot_w = total_slides * dot_r * 2 + (total_slides - 1) * gap
    dot_x = (SIZE - total_dot_w) // 2
    for i in range(total_slides):
        fill = GOLD if i == 0 else MUTED
        draw.ellipse([dot_x, dot_y, dot_x + dot_r * 2, dot_y + dot_r * 2], fill=fill)
        dot_x += dot_r * 2 + gap

    _brand_handle(draw, fonts, brand_handle)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", quality=95)
    logger.info("Generated tips cover: %s", output_path)
    return output_path


def generate_tips_slide(
    number: str,
    heading: str,
    body: str,
    bonus: str,
    slide_num: int,
    total_slides: int,
    brand_handle: str,
    output_path: Path,
) -> Path:
    """
    Tip content slide: large number + heading, body, bonus tip.
    """
    fonts = _ensure_fonts()
    img = Image.new("RGB", (SIZE, SIZE), WHITE)
    draw = ImageDraw.Draw(img)

    _thin_bar(draw, 0)
    _thin_bar(draw, SIZE - 12)

    max_w = SIZE - PAD * 2

    # Slide counter top right
    count_font = _font(fonts, "semibold", 32)
    count_text = f"{slide_num}/{total_slides}"
    cb = draw.textbbox((0, 0), count_text, font=count_font)
    draw.text((SIZE - PAD - (cb[2] - cb[0]), 12 + 28), count_text, font=count_font, fill=MUTED)

    # Number (large, gold)
    num_font = _font(fonts, "bold", 110)
    draw.text((PAD, 12 + 28), number, font=num_font, fill=GOLD)

    # Heading
    head_font = _font(fonts, "bold", 76)
    head_lines = _wrap(heading.upper(), head_font, max_w, draw)[:2]

    num_bbox = draw.textbbox((0, 0), number, font=num_font)
    y = 12 + 28 + (num_bbox[3] - num_bbox[1]) + 20

    y = _draw_lines(draw, head_lines, head_font, PAD, y, DARK, line_gap=16)

    # Gold underline
    y += 20
    draw.rectangle([PAD, y, PAD + 120, y + 6], fill=GOLD)
    y += 38

    # Body
    body_font = _font(fonts, "regular", 42)
    body_lines = _wrap(body, body_font, max_w, draw)[:5]
    y = _draw_lines(draw, body_lines, body_font, PAD, y, MID, line_gap=16)

    # Bonus tip (muted, smaller)
    if bonus:
        y += 24
        bonus_font = _font(fonts, "semibold", 34)
        bonus_lines = _wrap(f"✦  {bonus}", bonus_font, max_w, draw)[:2]
        _draw_lines(draw, bonus_lines, bonus_font, PAD, y, MUTED, line_gap=12)

    _brand_handle(draw, fonts, brand_handle)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", quality=95)
    logger.info("Generated tip slide %d/%d: %s", slide_num, total_slides, output_path)
    return output_path


def generate_tips_cta(
    tips_cta: str,
    brand_handle: str,
    output_path: Path,
) -> Path:
    """Final carousel slide: CTA + save prompt."""
    fonts = _ensure_fonts()
    img = Image.new("RGB", (SIZE, SIZE), CREAM)
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, SIZE, 60], fill=GOLD)
    _thin_bar(draw, SIZE - 12)

    max_w = SIZE - PAD * 2

    # Save icon area
    icon_font = _font(fonts, "bold", 120)
    icon = "🔖"
    try:
        # Use a large gold block as stand-in since emoji rendering is unreliable in Pillow
        draw.rectangle([(SIZE - 80) // 2, 180, (SIZE + 80) // 2, 260], fill=GOLD)
    except Exception:
        pass

    cta_font = _font(fonts, "bold", 68)
    cta_lines = _wrap(tips_cta.upper(), cta_font, max_w, draw)[:3]
    cta_h = _block_height(cta_lines, cta_font, draw, gap=20)

    y = 60 + (SIZE - 60 - 12 - cta_h - 80) // 2
    _draw_lines(draw, cta_lines, cta_font, PAD, y, DARK, align="center", max_w=max_w, line_gap=20)

    _brand_handle(draw, fonts, brand_handle)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", quality=95)
    logger.info("Generated tips CTA slide: %s", output_path)
    return output_path


# ═══════════════════════════════════════════════════════════════════════════════
# 3. MYTH vs FACT
# ═══════════════════════════════════════════════════════════════════════════════

def generate_myth_slide(
    myth: str,
    brand_handle: str,
    output_path: Path,
) -> Path:
    """Myth slide: bold red block at top, MYTH label, myth statement."""
    fonts = _ensure_fonts()
    img = Image.new("RGB", (SIZE, SIZE), WHITE)
    draw = ImageDraw.Draw(img)

    # Red colour block (top 200px)
    draw.rectangle([0, 0, SIZE, 200], fill=MYTH_RED)
    _thin_bar(draw, SIZE - 12, color=MYTH_RED)

    max_w = SIZE - PAD * 2

    # "MYTH" label — large, white, inside red block
    myth_lbl_font = _font(fonts, "bold", 110)
    lbl_bbox = draw.textbbox((0, 0), "MYTH", font=myth_lbl_font)
    lbl_h = lbl_bbox[3] - lbl_bbox[1]
    draw.text((PAD, (200 - lbl_h) // 2), "MYTH", font=myth_lbl_font, fill=BLOCK_TEXT)

    # Gold underline below MYTH
    draw.rectangle([PAD, 200 + 32, PAD + 160, 200 + 40], fill=MYTH_RED)

    y = 200 + 64

    # Tap hint
    tap_font = _font(fonts, "regular", 32)
    tap_text = "Tap for the truth →"
    tap_bbox = draw.textbbox((0, 0), tap_text, font=tap_font)
    draw.text((SIZE - PAD - (tap_bbox[2] - tap_bbox[0]), y), tap_text, font=tap_font, fill=MUTED)
    y += (tap_bbox[3] - tap_bbox[1]) + 36

    # Myth statement (italic-style — just semibold)
    myth_font = _font(fonts, "semibold", 54)
    myth_text = f'"{myth}"'
    myth_lines = _wrap(myth_text, myth_font, max_w, draw)[:5]
    _draw_lines(draw, myth_lines, myth_font, PAD, y, DARK, line_gap=18)

    _brand_handle(draw, fonts, brand_handle)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", quality=95)
    logger.info("Generated myth slide: %s", output_path)
    return output_path


def generate_fact_slide(
    fact_headline: str,
    fact_body: str,
    brand_handle: str,
    output_path: Path,
) -> Path:
    """Fact slide: bold green block at top, FACT label, fact content."""
    fonts = _ensure_fonts()
    img = Image.new("RGB", (SIZE, SIZE), WHITE)
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, SIZE, 200], fill=FACT_GREEN)
    _thin_bar(draw, SIZE - 12, color=FACT_GREEN)

    max_w = SIZE - PAD * 2

    # "FACT" label inside green block
    fact_lbl_font = _font(fonts, "bold", 110)
    lbl_bbox = draw.textbbox((0, 0), "FACT", font=fact_lbl_font)
    lbl_h = lbl_bbox[3] - lbl_bbox[1]
    draw.text((PAD, (200 - lbl_h) // 2), "FACT", font=fact_lbl_font, fill=BLOCK_TEXT)

    y = 200 + 60

    # Headline
    hl_font = _font(fonts, "bold", 68)
    hl_lines = _wrap(fact_headline.upper(), hl_font, max_w, draw)[:2]
    y = _draw_lines(draw, hl_lines, hl_font, PAD, y, DARK, line_gap=16)

    # Green underline
    y += 16
    draw.rectangle([PAD, y, PAD + 120, y + 6], fill=FACT_GREEN)
    y += 40

    # Body
    body_font = _font(fonts, "regular", 44)
    body_lines = _wrap(fact_body, body_font, max_w, draw)[:6]
    _draw_lines(draw, body_lines, body_font, PAD, y, MID, line_gap=16)

    _brand_handle(draw, fonts, brand_handle)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", quality=95)
    logger.info("Generated fact slide: %s", output_path)
    return output_path


# ═══════════════════════════════════════════════════════════════════════════════
# 4. QUOTE CARD
# ═══════════════════════════════════════════════════════════════════════════════

def generate_quote_card(
    quote_text: str,
    quote_attribution: str,
    quote_context: str,
    brand_handle: str,
    output_path: Path,
) -> Path:
    """
    Layout:
      [12px gold top bar]
      Large decorative " (gold, 180px)
      Quote text (58px bold, centred)
      ─── Attribution ───  (gold lines + name)
      Quote context (muted, small)
      @handle
      [12px gold bottom bar]
    """
    fonts = _ensure_fonts()
    img = Image.new("RGB", (SIZE, SIZE), CREAM)
    draw = ImageDraw.Draw(img)

    _thin_bar(draw, 0)
    _thin_bar(draw, SIZE - 12)

    max_w = SIZE - PAD * 2

    # Decorative quote mark
    q_font = _font(fonts, "bold", 200)
    draw.text((PAD, 12 + 10), "\u201c", font=q_font, fill=GOLD)
    q_bbox = draw.textbbox((0, 0), "\u201c", font=q_font)
    q_mark_h = q_bbox[3] - q_bbox[1]

    y = 12 + 10 + q_mark_h - 40  # slight overlap so quote sits close

    # Quote text
    qt_font = _font(fonts, "bold", 56)
    qt_lines = _wrap(quote_text, qt_font, max_w, draw)[:6]
    qt_h = _block_height(qt_lines, qt_font, draw, gap=18)
    y = _draw_lines(draw, qt_lines, qt_font, PAD, y, DARK, align="center", max_w=max_w, line_gap=18)

    y += 48

    # Attribution line: short gold rule — Name — short gold rule
    attr_font = _font(fonts, "semibold", 36)
    attr_bbox = draw.textbbox((0, 0), quote_attribution, font=attr_font)
    attr_w = attr_bbox[2] - attr_bbox[0]
    rule_w = (max_w - attr_w - 48) // 2
    rule_y = y + (attr_bbox[3] - attr_bbox[1]) // 2
    x0 = PAD
    # left rule
    draw.rectangle([x0, rule_y, x0 + rule_w, rule_y + 3], fill=GOLD)
    # name
    draw.text((x0 + rule_w + 24, y), quote_attribution, font=attr_font, fill=MID)
    # right rule
    rx = x0 + rule_w + 24 + attr_w + 24
    draw.rectangle([rx, rule_y, rx + rule_w, rule_y + 3], fill=GOLD)

    # Context
    if quote_context:
        y += (attr_bbox[3] - attr_bbox[1]) + 32
        ctx_font = _font(fonts, "regular", 34)
        ctx_lines = _wrap(quote_context, ctx_font, max_w, draw)[:2]
        _draw_lines(draw, ctx_lines, ctx_font, PAD, y, MUTED, align="center", max_w=max_w, line_gap=12)

    _brand_handle(draw, fonts, brand_handle)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", quality=95)
    logger.info("Generated quote card: %s", output_path)
    return output_path


# ═══════════════════════════════════════════════════════════════════════════════
# Legacy wrappers (kept so Canva fallback path still compiles)
# ═══════════════════════════════════════════════════════════════════════════════

def generate_single_post(hook, caption_preview, brand_handle, output_path):
    """Legacy wrapper — maps old single-post call to a stat-style card."""
    return generate_stat_card(
        stat_number="",
        stat_label=hook[:60],
        stat_context=caption_preview[:120],
        stat_source="",
        brand_handle=brand_handle,
        output_path=output_path,
    )


def generate_carousel_cover(hook, total_slides, brand_handle, output_path):
    return generate_tips_cover(
        tips_title=hook,
        total_slides=total_slides,
        brand_handle=brand_handle,
        output_path=output_path,
    )


def generate_carousel_slide(heading, body, slide_num, total_slides, brand_handle, output_path):
    return generate_tips_slide(
        number=f"{slide_num:02d}",
        heading=heading,
        body=body,
        bonus="",
        slide_num=slide_num,
        total_slides=total_slides,
        brand_handle=brand_handle,
        output_path=output_path,
    )
