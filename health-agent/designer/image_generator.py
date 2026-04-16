"""
Automatic branded image generator using Pillow.

Creates Instagram-ready 1080x1080 px post images with a warm earthy palette:
  Background:   #FDF6EC  (warm cream)
  Accent:       #E8A84C  (gold/orange bars and highlights)
  Primary text: #2C1810  (dark espresso brown)
  Secondary:    #7A5C4F  (warm medium brown)

No Canva templates needed — images are generated fully automatically.
Poppins font is downloaded on first run and cached in output/fonts/.
"""

import logging
import textwrap
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

import config

logger = logging.getLogger(__name__)

# ── Brand palette ─────────────────────────────────────────────────────────────
BG          = "#FDF6EC"
ACCENT      = "#E8A84C"
TEXT_DARK   = "#2C1810"
TEXT_MID    = "#7A5C4F"
TEXT_LIGHT  = "#B08B7A"
SIZE        = 1080
PADDING     = 80
ACCENT_BAR  = 12

# ── Font paths ────────────────────────────────────────────────────────────────
FONT_DIR = config.OUTPUT_DIR.parent / "fonts"

FONT_URLS = {
    "bold":    "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf",
    "semibold":"https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-SemiBold.ttf",
    "regular": "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Regular.ttf",
}


def _ensure_fonts() -> dict[str, Path]:
    """Download Poppins fonts on first run, return paths."""
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


def _load_font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    """Load a TTF font, fall back to PIL default if unavailable."""
    try:
        return ImageFont.truetype(str(path), size)
    except Exception:
        return ImageFont.load_default()


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
    """Wrap text to fit within max_width pixels."""
    words = text.split()
    lines: list[str] = []
    current = ""

    for word in words:
        test = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines


def _text_block_height(lines: list[str], font: ImageFont.FreeTypeFont, line_gap: int, draw: ImageDraw.ImageDraw) -> int:
    total = 0
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        total += (bbox[3] - bbox[1]) + line_gap
    return total - line_gap


def _draw_accent_bars(draw: ImageDraw.ImageDraw) -> None:
    draw.rectangle([0, 0, SIZE, ACCENT_BAR], fill=ACCENT)
    draw.rectangle([0, SIZE - ACCENT_BAR, SIZE, SIZE], fill=ACCENT)


def _draw_brand_handle(draw: ImageDraw.ImageDraw, handle: str, fonts: dict) -> None:
    font = _load_font(fonts.get("regular", Path()), 32)
    text = handle if handle.startswith("@") else f"@{handle}"
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    x = (SIZE - w) // 2
    y = SIZE - ACCENT_BAR - 50
    draw.text((x, y), text, font=font, fill=TEXT_LIGHT)


# ── Single post ───────────────────────────────────────────────────────────────


