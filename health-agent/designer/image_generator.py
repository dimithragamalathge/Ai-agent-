"""
Dr. Dimithra Instagram image generator — Modern Clinical Wellness theme.

Brand palette:
  Base cream:        #F9F6F0   backgrounds
  Primary sage:      #8FA89B   headers, healthy data bars
  Anchor slate:      #3A4042   body text
  Accent terracotta: #C87B67   alerts, high-risk bars, CTAs

7-slide carousel (post_type = "tips"):
  1. Hook            — bold Lora headline on cream
  2. Clinical Reality — empathy context
  3–5. Breakdown      — bar chart (matplotlib) or key-idea text slide
  6. Prevention       — numbered action bullets
  7. CTA + Disclaimer

Single posts: Stat Card, Quote Card
2-slide: Myth (terracotta block) / Fact (sage block)
"""

import io
import logging
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    _MPL = True
except ImportError:
    _MPL = False

import config

logger = logging.getLogger(__name__)

# ── Brand palette ──────────────────────────────────────────────────────────────
BASE_CREAM        = "#F9F6F0"
PRIMARY_SAGE      = "#8FA89B"
ANCHOR_SLATE      = "#3A4042"
ACCENT_TERRACOTTA = "#C87B67"
LIGHT_SAGE        = "#C8D5CF"
WHITE             = "#FFFFFF"

# ── Canvas ─────────────────────────────────────────────────────────────────────
SIZE = 1080
PAD  = 72

# ── Fonts ──────────────────────────────────────────────────────────────────────
FONT_DIR = config.OUTPUT_DIR.parent / "fonts"

FONT_URLS = {
    "lora_bold":        "https://github.com/google/fonts/raw/main/ofl/lora/static/Lora-Bold.ttf",
    "lato_regular":     "https://github.com/google/fonts/raw/main/ofl/lato/Lato-Regular.ttf",
    "lato_bold":        "https://github.com/google/fonts/raw/main/ofl/lato/Lato-Bold.ttf",
    "poppins_bold":     "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf",
    "poppins_semibold": "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-SemiBold.ttf",
    "poppins_regular":  "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Regular.ttf",
}

# Logical font → candidate priority
_FONT_FALLBACKS = {
    "header":     ["lora_bold", "poppins_bold"],
    "body":       ["lato_regular", "poppins_regular"],
    "body_bold":  ["lato_bold", "poppins_bold"],
    "accent":     ["lato_bold", "poppins_semibold"],
}


def _ensure_fonts() -> dict[str, Path]:
    FONT_DIR.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for name, url in FONT_URLS.items():
        dest = FONT_DIR / f"{name}.ttf"
        if not dest.exists():
            logger.info("Downloading font: %s", dest.name)
            try:
                resp = requests.get(url, timeout=20)
                resp.raise_for_status()
                dest.write_bytes(resp.content)
            except Exception as exc:
                logger.warning("Font download failed (%s): %s", name, exc)
        paths[name] = dest
    return paths


def _font(paths: dict[str, Path], role: str, size: int) -> ImageFont.FreeTypeFont:
    for candidate in _FONT_FALLBACKS.get(role, [role]):
        p = paths.get(candidate)
        if p and p.exists():
            try:
                return ImageFont.truetype(str(p), size)
            except Exception:
                continue
    return ImageFont.load_default()


def _wrap(text: str, font: ImageFont.FreeTypeFont, max_w: int,
          draw: ImageDraw.ImageDraw) -> list[str]:
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


def _draw_lines(draw, lines, font, x, y, fill,
                align="left", max_w=None, gap=16) -> int:
    for line in lines:
        bb = draw.textbbox((0, 0), line, font=font)
        lw, lh = bb[2] - bb[0], bb[3] - bb[1]
        lx = x + (max_w - lw) // 2 if align == "center" and max_w else x
        draw.text((lx, y), line, font=font, fill=fill)
        y += lh + gap
    return y


def _block_h(lines, font, draw, gap=16) -> int:
    if not lines:
        return 0
    total = sum((draw.textbbox((0, 0), l, font=font)[3] - draw.textbbox((0, 0), l, font=font)[1]) + gap
                for l in lines)
    return total - gap


# ── Base elements ──────────────────────────────────────────────────────────────

def _sage_block(draw: ImageDraw.ImageDraw, height: int = 90):
    draw.rectangle([0, 0, SIZE, height], fill=PRIMARY_SAGE)


