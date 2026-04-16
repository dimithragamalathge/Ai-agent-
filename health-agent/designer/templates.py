"""
Template selection and design creation logic.

Priority order:
  1. Canva API  — if CANVA_SINGLE_POST_TEMPLATE_ID and CANVA_ACCESS_TOKEN are set
  2. Pillow generator — automatic, no setup needed (default)
"""

import logging
from pathlib import Path

import config
from processor.generator import GeneratedPost

logger = logging.getLogger(__name__)


def create_post_images(
    post: GeneratedPost,
    post_id: int,
    client=None,
) -> list[str]:
    """
    Produce PNG images for a post. Returns a list of local file paths.

    Uses Canva if configured, otherwise falls back to the Pillow generator.
    """
    output_dir = config.OUTPUT_DIR / f"post_{post_id}"
    output_dir.mkdir(parents=True, exist_ok=True)

    canva_ready = bool(
        config.CANVA_ACCESS_TOKEN
        and config.CANVA_CLIENT_ID
        and config.CANVA_SINGLE_POST_TEMPLATE_ID
    )

    if canva_ready:
        logger.info("Using Canva for post %d", post_id)
        return _create_with_canva(post, post_id, output_dir, client)
    else:
        logger.info("Using Pillow image generator for post %d (type: %s)", post_id, post.post_type)
        return _create_with_pillow(post, post_id, output_dir)


# ── Pillow generator (default) ────────────────────────────────────────────────


def _create_with_pillow(
    post: GeneratedPost,
    post_id: int,
    output_dir: Path,
) -> list[str]:
    from designer.image_generator import (
        generate_stat_card,
        generate_tips_cover,
        generate_tips_slide,
        generate_tips_cta,
        generate_myth_slide,
        generate_fact_slide,
        generate_quote_card,
    )

    handle = config.INSTAGRAM_HANDLE
    paths: list[str] = []
    post_type = getattr(post, "post_type", "tips")

    # ── Stat card ──────────────────────────────────────────────────────────────
    if post_type == "stat":
        out = output_dir / "post.png"
        generate_stat_card(
            stat_number=post.stat_number or post.hook[:10],
            stat_label=post.stat_label or post.hook,
            stat_context=post.stat_context or post.caption[:140],
            stat_source=post.stat_source or "",
            brand_handle=handle,
            output_path=out,
        )
        paths.append(str(out))

    # ── Tip carousel ───────────────────────────────────────────────────────────
    elif post_type == "tips":
        tips = post.tips if post.tips else [
            {"number": f"{i+1:02d}", "heading": s.get("heading",""), "body": s.get("body",""), "bonus": ""}
            for i, s in enumerate(post.slides)
        ]
        total = len(tips) + 2  # cover + tips + CTA

        cover_path = output_dir / "slide_00_cover.png"
        generate_tips_cover(
            tips_title=post.tips_title or post.hook or post.caption[:60],
            total_slides=total,
            brand_handle=handle,
            output_path=cover_path,
        )
        paths.append(str(cover_path))

        for idx, tip in enumerate(tips):
            slide_path = output_dir / f"slide_{idx + 1:02d}.png"
            generate_tips_slide(
                number=tip.get("number", f"{idx+1:02d}"),
                heading=tip.get("heading", ""),
                body=tip.get("body", ""),
                bonus=tip.get("bonus", ""),
                slide_num=idx + 2,
                total_slides=total,
                brand_handle=handle,
                output_path=slide_path,
            )
            paths.append(str(slide_path))

        cta_path = output_dir / f"slide_{len(tips) + 1:02d}_cta.png"
        generate_tips_cta(
            tips_cta=post.tips_cta or "Save this post for later!",
            brand_handle=handle,
            output_path=cta_path,
        )
        paths.append(str(cta_path))

    # ── Myth vs Fact ───────────────────────────────────────────────────────────
    elif post_type == "myth_fact":
        myth_path = output_dir / "slide_01_myth.png"
        generate_myth_slide(
            myth=post.myth or (post.slides[0].get("body","") if post.slides else post.hook),
            brand_handle=handle,
            output_path=myth_path,
        )
        paths.append(str(myth_path))

        fact_path = output_dir / "slide_02_fact.png"
        generate_fact_slide(
            fact_headline=post.fact_headline or (post.slides[1].get("heading","") if len(post.slides) > 1 else "The Truth"),
            fact_body=post.fact_body or (post.slides[1].get("body","") if len(post.slides) > 1 else post.caption[:200]),
            brand_handle=handle,
            output_path=fact_path,
        )
        paths.append(str(fact_path))

    # ── Quote card ─────────────────────────────────────────────────────────────
    elif post_type == "quote":
        out = output_dir / "post.png"
        generate_quote_card(
            quote_text=post.quote_text or post.hook,
            quote_attribution=post.quote_attribution or config.BRAND_NAME,
            quote_context=post.quote_context or "",
            brand_handle=handle,
            output_path=out,
        )
        paths.append(str(out))

    # ── Fallback: treat as tips carousel ──────────────────────────────────────
    else:
        total = len(post.slides) + 1
        cover_path = output_dir / "slide_00_cover.png"
        generate_tips_cover(
            tips_title=post.hook or post.caption[:60],
            total_slides=total,
            brand_handle=handle,
            output_path=cover_path,
        )
        paths.append(str(cover_path))

        for idx, slide in enumerate(post.slides):
            slide_path = output_dir / f"slide_{idx + 1:02d}.png"
            generate_tips_slide(
                number=f"{idx+1:02d}",
                heading=slide.get("heading", ""),
                body=slide.get("body", ""),
                bonus="",
                slide_num=idx + 2,
                total_slides=total,
                brand_handle=handle,
                output_path=slide_path,
            )
            paths.append(str(slide_path))

    return paths


