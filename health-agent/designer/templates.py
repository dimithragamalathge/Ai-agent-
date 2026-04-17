"""
Template selection and design creation logic.
Routes each post_type to the correct image generator functions.
"""

import logging
from pathlib import Path

import config
from processor.generator import GeneratedPost

logger = logging.getLogger(__name__)


def create_post_images(post: GeneratedPost, post_id: int, client=None) -> list[str]:
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
        logger.info("Using Pillow generator for post %d (type: %s)", post_id, post.post_type)
        return _create_with_pillow(post, post_id, output_dir)


# ── Pillow generator ──────────────────────────────────────────────────────────

def _create_with_pillow(post: GeneratedPost, post_id: int, output_dir: Path) -> list[str]:
    from designer.image_generator import (
        generate_hook_slide,
        generate_clinical_reality_slide,
        generate_chart_breakdown_slide,
        generate_text_breakdown_slide,
        generate_prevention_slide,
        generate_cta_slide,
        generate_stat_card,
        generate_quote_card,
        generate_myth_slide,
        generate_fact_slide,
    )

    handle   = config.INSTAGRAM_HANDLE
    paths: list[str] = []
    post_type = getattr(post, "post_type", "tips")

    # ── Stat card (single image) ───────────────────────────────────────────────
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

    # ── Tips — 7-slide carousel ────────────────────────────────────────────────
    elif post_type == "tips":
        breakdown = post.breakdown_slides or []
        # Total slides: hook + clinical reality + breakdown slides + prevention + CTA
        total = 2 + len(breakdown) + 2

        # Slide 1: Hook
        p = output_dir / "slide_01_hook.png"
        generate_hook_slide(post.hook or post.caption[:60], total, handle, p)
        paths.append(str(p))

        # Slide 2: Clinical Reality
        p = output_dir / "slide_02_reality.png"
        generate_clinical_reality_slide(
            post.clinical_reality or post.caption[:300],
            2, total, handle, p,
        )
        paths.append(str(p))

        # Slides 3-N: Breakdown (chart or text)
        for idx, bd in enumerate(breakdown):
            slide_num = idx + 3
            p = output_dir / f"slide_{slide_num:02d}_breakdown.png"
            if bd.get("type") == "bar_chart":
                generate_chart_breakdown_slide(
                    title=bd.get("title", ""),
                    takeaway=bd.get("takeaway", ""),
                    categories=bd.get("categories", []),
                    values=bd.get("values", []),
                    highlight_index=bd.get("highlight_index", 0),
                    slide_num=slide_num, total=total,
                    brand_handle=handle, output_path=p,
                )
            else:
                generate_text_breakdown_slide(
                    heading=bd.get("heading", ""),
                    body=bd.get("body", ""),
                    slide_num=slide_num, total=total,
                    brand_handle=handle, output_path=p,
                )
            paths.append(str(p))

        # Prevention slide
        p = output_dir / f"slide_{total - 1:02d}_prevention.png"
        generate_prevention_slide(
            bullets=post.prevention_bullets or ["Consult your doctor",
                                                "Track your symptoms",
                                                "Make small daily changes"],
            slide_num=total - 1, total=total,
            brand_handle=handle, output_path=p,
        )
        paths.append(str(p))

        # CTA + Disclaimer
        p = output_dir / f"slide_{total:02d}_cta.png"
        generate_cta_slide(
            cta_text=post.cta_text or "Save this post 📌",
            disclaimer=post.disclaimer or "For educational purposes only. Consult your doctor.",
            brand_handle=handle, output_path=p,
        )
        paths.append(str(p))

    # ── Myth vs Fact (2 slides) ────────────────────────────────────────────────
    elif post_type == "myth_fact":
        p = output_dir / "slide_01_myth.png"
        generate_myth_slide(
            myth=post.myth or (post.slides[0].get("body", "") if post.slides else post.hook),
            brand_handle=handle, output_path=p,
        )
        paths.append(str(p))

        p = output_dir / "slide_02_fact.png"
        generate_fact_slide(
            fact_headline=post.fact_headline or "The Truth",
            fact_body=post.fact_body or (post.slides[1].get("body", "") if len(post.slides) > 1 else post.caption[:300]),
            brand_handle=handle, output_path=p,
        )
        paths.append(str(p))

    # ── Quote card (single image) ──────────────────────────────────────────────
    elif post_type == "quote":
        p = output_dir / "post.png"
        generate_quote_card(
            quote_text=post.quote_text or post.hook,
            quote_attribution=post.quote_attribution or config.BRAND_NAME,
            quote_context=post.quote_context or "",
            brand_handle=handle, output_path=p,
        )
        paths.append(str(p))

    # ── Fallback ───────────────────────────────────────────────────────────────
    else:
        total = len(post.slides) + 1
        p = output_dir / "slide_01_hook.png"
        generate_hook_slide(post.hook or post.caption[:60], total, handle, p)
        paths.append(str(p))
        for idx, slide in enumerate(post.slides):
            p = output_dir / f"slide_{idx + 2:02d}.png"
            generate_text_breakdown_slide(
                heading=slide.get("heading", ""),
                body=slide.get("body", ""),
                slide_num=idx + 2, total=total,
                brand_handle=handle, output_path=p,
            )
            paths.append(str(p))

    return paths


# ── Canva (optional) ──────────────────────────────────────────────────────────

def _create_with_canva(post: GeneratedPost, post_id: int, output_dir: Path, client=None) -> list[str]:
    from designer.canva_client import CanvaClient
    if client is None:
        client = CanvaClient()
    if post.format == "carousel" and post.slides:
        return _canva_carousel(post, post_id, output_dir, client)
    return _canva_single(post, post_id, output_dir, client)


def _canva_single(post, post_id, output_dir, client) -> list[str]:
    design_id = client.create_design_from_template(config.CANVA_SINGLE_POST_TEMPLATE_ID)
    client.autofill_design(design_id, [
        {"name": "hook",            "type": "text", "text": post.hook},
        {"name": "caption_preview", "type": "text", "text": post.caption[:120]},
        {"name": "brand_handle",    "type": "text", "text": config.INSTAGRAM_HANDLE},
    ])
    out = output_dir / "post.png"
    client.export_design_as_png(design_id, out)
    return [str(out)]


def _canva_carousel(post, post_id, output_dir, client) -> list[str]:
    template_id = config.CANVA_CAROUSEL_TEMPLATE_ID or config.CANVA_SINGLE_POST_TEMPLATE_ID
    paths = []
    for idx, slide in enumerate(post.slides):
        design_id = client.create_design_from_template(template_id)
        client.autofill_design(design_id, [
            {"name": "slide_heading", "type": "text", "text": slide.get("heading", "")},
            {"name": "slide_body",    "type": "text", "text": slide.get("body", "")},
            {"name": "slide_number",  "type": "text", "text": f"{idx + 1}/{len(post.slides)}"},
            {"name": "brand_handle",  "type": "text", "text": config.INSTAGRAM_HANDLE},
        ])
        out = output_dir / f"slide_{idx + 1:02d}.png"
        client.export_design_as_png(design_id, out)
        paths.append(str(out))
    return paths