def _thin_bar(draw: ImageDraw.ImageDraw, y: int, color: str = PRIMARY_SAGE, h: int = 8):
    draw.rectangle([0, y, SIZE, y + h], fill=color)


def _brand_handle(draw: ImageDraw.ImageDraw, fonts: dict, handle: str):
    font = _font(fonts, "body", 30)
    text = handle if handle.startswith("@") else f"@{handle}"
    bb = draw.textbbox((0, 0), text, font=font)
    draw.text(((SIZE - (bb[2] - bb[0])) // 2, SIZE - 8 - 52), text, font=font, fill=ANCHOR_SLATE)


def _slide_counter(draw: ImageDraw.ImageDraw, fonts: dict, num: int, total: int, y: int = 26):
    font = _font(fonts, "body", 28)
    text = f"{num} / {total}"
    bb = draw.textbbox((0, 0), text, font=font)
    draw.text((SIZE - PAD - (bb[2] - bb[0]), y), text, font=font, fill=ANCHOR_SLATE)


# ── Matplotlib bar chart → PIL Image ──────────────────────────────────────────

def _make_bar_chart(title: str, takeaway: str, categories: list,
                    values: list, highlight_index: int,
                    w_px: int, h_px: int) -> "Image.Image | None":
    if not _MPL:
        return None
    dpi = 100
    fig, ax = plt.subplots(figsize=(w_px / dpi, h_px / dpi), facecolor=BASE_CREAM)
    ax.set_facecolor(BASE_CREAM)

    bar_colors = [ACCENT_TERRACOTTA if i == highlight_index else PRIMARY_SAGE
                  for i in range(len(categories))]
    bars = ax.bar(categories, values, color=bar_colors, width=0.55, zorder=3)

    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(ANCHOR_SLATE)
    ax.spines["bottom"].set_linewidth(1.5)
    ax.set_yticks([])
    ax.tick_params(axis="x", colors=ANCHOR_SLATE, labelsize=13)

    for bar in bars:
        h = bar.get_height()
        ax.annotate(f"{h:.0f}",
                    xy=(bar.get_x() + bar.get_width() / 2, h),
                    xytext=(0, 6), textcoords="offset points",
                    ha="center", va="bottom",
                    color=ANCHOR_SLATE, fontsize=14, fontweight="bold")

    fig.suptitle(title, color=ANCHOR_SLATE, fontsize=16, fontweight="bold", y=0.97)
    ax.set_title(takeaway, color=ACCENT_TERRACOTTA, fontsize=12, pad=14)

    plt.tight_layout()
    plt.subplots_adjust(top=0.86, bottom=0.1)

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=dpi, bbox_inches="tight",
                facecolor=BASE_CREAM, edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert("RGB")


# ═══════════════════════════════════════════════════════════════════════════════
# 7-SLIDE CAROUSEL
# ═══════════════════════════════════════════════════════════════════════════════

def generate_hook_slide(hook: str, total_slides: int,
                         brand_handle: str, output_path: Path) -> Path:
    """Slide 1 — The Hook."""
    fonts = _ensure_fonts()
    img = Image.new("RGB", (SIZE, SIZE), BASE_CREAM)
    draw = ImageDraw.Draw(img)

    _sage_block(draw, height=90)
    _thin_bar(draw, SIZE - 8)
    max_w = SIZE - PAD * 2

    # Brand + SWIPE hint on sage block
    lbl_font = _font(fonts, "body", 28)
    handle_text = brand_handle if brand_handle.startswith("@") else f"@{brand_handle}"
    lbl_h = draw.textbbox((0, 0), handle_text, font=lbl_font)[3]
    draw.text((PAD, (90 - lbl_h) // 2), handle_text, font=lbl_font, fill=WHITE)
    hint = "SWIPE →"
    hb = draw.textbbox((0, 0), hint, font=lbl_font)
    draw.text((SIZE - PAD - (hb[2] - hb[0]), (90 - (hb[3] - hb[1])) // 2),
              hint, font=lbl_font, fill=WHITE)

    # Hook text — Lora Bold, large, centered in remaining space
    h_font = _font(fonts, "header", 84)
    hook_lines = _wrap(hook, h_font, max_w, draw)[:4]
    hook_h = _block_h(hook_lines, h_font, draw, gap=20)
    y = 90 + (SIZE - 90 - 8 - hook_h) // 2
    _draw_lines(draw, hook_lines, h_font, PAD, y, ANCHOR_SLATE,
                align="center", max_w=max_w, gap=20)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", quality=95)
    logger.info("Generated hook slide: %s", output_path)
    return output_path


def generate_clinical_reality_slide(text: str, slide_num: int, total: int,
                                     brand_handle: str, output_path: Path) -> Path:
    """Slide 2 — Clinical Reality (empathy)."""
    fonts = _ensure_fonts()
    img = Image.new("RGB", (SIZE, SIZE), BASE_CREAM)
    draw = ImageDraw.Draw(img)

    _thin_bar(draw, 0)
    _thin_bar(draw, SIZE - 8)
    _slide_counter(draw, fonts, slide_num, total, y=26)

    max_w = SIZE - PAD * 2

    lbl_font = _font(fonts, "accent", 22)
    draw.text((PAD, 32), "CLINICAL REALITY", font=lbl_font, fill=PRIMARY_SAGE)
    underline_y = 32 + draw.textbbox((0, 0), "CLINICAL REALITY", font=lbl_font)[3] + 8
    draw.rectangle([PAD, underline_y, PAD + 180, underline_y + 4], fill=PRIMARY_SAGE)

    body_font = _font(fonts, "header", 52)
    body_lines = _wrap(text, body_font, max_w, draw)[:6]
    body_h = _block_h(body_lines, body_font, draw, gap=22)
    y = underline_y + 60 + (SIZE - underline_y - 60 - 80 - body_h) // 2
    _draw_lines(draw, body_lines, body_font, PAD, y, ANCHOR_SLATE, gap=22)

    _brand_handle(draw, fonts, brand_handle)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", quality=95)
    logger.info("Generated clinical reality slide: %s", output_path)
    return output_path


def generate_chart_breakdown_slide(title: str, takeaway: str,
                                    categories: list, values: list, highlight_index: int,
                                    slide_num: int, total: int,
                                    brand_handle: str, output_path: Path) -> Path:
    """Slides 3-5 — Branded bar chart."""
    fonts = _ensure_fonts()
    img = Image.new("RGB", (SIZE, SIZE), BASE_CREAM)
    draw = ImageDraw.Draw(img)

    _thin_bar(draw, 0)
    _thin_bar(draw, SIZE - 8)
    _slide_counter(draw, fonts, slide_num, total, y=22)

    chart_top = 64
    chart_bottom = SIZE - 90
    chart_w = SIZE - PAD * 2
    chart_h = chart_bottom - chart_top

    chart_img = _make_bar_chart(title, takeaway, categories, values,
                                highlight_index, chart_w, chart_h)
    if chart_img:
        chart_img = chart_img.resize((chart_w, chart_h), Image.LANCZOS)
        img.paste(chart_img, (PAD, chart_top))
    else:
        # Text fallback if matplotlib unavailable
        tf = _font(fonts, "header", 52)
        tl = _wrap(f"{title} — {takeaway}", tf, chart_w, draw)[:4]
        _draw_lines(draw, tl, tf, PAD, chart_top + 80, ANCHOR_SLATE, gap=20)

    _brand_handle(draw, fonts, brand_handle)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", quality=95)
    logger.info("Generated chart slide %d/%d: %s", slide_num, total, output_path)
    return output_path


def generate_text_breakdown_slide(heading: str, body: str,
                                   slide_num: int, total: int,
                                   brand_handle: str, output_path: Path) -> Path:
    """Slides 3-5 — Key idea text slide."""
    fonts = _ensure_fonts()
    img = Image.new("RGB", (SIZE, SIZE), BASE_CREAM)
    draw = ImageDraw.Draw(img)

    _thin_bar(draw, 0)
    _thin_bar(draw, SIZE - 8)
    _slide_counter(draw, fonts, slide_num, total, y=22)

    max_w = SIZE - PAD * 2

    h_font = _font(fonts, "header", 68)
    h_lines = _wrap(heading.upper(), h_font, max_w, draw)[:2]
    y = 100
    y = _draw_lines(draw, h_lines, h_font, PAD, y, PRIMARY_SAGE, gap=16)

    y += 24
    draw.rectangle([PAD, y, PAD + 120, y + 6], fill=ACCENT_TERRACOTTA)
    y += 48

    b_font = _font(fonts, "body", 46)
    b_lines = _wrap(body, b_font, max_w, draw)[:7]
    _draw_lines(draw, b_lines, b_font, PAD, y, ANCHOR_SLATE, gap=18)

    _brand_handle(draw, fonts, brand_handle)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", quality=95)
    logger.info("Generated text breakdown slide %d/%d: %s", slide_num, total, output_path)
    return output_path


def generate_prevention_slide(bullets: list, slide_num: int, total: int,
                               brand_handle: str, output_path: Path) -> Path:
    """Slide 6 — What You Can Do (3 numbered bullets)."""
    fonts = _ensure_fonts()
    img = Image.new("RGB", (SIZE, SIZE), BASE_CREAM)
    draw = ImageDraw.Draw(img)

    _sage_block(draw, height=90)
    _thin_bar(draw, SIZE - 8)
    _slide_counter(draw, fonts, slide_num, total, y=32)

    hdr_font = _font(fonts, "body_bold", 28)
    hdr_h = draw.textbbox((0, 0), "WHAT YOU CAN DO", font=hdr_font)[3]
    draw.text((PAD, (90 - hdr_h) // 2), "WHAT YOU CAN DO", font=hdr_font, fill=WHITE)

    max_w = SIZE - PAD * 2 - 100
    num_font = _font(fonts, "header", 56)
    txt_font = _font(fonts, "body", 44)

    y = 130
    for i, bullet in enumerate(bullets[:3]):
        r = 40
        cx, cy = PAD + r, y + r
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=ACCENT_TERRACOTTA)
        n = str(i + 1)
        nb = draw.textbbox((0, 0), n, font=num_font)
        draw.text((cx - (nb[2] - nb[0]) // 2, cy - (nb[3] - nb[1]) // 2 - 2),
                  n, font=num_font, fill=WHITE)

        b_lines = _wrap(bullet, txt_font, max_w, draw)[:3]
        bh = _block_h(b_lines, txt_font, draw, gap=12)
        by = y + max(0, (r * 2 - bh) // 2)
        _draw_lines(draw, b_lines, txt_font, PAD + r * 2 + 24, by, ANCHOR_SLATE, gap=12)
        y += max(r * 2, bh) + 52

    _brand_handle(draw, fonts, brand_handle)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", quality=95)
    logger.info("Generated prevention slide: %s", output_path)
    return output_path


def generate_cta_slide(cta_text: str, disclaimer: str,
                        brand_handle: str, output_path: Path) -> Path:
    """Slide 7 — CTA + Disclaimer."""
    fonts = _ensure_fonts()
    img = Image.new("RGB", (SIZE, SIZE), BASE_CREAM)
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, SIZE, 200], fill=PRIMARY_SAGE)
    _thin_bar(draw, SIZE - 8)

    bn_font = _font(fonts, "body_bold", 40)
    bn = brand_handle if brand_handle.startswith("@") else f"@{brand_handle}"
    bb = draw.textbbox((0, 0), bn, font=bn_font)
    draw.text(((SIZE - (bb[2] - bb[0])) // 2, (200 - (bb[3] - bb[1])) // 2),
              bn, font=bn_font, fill=WHITE)

    max_w = SIZE - PAD * 2

    cta_font = _font(fonts, "header", 64)
    cta_lines = _wrap(cta_text, cta_font, max_w, draw)[:3]
    cta_h = _block_h(cta_lines, cta_font, draw, gap=20)
    y = 200 + (SIZE - 200 - 8 - cta_h - 140) // 2
    y = _draw_lines(draw, cta_lines, cta_font, PAD, y, ANCHOR_SLATE,
                    align="center", max_w=max_w, gap=20)

    y += 44
    draw.rectangle([(SIZE - 120) // 2, y, (SIZE + 120) // 2, y + 4], fill=ACCENT_TERRACOTTA)
    y += 36

    if disclaimer:
        d_font = _font(fonts, "body", 26)
        d_lines = _wrap(disclaimer, d_font, max_w, draw)[:3]
        _draw_lines(draw, d_lines, d_font, PAD, y, ANCHOR_SLATE,
                    align="center", max_w=max_w, gap=10)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", quality=95)
    logger.info("Generated CTA slide: %s", output_path)
    return output_path


# ═══════════════════════════════════════════════════════════════════════════════
# STAT CARD
# ═══════════════════════════════════════════════════════════════════════════════

def generate_stat_card(stat_number: str, stat_label: str, stat_context: str,
                        stat_source: str, brand_handle: str, output_path: Path) -> Path:
    fonts = _ensure_fonts()
    img = Image.new("RGB", (SIZE, SIZE), BASE_CREAM)
    draw = ImageDraw.Draw(img)

    _sage_block(draw, height=90)
    _thin_bar(draw, SIZE - 8)
    max_w = SIZE - PAD * 2

    num_font  = _font(fonts, "header", 210)
    lbl_font  = _font(fonts, "accent",  52)
    ctx_font  = _font(fonts, "body",    38)
    src_font  = _font(fonts, "body",    26)

    num_lines = _wrap(stat_number, num_font, max_w, draw)[:1]
    lbl_lines = _wrap(stat_label.upper(), lbl_font, max_w, draw)[:2]
    ctx_lines = _wrap(stat_context, ctx_font, max_w, draw)[:3]

    num_h = _block_h(num_lines, num_font, draw, gap=8)
    lbl_h = _block_h(lbl_lines, lbl_font, draw, gap=10)
    ctx_h = _block_h(ctx_lines, ctx_font, draw, gap=10)
    src_h = draw.textbbox((0, 0), stat_source, font=src_font)[3] if stat_source else 0

    total = num_h + 40 + 8 + 32 + lbl_h + 28 + ctx_h + (36 + src_h if stat_source else 0)
    y = 90 + (SIZE - 90 - 8 - total) // 2

    y = _draw_lines(draw, num_lines, num_font, PAD, y, ANCHOR_SLATE,
                    align="center", max_w=max_w, gap=8)
    y += 40
    draw.rectangle([(SIZE - 120) // 2, y, (SIZE + 120) // 2, y + 8], fill=ACCENT_TERRACOTTA)
    y += 8 + 32
    y = _draw_lines(draw, lbl_lines, lbl_font, PAD, y, ANCHOR_SLATE,
                    align="center", max_w=max_w, gap=10)
    y += 28
    y = _draw_lines(draw, ctx_lines, ctx_font, PAD, y, ANCHOR_SLATE,
                    align="center", max_w=max_w, gap=10)
    if stat_source:
        y += 36
        sb = draw.textbbox((0, 0), stat_source, font=src_font)
        draw.text(((SIZE - (sb[2] - sb[0])) // 2, y), stat_source, font=src_font, fill=ANCHOR_SLATE)

    _brand_handle(draw, fonts, brand_handle)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", quality=95)
    logger.info("Generated stat card: %s", output_path)
    return output_path


# ═══════════════════════════════════════════════════════════════════════════════
# QUOTE CARD
# ═══════════════════════════════════════════════════════════════════════════════

def generate_quote_card(quote_text: str, quote_attribution: str, quote_context: str,
                         brand_handle: str, output_path: Path) -> Path:
    fonts = _ensure_fonts()
    img = Image.new("RGB", (SIZE, SIZE), BASE_CREAM)
    draw = ImageDraw.Draw(img)

    _thin_bar(draw, 0)
    _thin_bar(draw, SIZE - 8)
    max_w = SIZE - PAD * 2

    q_font = _font(fonts, "header", 200)
    draw.text((PAD, 8), "\u201c", font=q_font, fill=ACCENT_TERRACOTTA)
    q_h = draw.textbbox((0, 0), "\u201c", font=q_font)[3]

    y = 8 + q_h - 50
    qt_font = _font(fonts, "header", 56)
    qt_lines = _wrap(quote_text, qt_font, max_w, draw)[:6]
    y = _draw_lines(draw, qt_lines, qt_font, PAD, y, ANCHOR_SLATE,
                    align="center", max_w=max_w, gap=18)

    y += 52
    attr_font = _font(fonts, "accent", 34)
    ab = draw.textbbox((0, 0), quote_attribution, font=attr_font)
    aw, ah = ab[2] - ab[0], ab[3] - ab[1]
    rule_w = (max_w - aw - 48) // 2
    rule_y = y + ah // 2
    draw.rectangle([PAD, rule_y, PAD + rule_w, rule_y + 3], fill=PRIMARY_SAGE)
    draw.text((PAD + rule_w + 24, y), quote_attribution, font=attr_font, fill=ANCHOR_SLATE)
    rx = PAD + rule_w + 24 + aw + 24
    draw.rectangle([rx, rule_y, rx + rule_w, rule_y + 3], fill=PRIMARY_SAGE)

    if quote_context:
        y += ah + 36
        cf = _font(fonts, "body", 32)
        cl = _wrap(quote_context, cf, max_w, draw)[:2]
        _draw_lines(draw, cl, cf, PAD, y, ANCHOR_SLATE, align="center", max_w=max_w, gap=10)

    _brand_handle(draw, fonts, brand_handle)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", quality=95)
    logger.info("Generated quote card: %s", output_path)
    return output_path


# ═══════════════════════════════════════════════════════════════════════════════
# MYTH vs FACT
# ═══════════════════════════════════════════════════════════════════════════════

def generate_myth_slide(myth: str, brand_handle: str, output_path: Path) -> Path:
    fonts = _ensure_fonts()
    img = Image.new("RGB", (SIZE, SIZE), BASE_CREAM)
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, SIZE, 200], fill=ACCENT_TERRACOTTA)
    _thin_bar(draw, SIZE - 8, color=ACCENT_TERRACOTTA)
    max_w = SIZE - PAD * 2

    lbl_font = _font(fonts, "header", 110)
    lb = draw.textbbox((0, 0), "MYTH", font=lbl_font)
    draw.text((PAD, (200 - (lb[3] - lb[1])) // 2), "MYTH", font=lbl_font, fill=WHITE)

    y = 200 + 60
    tap_font = _font(fonts, "body", 30)
    tap = "Tap for the truth →"
    tb = draw.textbbox((0, 0), tap, font=tap_font)
    draw.text((SIZE - PAD - (tb[2] - tb[0]), y), tap, font=tap_font, fill=ANCHOR_SLATE)
    y += (tb[3] - tb[1]) + 40

    myth_font = _font(fonts, "header", 52)
    myth_lines = _wrap(f'"{myth}"', myth_font, max_w, draw)[:5]
    _draw_lines(draw, myth_lines, myth_font, PAD, y, ANCHOR_SLATE, gap=18)

    _brand_handle(draw, fonts, brand_handle)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", quality=95)
    logger.info("Generated myth slide: %s", output_path)
    return output_path


def generate_fact_slide(fact_headline: str, fact_body: str,
                         brand_handle: str, output_path: Path) -> Path:
    fonts = _ensure_fonts()
    img = Image.new("RGB", (SIZE, SIZE), BASE_CREAM)
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, SIZE, 200], fill=PRIMARY_SAGE)
    _thin_bar(draw, SIZE - 8, color=PRIMARY_SAGE)
    max_w = SIZE - PAD * 2

    lbl_font = _font(fonts, "header", 110)
    lb = draw.textbbox((0, 0), "FACT", font=lbl_font)
    draw.text((PAD, (200 - (lb[3] - lb[1])) // 2), "FACT", font=lbl_font, fill=WHITE)

    y = 200 + 60
    hl_font = _font(fonts, "header", 68)
    hl_lines = _wrap(fact_headline.upper(), hl_font, max_w, draw)[:2]
    y = _draw_lines(draw, hl_lines, hl_font, PAD, y, ANCHOR_SLATE, gap=16)
    y += 16
    draw.rectangle([PAD, y, PAD + 120, y + 6], fill=ACCENT_TERRACOTTA)
    y += 44

    b_font = _font(fonts, "body", 44)
    b_lines = _wrap(fact_body, b_font, max_w, draw)[:6]
    _draw_lines(draw, b_lines, b_font, PAD, y, ANCHOR_SLATE, gap=16)

    _brand_handle(draw, fonts, brand_handle)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", quality=95)
    logger.info("Generated fact slide: %s", output_path)
    return output_path


# ═══════════════════════════════════════════════════════════════════════════════
# LEGACY WRAPPERS
# ═══════════════════════════════════════════════════════════════════════════════

def generate_single_post(hook, caption_preview, brand_handle, output_path):
    return generate_stat_card("", hook[:60], caption_preview[:120], "",
                               brand_handle, output_path)


def generate_carousel_cover(hook, total_slides, brand_handle, output_path):
    return generate_hook_slide(hook, total_slides, brand_handle, output_path)


def generate_carousel_slide(heading, body, slide_num, total_slides, brand_handle, output_path):
    return generate_text_breakdown_slide(heading, body, slide_num, total_slides,
                                          brand_handle, output_path)

# Tips cover/cta kept for any old code paths
def generate_tips_cover(tips_title, total_slides, brand_handle, output_path):
    return generate_hook_slide(tips_title, total_slides, brand_handle, output_path)

def generate_tips_slide(number, heading, body, bonus, slide_num, total_slides, brand_handle, output_path):
    return generate_text_breakdown_slide(heading, body, slide_num, total_slides, brand_handle, output_path)

def generate_tips_cta(tips_cta, brand_handle, output_path):
    return generate_cta_slide(tips_cta, "", brand_handle, output_path)
