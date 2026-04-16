"""
Base scraper class with rate limiting and deduplication helpers.
"""

import time
import logging
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ScrapedArticle:
    """Plain data object representing one scraped article."""
    url: str
    title: str
    summary: str
    source: str
    topic: str
    scraped_at: datetime = field(default_factory=datetime.utcnow)


class BaseScraper:
    """
    Base class for all scrapers.
    Subclasses implement `_fetch_raw()` and call `fetch()`.
    """

    # Seconds to wait between requests to the same host
    RATE_LIMIT_SECONDS: float = 1.5

    def __init__(self, source_name: str, topic: str) -> None:
        self.source_name = source_name
        self.topic = topic
        self._last_request_time: float = 0.0

    def _rate_limit(self) -> None:
        elapsed = time.time() - self._last_request_time
        if elapsed < self.RATE_LIMIT_SECONDS:
            time.sleep(self.RATE_LIMIT_SECONDS - elapsed)
        self._last_request_time = time.time()

    def _clean_text(self, text: str) -> str:
        """Strip HTML tags and excessive whitespace from text."""
        import re
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def fetch(self, existing_urls: set[str] | None = None) -> list[ScrapedArticle]:
        """
        Fetch articles, skipping any whose URLs are in `existing_urls`.
        Returns a list of new ScrapedArticle objects.
        """
        existing_urls = existing_urls or set()
        self._rate_limit()
        try:
            articles = self._fetch_raw()
        except Exception as exc:
            logger.error("Scraper %s failed: %s", self.source_name, exc)
            return []

        new_articles = [a for a in articles if a.url not in existing_urls]
        logger.info(
            "Scraper %s: %d fetched, %d new",
            self.source_name, len(articles), len(new_articles),
        )
        return new_articles

    def _fetch_raw(self) -> list[ScrapedArticle]:
        raise NotImplementedError