def generate_single_post(
    hook: str,
    caption_preview: str,
    brand_handle: str,
    output_path: Path,
) -> Path:
    """
    Generate a single 1080x1080 post image.

    Layout:
      [gold bar top]
      large bold HOOK TEXT (centered)
      gold divider line
      smaller caption preview
      @brand_handle
      [gold bar bottom]
    """
    fonts = _ensure_fonts()
    img = Image.new("RGB", (SIZE, SIZE), BG)
    draw = ImageDraw.Draw(img)

    _draw_accent_bars(draw)

    max_w = SIZE - PADDING * 2

    # ── Hook text ─────────────────────────────────────────────────────────────
    hook_font = _load_font(fonts.get("bold", Path()), 76)
    hook_lines = _wrap_text(hook.upper(), hook_font, max_w, draw)

    # Limit to 3 lines
    if len(hook_lines) > 3:
        hook_lines = hook_lines[:3]
        hook_lines[-1] = hook_lines[-1].rstrip() + "…"

    line_gap = 18
    hook_h = _text_block_height(hook_lines, hook_font, line_gap, draw)

    # Center hook vertically in upper 55% of canvas
    hook_top = ACCENT_BAR + int((SIZE * 0.55 - hook_h) / 2)
    y = hook_top
    for line in hook_lines:
        bbox = draw.textbbox((0, 0), line, font=hook_font)
        lw = bbox[2] - bbox[0]
        lh = bbox[3] - bbox[1]
        draw.text(((SIZE - lw) // 2, y), line, font=hook_font, fill=TEXT_DARK)
        y += lh + line_gap

    # ── Gold divider ──────────────────────────────────────────────────────────
    divider_y = y + 40
    div_w = 200
    draw.rectangle(
        [(SIZE - div_w) // 2, divider_y, (SIZE + div_w) // 2, divider_y + 4],
        fill=ACCENT,
    )

    # ── Caption preview ───────────────────────────────────────────────────────
    if caption_preview:
        cap_font = _load_font(fonts.get("regular", Path()), 38)
        preview = caption_preview[:120] + ("…" if len(caption_preview) > 120 else "")
        cap_lines = _wrap_text(preview, cap_font, max_w, draw)[:3]

        y = divider_y + 36
        for line in cap_lines:
            bbox = draw.textbbox((0, 0), line, font=cap_font)
            lw = bbox[2] - bbox[0]
            lh = bbox[3] - bbox[1]
            draw.text(((SIZE - lw) // 2, y), line, font=cap_font, fill=TEXT_MID)
            y += lh + 12

    _draw_brand_handle(draw, brand_handle, fonts)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", quality=95)
    logger.info("Generated single post image: %s", output_path)
    return output_path


# ── Carousel slide ────────────────────────────────────────────────────────────


def generate_carousel_slide(
    heading: str,
    body: str,
    slide_num: int,
    total_slides: int,
    brand_handle: str,
    output_path: Path,
) -> Path:
    """
    Generate one carousel slide image.

    Layout:
      [gold bar top]    slide N/total (top right)
      SLIDE HEADING
      ── short gold underline ──
      body text
      @brand_handle
      [gold bar bottom]
    """
    fonts = _ensure_fonts()
    img = Image.new("RGB", (SIZE, SIZE), BG)
    draw = ImageDraw.Draw(img)

    _draw_accent_bars(draw)

    max_w = SIZE - PADDING * 2

    # ── Slide number (top right) ──────────────────────────────────────────────
    num_font = _load_font(fonts.get("semibold", Path()), 34)
    num_text = f"{slide_num} / {total_slides}"
    bbox = draw.textbbox((0, 0), num_text, font=num_font)
    num_w = bbox[2] - bbox[0]
    draw.text((SIZE - PADDING - num_w, ACCENT_BAR + 28), num_text, font=num_font, fill=TEXT_LIGHT)

    # ── Heading ───────────────────────────────────────────────────────────────
    head_font = _load_font(fonts.get("bold", Path()), 68)
    head_lines = _wrap_text(heading.upper(), head_font, max_w, draw)[:2]

    y = ACCENT_BAR + 120
    for line in head_lines:
        bbox = draw.textbbox((0, 0), line, font=head_font)
        lh = bbox[3] - bbox[1]
        draw.text((PADDING, y), line, font=head_font, fill=TEXT_DARK)
        y += lh + 14

    # ── Gold underline ────────────────────────────────────────────────────────
    y += 20
    draw.rectangle([PADDING, y, PADDING + 120, y + 5], fill=ACCENT)
    y += 44

    # ── Body text ─────────────────────────────────────────────────────────────
    body_font = _load_font(fonts.get("regular", Path()), 42)
    body_lines = _wrap_text(body, body_font, max_w, draw)[:6]

    for line in body_lines:
        bbox = draw.textbbox((0, 0), line, font=body_font)
        lh = bbox[3] - bbox[1]
        draw.text((PADDING, y), line, font=body_font, fill=TEXT_MID)
        y += lh + 16

    _draw_brand_handle(draw, brand_handle, fonts)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", quality=95)
    logger.info("Generated carousel slide %d/%d: %s", slide_num, total_slides, output_path)
    return output_path


# ── Cover slide (slide 1 of a carousel) ──────────────────────────────────────


def generate_carousel_cover(
    hook: str,
    total_slides: int,
    brand_handle: str,
    output_path: Path,
) -> Path:
    """Generate the first carousel slide — a cover with the hook text."""
    fonts = _ensure_fonts()
    img = Image.new("RGB", (SIZE, SIZE), BG)
    draw = ImageDraw.Draw(img)

    _draw_accent_bars(draw)

    max_w = SIZE - PADDING * 2

    # "SWIPE →" hint at top right
    hint_font = _load_font(fonts.get("regular", Path()), 30)
    hint = "SWIPE →"
    bbox = draw.textbbox((0, 0), hint, font=hint_font)
    draw.text(
        (SIZE - PADDING - (bbox[2] - bbox[0]), ACCENT_BAR + 28),
        hint, font=hint_font, fill=ACCENT,
    )

    # Hook text (large, centered)
    hook_font = _load_font(fonts.get("bold", Path()), 80)
    hook_lines = _wrap_text(hook.upper(), hook_font, max_w, draw)[:3]

    line_gap = 20
    hook_h = _text_block_height(hook_lines, hook_font, line_gap, draw)
    y = ACCENT_BAR + (SIZE - ACCENT_BAR * 2 - hook_h) // 2 - 40

    for line in hook_lines:
        bbox = draw.textbbox((0, 0), line, font=hook_font)
        lw, lh = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((SIZE - lw) // 2, y), line, font=hook_font, fill=TEXT_DARK)
        y += lh + line_gap

    # Dots for slide count
    dot_y = y + 48
    dot_r = 8
    total_dot_w = total_slides * (dot_r * 2) + (total_slides - 1) * 10
    dot_x = (SIZE - total_dot_w) // 2
    for i in range(total_slides):
        fill = ACCENT if i == 0 else TEXT_LIGHT
        draw.ellipse([dot_x, dot_y, dot_x + dot_r * 2, dot_y + dot_r * 2], fill=fill)
        dot_x += dot_r * 2 + 10

    _draw_brand_handle(draw, brand_handle, fonts)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", quality=95)
    logger.info("Generated carousel cover: %s", output_path)
    return output_path
