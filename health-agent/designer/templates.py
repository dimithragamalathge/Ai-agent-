"""
Template selection and design creation logic.

Orchestrates the full Canva pipeline:
  1. Pick the right template (single vs carousel)
  2. Create a design from the template
  3. Autofill text fields
  4. Export PNG(s) to disk
  5. Return local file paths
"""

import logging
from pathlib import Path

import config
from designer.canva_client import CanvaClient
from processor.generator import GeneratedPost

logger = logging.getLogger(__name__)


def _slugify(text: str, max_len: int = 40) -> str:
    import re
    text = re.sub(r"[^\w\s-]", "", text.lower())
    text = re.sub(r"[\s_-]+", "-", text).strip("-")
    return text[:max_len]


def create_post_images(
    post: GeneratedPost,
    post_id: int,
    client: CanvaClient | None = None,
) -> list[str]:
    """
    Given a GeneratedPost, produce PNG images via Canva and return their paths.

    For single posts  → returns ["/path/to/image.png"]
    For carousels     → returns ["/path/slide_1.png", "/path/slide_2.png", ...]
    """
    if client is None:
        client = CanvaClient()

    output_dir = config.OUTPUT_DIR / f"post_{post_id}"
    output_dir.mkdir(parents=True, exist_ok=True)

    if post.format == "carousel":
        return _create_carousel_images(post, post_id, output_dir, client)
    else:
        return _create_single_image(post, post_id, output_dir, client)


def _create_single_image(
    post: GeneratedPost,
    post_id: int,
    output_dir: Path,
    client: CanvaClient,
) -> list[str]:
    template_id = config.CANVA_SINGLE_POST_TEMPLATE_ID
    if not template_id:
        logger.warning("CANVA_SINGLE_POST_TEMPLATE_ID not set — skipping Canva design")
        return []

    design_id = client.create_design_from_template(template_id)
    logger.info("Created Canva design %s from single-post template", design_id)

    # Autofill the template text fields
    # Field names must match what you named them in your Canva template
    fields = [
        {"name": "hook", "type": "text", "text": post.hook},
        {"name": "caption_preview", "type": "text", "text": post.caption[:120]},
        {"name": "brand_handle", "type": "text", "text": config.INSTAGRAM_HANDLE},
    ]
    client.autofill_design(design_id, fields)

    output_path = output_dir / "post.png"
    client.export_design_as_png(design_id, output_path)
    return [str(output_path)]


def _create_carousel_images(
    post: GeneratedPost,
    post_id: int,
    output_dir: Path,
    client: CanvaClient,
) -> list[str]:
    template_id = config.CANVA_CAROUSEL_TEMPLATE_ID
    if not template_id:
        logger.warning("CANVA_CAROUSEL_TEMPLATE_ID not set — skipping Canva design")
        return []

    slides = post.slides
    if not slides:
        # Fall back to single if no slide data
        return _create_single_image(post, post_id, output_dir, client)

    paths: list[str] = []

    for idx, slide in enumerate(slides):
        design_id = client.create_design_from_template(template_id)
        logger.info("Created carousel slide %d design %s", idx + 1, design_id)

        fields = [
            {"name": "slide_heading", "type": "text", "text": slide.get("heading", "")},
            {"name": "slide_body", "type": "text", "text": slide.get("body", "")},
            {"name": "slide_number", "type": "text", "text": f"{idx + 1}/{len(slides)}"},
            {"name": "brand_handle", "type": "text", "text": config.INSTAGRAM_HANDLE},
        ]
        client.autofill_design(design_id, fields)

        output_path = output_dir / f"slide_{idx + 1:02d}.png"
        client.export_design_as_png(design_id, output_path)
        paths.append(str(output_path))

    return paths
