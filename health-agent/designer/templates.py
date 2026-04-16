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
        logger.info("Using Pillow image generator for post %d", post_id)
        return _create_with_pillow(post, post_id, output_dir)


# ── Pillow generator (default) ────────────────────────────────────────────────


def _create_with_pillow(
    post: GeneratedPost,
    post_id: int,
    output_dir: Path,
) -> list[str]:
    from designer.image_generator import (
        generate_single_post,
        generate_carousel_cover,
        generate_carousel_slide,
    )

    handle = config.INSTAGRAM_HANDLE
    paths: list[str] = []

    if post.format == "carousel" and post.slides:
        total = len(post.slides) + 1  # cover + content slides

        # Cover slide
        cover_path = output_dir / "slide_00_cover.png"
        generate_carousel_cover(
            hook=post.hook or post.caption[:80],
            total_slides=total,
            brand_handle=handle,
            output_path=cover_path,
        )
        paths.append(str(cover_path))

        # Content slides
        for idx, slide in enumerate(post.slides):
            slide_path = output_dir / f"slide_{idx + 1:02d}.png"
            generate_carousel_slide(
                heading=slide.get("heading", ""),
                body=slide.get("body", ""),
                slide_num=idx + 2,
                total_slides=total,
                brand_handle=handle,
                output_path=slide_path,
            )
            paths.append(str(slide_path))

    else:
        # Single post
        post_path = output_dir / "post.png"
        generate_single_post(
            hook=post.hook or post.caption[:80],
            caption_preview=post.caption[:140],
            brand_handle=handle,
            output_path=post_path,
        )
        paths.append(str(post_path))

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