# ── Canva (optional, when template IDs are configured) ───────────────────────


def _create_with_canva(
    post: GeneratedPost,
    post_id: int,
    output_dir: Path,
    client=None,
) -> list[str]:
    from designer.canva_client import CanvaClient

    if client is None:
        client = CanvaClient()

    if post.format == "carousel" and post.slides:
        return _canva_carousel(post, post_id, output_dir, client)
    else:
        return _canva_single(post, post_id, output_dir, client)


def _canva_single(post, post_id, output_dir, client) -> list[str]:
    template_id = config.CANVA_SINGLE_POST_TEMPLATE_ID
    design_id = client.create_design_from_template(template_id)

    fields = [
        {"name": "hook",            "type": "text", "text": post.hook},
        {"name": "caption_preview", "type": "text", "text": post.caption[:120]},
        {"name": "brand_handle",    "type": "text", "text": config.INSTAGRAM_HANDLE},
    ]
    client.autofill_design(design_id, fields)

    output_path = output_dir / "post.png"
    client.export_design_as_png(design_id, output_path)
    return [str(output_path)]


def _canva_carousel(post, post_id, output_dir, client) -> list[str]:
    template_id = config.CANVA_CAROUSEL_TEMPLATE_ID or config.CANVA_SINGLE_POST_TEMPLATE_ID
    paths: list[str] = []

    for idx, slide in enumerate(post.slides):
        design_id = client.create_design_from_template(template_id)
        fields = [
            {"name": "slide_heading", "type": "text", "text": slide.get("heading", "")},
            {"name": "slide_body",    "type": "text", "text": slide.get("body", "")},
            {"name": "slide_number",  "type": "text", "text": f"{idx + 1}/{len(post.slides)}"},
            {"name": "brand_handle",  "type": "text", "text": config.INSTAGRAM_HANDLE},
        ]
        client.autofill_design(design_id, fields)
        output_path = output_dir / f"slide_{idx + 1:02d}.png"
        client.export_design_as_png(design_id, output_path)
        paths.append(str(output_path))

    return paths
