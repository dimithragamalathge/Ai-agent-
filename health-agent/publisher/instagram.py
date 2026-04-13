"""
Instagram Graph API publisher.

Supports:
- Single image posts
- Carousel posts (multiple images)

Prerequisites:
- Instagram Business or Creator account linked to a Facebook Page
- Facebook App with instagram_business_content_publish permission
- Long-lived User Access Token (valid 60 days)
- Instagram User ID

Full setup guide in README.md.
"""

import logging
import time
from pathlib import Path

import requests

import config

logger = logging.getLogger(__name__)

GRAPH_BASE = config.INSTAGRAM_API_BASE


def _api_get(path: str, params: dict | None = None) -> dict:
    params = params or {}
    params["access_token"] = config.INSTAGRAM_ACCESS_TOKEN
    resp = requests.get(f"{GRAPH_BASE}/{path}", params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def _api_post(path: str, data: dict | None = None) -> dict:
    data = data or {}
    data["access_token"] = config.INSTAGRAM_ACCESS_TOKEN
    resp = requests.post(f"{GRAPH_BASE}/{path}", data=data, timeout=15)
    resp.raise_for_status()
    return resp.json()


def _wait_for_container(container_id: str, timeout: int = 120) -> None:
    """Poll until a media container reaches FINISHED status."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        resp = _api_get(container_id, params={"fields": "status_code,status"})
        status = resp.get("status_code", "")
        if status == "FINISHED":
            return
        if status == "ERROR":
            raise RuntimeError(
                f"Instagram container {container_id} failed: {resp.get('status')}"
            )
        logger.debug("Container %s status: %s — waiting…", container_id, status)
        time.sleep(5)
    raise TimeoutError(f"Instagram container {container_id} did not finish in time")


def _build_caption(caption: str, hashtags: list[str]) -> str:
    """Combine caption and hashtags into the final Instagram text."""
    tag_string = " ".join(hashtags)
    return f"{caption}\n\n.\n.\n.\n{tag_string}"


def _get_public_url(image_path: str) -> str:
    """
    Instagram Graph API requires a publicly accessible image URL.

    During development: host images on a free service like Imgur or use
    the Canva export URL directly (already public).

    If image_path starts with http(s), return it as-is (e.g. Canva URLs).
    Otherwise raise a helpful error guiding the user.
    """
    if image_path.startswith("http://") or image_path.startswith("https://"):
        return image_path

    raise ValueError(
        f"Instagram requires a public URL for images, but got a local path: {image_path}\n"
        "Options:\n"
        "  1. Use Canva export URLs directly (already public) — recommended\n"
        "  2. Upload to Imgur: https://api.imgur.com/3/image\n"
        "  3. Use any public image hosting service\n"
        "Set INSTAGRAM_IMAGE_HOST in config if needed."
    )


# ─── Main publish functions ───────────────────────────────────────────────────


def publish_single_post(
    image_path: str,
    caption: str,
    hashtags: list[str],
) -> str:
    """
    Publish a single-image Instagram post.
    Returns the Instagram media ID of the published post.
    """
    if not config.INSTAGRAM_USER_ID or not config.INSTAGRAM_ACCESS_TOKEN:
        raise EnvironmentError(
            "INSTAGRAM_USER_ID and INSTAGRAM_ACCESS_TOKEN must be set in .env"
        )

    full_caption = _build_caption(caption, hashtags)
    image_url = _get_public_url(image_path)

    # Step 1: Create media container
    container = _api_post(
        f"{config.INSTAGRAM_USER_ID}/media",
        data={
            "image_url": image_url,
            "caption": full_caption,
        },
    )
    container_id = container.get("id")
    if not container_id:
        raise RuntimeError(f"Failed to create media container: {container}")

    logger.info("Created media container: %s", container_id)

    # Step 2: Wait for processing
    _wait_for_container(container_id)

    # Step 3: Publish
    result = _api_post(
        f"{config.INSTAGRAM_USER_ID}/media_publish",
        data={"creation_id": container_id},
    )
    media_id = result.get("id")
    logger.info("Published single post: %s", media_id)
    return media_id


def publish_carousel_post(
    image_paths: list[str],
    caption: str,
    hashtags: list[str],
) -> str:
    """
    Publish a carousel (multi-image) Instagram post.
    Returns the Instagram media ID of the published carousel.
    """
    if not config.INSTAGRAM_USER_ID or not config.INSTAGRAM_ACCESS_TOKEN:
        raise EnvironmentError(
            "INSTAGRAM_USER_ID and INSTAGRAM_ACCESS_TOKEN must be set in .env"
        )

    if not 2 <= len(image_paths) <= 10:
        raise ValueError(f"Carousel requires 2–10 images, got {len(image_paths)}")

    full_caption = _build_caption(caption, hashtags)

    # Step 1: Create a container for each slide image
    child_ids: list[str] = []
    for idx, path in enumerate(image_paths):
        image_url = _get_public_url(path)
        container = _api_post(
            f"{config.INSTAGRAM_USER_ID}/media",
            data={
                "image_url": image_url,
                "is_carousel_item": "true",
            },
        )
        container_id = container.get("id")
        if not container_id:
            raise RuntimeError(f"Failed to create carousel item container for slide {idx+1}")
        logger.info("Created carousel item container %d: %s", idx + 1, container_id)
        _wait_for_container(container_id)
        child_ids.append(container_id)

    # Step 2: Create the carousel container
    carousel = _api_post(
        f"{config.INSTAGRAM_USER_ID}/media",
        data={
            "media_type": "CAROUSEL",
            "caption": full_caption,
            "children": ",".join(child_ids),
        },
    )
    carousel_id = carousel.get("id")
    if not carousel_id:
        raise RuntimeError(f"Failed to create carousel container: {carousel}")

    logger.info("Created carousel container: %s", carousel_id)
    _wait_for_container(carousel_id)

    # Step 3: Publish the carousel
    result = _api_post(
        f"{config.INSTAGRAM_USER_ID}/media_publish",
        data={"creation_id": carousel_id},
    )
    media_id = result.get("id")
    logger.info("Published carousel post: %s", media_id)
    return media_id


def publish_post(
    image_paths: list[str],
    caption: str,
    hashtags: list[str],
    post_format: str = "single",
) -> str:
    """
    Unified publish function. Dispatches to single or carousel based on format.
    Returns the Instagram media ID.
    """
    if post_format == "carousel" and len(image_paths) > 1:
        return publish_carousel_post(image_paths, caption, hashtags)
    else:
        return publish_single_post(image_paths[0], caption, hashtags)


def get_account_info() -> dict:
    """Verify the token works and return basic account info."""
    return _api_get(
        config.INSTAGRAM_USER_ID,
        params={"fields": "id,username,account_type,media_count"},
    )


def refresh_long_lived_token() -> str:
    """
    Refresh a long-lived token before it expires (valid 60 days).
    Should be called every ~50 days.
    Returns the new token.
    """
    resp = requests.get(
        "https://graph.instagram.com/refresh_access_token",
        params={
            "grant_type": "ig_refresh_token",
            "access_token": config.INSTAGRAM_ACCESS_TOKEN,
        },
        timeout=15,
    )
    resp.raise_for_status()
    new_token = resp.json().get("access_token", "")
    logger.info("Instagram access token refreshed successfully")
    return new_token
