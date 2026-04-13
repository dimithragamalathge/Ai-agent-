"""
APScheduler-based pipeline scheduler.
Runs the full content pipeline on Mon/Wed/Fri at the configured time.
"""

import logging
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

import config
from utils.helpers import configure_logging

logger = logging.getLogger(__name__)


def run_full_pipeline() -> None:
    """
    Execute the complete content generation pipeline:
    1. Scrape health articles from all sources
    2. Use Claude to select the 3 most engaging articles
    3. Use Claude to generate Instagram content for each
    4. Use Canva to create and export designed images
    5. Save posts to the database with status 'draft'

    After this runs, open the dashboard to review and publish.
    """
    from scraper.rss import fetch_all_rss
    from scraper.pubmed import fetch_all_pubmed
    from processor.selector import select_best_articles
    from processor.generator import generate_post
    from designer.templates import create_post_images
    from designer.canva_client import CanvaClient
    from database.db import get_session, init_db
    from database.models import Article, Post

    init_db()
    logger.info("=" * 60)
    logger.info("Pipeline started at %s", datetime.now().strftime("%Y-%m-%d %H:%M"))
    logger.info("=" * 60)

    # ── 1. Scrape ──────────────────────────────────────────────────────────
    logger.info("Step 1/5: Scraping health articles…")
    with get_session() as db:
        existing_urls = {a.url for a in db.query(Article.url).all()}

    rss_articles = fetch_all_rss(existing_urls=existing_urls)
    pubmed_articles = fetch_all_pubmed(existing_urls=existing_urls | {a.url for a in rss_articles})
    all_scraped = rss_articles + pubmed_articles

    logger.info("Scraped %d new articles total", len(all_scraped))

    if not all_scraped:
        logger.warning("No new articles found — skipping this pipeline run")
        return

    # ── 2. Save articles to DB ─────────────────────────────────────────────
    with get_session() as db:
        for a in all_scraped:
            db.add(Article(
                url=a.url,
                title=a.title,
                summary=a.summary,
                source=a.source,
                topic=a.topic,
                scraped_at=a.scraped_at,
            ))
    logger.info("Saved %d articles to database", len(all_scraped))

    # ── 3. Select best articles ────────────────────────────────────────────
    logger.info("Step 2/5: Asking Claude to select the best articles…")
    selected = select_best_articles(all_scraped, n=3)
    logger.info("Claude selected %d articles", len(selected))

    # ── 4. Generate content + design ──────────────────────────────────────
    canva_client = CanvaClient() if (config.CANVA_CLIENT_ID and config.CANVA_ACCESS_TOKEN) else None
    posts_created = 0

    for article in selected:
        logger.info("Step 3/5: Generating content for: %s", article.title[:60])
        try:
            post_content = generate_post(article)
        except Exception as exc:
            logger.error("Content generation failed for %r: %s", article.title, exc)
            continue

        # Mark article as used
        with get_session() as db:
            db_article = db.query(Article).filter_by(url=article.url).first()
            if db_article:
                db_article.used = True
                article_id = db_article.id
            else:
                article_id = None

        # Create post record (without images first)
        with get_session() as db:
            post = Post(
                article_id=article_id,
                format=post_content.format,
                hook=post_content.hook,
                caption=post_content.caption,
                status="draft",
            )
            post.set_hashtags(post_content.hashtags)
            post.set_slide_texts(post_content.slides)
            db.add(post)
            db.flush()
            post_id = post.id

        # ── 5. Generate Canva images ───────────────────────────────────────
        image_paths: list[str] = []
        if canva_client:
            logger.info("Step 4/5: Creating Canva design for post %d…", post_id)
            try:
                image_paths = create_post_images(post_content, post_id, client=canva_client)
                logger.info("Created %d image(s) for post %d", len(image_paths), post_id)
            except Exception as exc:
                logger.error("Canva design failed for post %d: %s", post_id, exc)
        else:
            logger.warning("Canva not configured — post %d has no images", post_id)

        # Save image paths back to the post
        with get_session() as db:
            post = db.query(Post).filter_by(id=post_id).first()
            if post:
                post.set_image_paths(image_paths)

        posts_created += 1
        logger.info("Post %d ready for review", post_id)

    logger.info("=" * 60)
    logger.info(
        "Pipeline complete: %d post(s) added to review queue",
        posts_created,
    )
    logger.info("Open the dashboard to review: python main.py dashboard")
    logger.info("=" * 60)


def start_scheduler() -> None:
    """Start the APScheduler and block until interrupted."""
    configure_logging()
    scheduler = BlockingScheduler(timezone="local")

    # Parse schedule from config  e.g. "mon,wed,fri" and "08:00"
    days = config.SCHEDULE_DAYS.strip()
    hour, minute = config.SCHEDULE_TIME.strip().split(":")

    trigger = CronTrigger(
        day_of_week=days,
        hour=int(hour),
        minute=int(minute),
    )

    scheduler.add_job(
        run_full_pipeline,
        trigger=trigger,
        id="health_pipeline",
        name="Health Content Pipeline",
        misfire_grace_time=3600,
    )

    next_run = scheduler.get_jobs()[0].next_run_time
    logger.info("Scheduler started. Next run: %s", next_run)
    logger.info("Schedule: %s at %s:%s", days, hour, minute)
    logger.info("Press Ctrl+C to stop.")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")
