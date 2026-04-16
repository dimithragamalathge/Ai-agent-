"""
RSS feed scraper using feedparser.
Works for Healthline, WHO, NIH, Medical News Today, Harvard Health, WebMD, etc.
"""

import logging
import feedparser

from scraper.base import BaseScraper, ScrapedArticle
from scraper.sources import FeedSource

logger = logging.getLogger(__name__)


class RSScraper(BaseScraper):
    """Fetches articles from a single RSS/Atom feed."""

    def __init__(self, source: FeedSource) -> None:
        super().__init__(source_name=source.name, topic=source.topic)
        self.feed_url = source.url
        self.max_articles = source.max_articles

    def _fetch_raw(self) -> list[ScrapedArticle]:
        feed = feedparser.parse(self.feed_url)

        if feed.bozo and not feed.entries:
            logger.warning("Feed parse issue for %s: %s", self.feed_url, feed.bozo_exception)
            return []

        articles: list[ScrapedArticle] = []
        for entry in feed.entries[: self.max_articles]:
            url = entry.get("link", "")
            title = entry.get("title", "")
            if not url or not title:
                continue

            summary = (
                entry.get("summary")
                or entry.get("description")
                or entry.get("content", [{}])[0].get("value", "")
                or ""
            )
            summary = self._clean_text(summary)[:800]

            articles.append(
                ScrapedArticle(
                    url=url,
                    title=self._clean_text(title),
                    summary=summary,
                    source=self.source_name,
                    topic=self.topic,
                )
            )

        return articles


def fetch_all_rss(existing_urls: set[str] | None = None) -> list[ScrapedArticle]:
    """Convenience function: scrape every configured RSS source."""
    from scraper.sources import RSS_SOURCES

    all_articles: list[ScrapedArticle] = []
    seen_urls = existing_urls or set()

    for source in RSS_SOURCES:
        scraper = RSScraper(source)
        new = scraper.fetch(existing_urls=seen_urls)
        seen_urls.update(a.url for a in new)
        all_articles.extend(new)

    return all_articles
