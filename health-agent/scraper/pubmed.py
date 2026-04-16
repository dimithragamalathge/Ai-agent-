"""
PubMed E-utilities scraper.
Free API — no scraping involved. Optionally uses a free API key for higher rate limits.
Register for a free key at: https://www.ncbi.nlm.nih.gov/account/
"""

import logging
import time
import requests

import config
from scraper.base import BaseScraper, ScrapedArticle
from scraper.sources import PUBMED_QUERIES

logger = logging.getLogger(__name__)

ESEARCH_URL = f"{config.PUBMED_BASE_URL}/esearch.fcgi"
EFETCH_URL = f"{config.PUBMED_BASE_URL}/efetch.fcgi"
ESUMMARY_URL = f"{config.PUBMED_BASE_URL}/esummary.fcgi"


class PubMedScraper(BaseScraper):
    """Fetches latest PubMed articles for a given query."""

    RATE_LIMIT_SECONDS = 0.34  # 3 req/s without key; overridden if key present

    def __init__(self, query: str, topic: str, max_results: int = 3) -> None:
        super().__init__(source_name="pubmed", topic=topic)
        self.query = query
        self.max_results = max_results
        if config.PUBMED_API_KEY:
            self.RATE_LIMIT_SECONDS = 0.11  # 10 req/s with key

    def _fetch_raw(self) -> list[ScrapedArticle]:
        # Step 1: search for IDs
        params = {
            "db": "pubmed",
            "term": self.query,
            "retmax": self.max_results,
            "sort": "pub+date",
            "retmode": "json",
            "datetype": "pdat",
            "reldate": 60,  # Last 60 days
        }
        if config.PUBMED_API_KEY:
            params["api_key"] = config.PUBMED_API_KEY

        resp = requests.get(ESEARCH_URL, params=params, timeout=10)
        resp.raise_for_status()
        ids = resp.json().get("esearchresult", {}).get("idlist", [])

        if not ids:
            return []

        time.sleep(self.RATE_LIMIT_SECONDS)

        # Step 2: fetch summaries for those IDs
        summary_params = {
            "db": "pubmed",
            "id": ",".join(ids),
            "retmode": "json",
        }
        if config.PUBMED_API_KEY:
            summary_params["api_key"] = config.PUBMED_API_KEY

        resp = requests.get(ESUMMARY_URL, params=summary_params, timeout=10)
        resp.raise_for_status()
        result = resp.json().get("result", {})

        articles: list[ScrapedArticle] = []
        for pmid in ids:
            entry = result.get(pmid, {})
            title = entry.get("title", "").strip()
            if not title:
                continue

            authors = entry.get("authors", [])
            author_str = authors[0].get("name", "") if authors else ""
            source_journal = entry.get("source", "PubMed")
            pub_date = entry.get("pubdate", "")

            summary = (
                f"Published in {source_journal} ({pub_date}). "
                f"Author(s): {author_str}. "
                f"PubMed ID: {pmid}."
            )

            url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

            articles.append(
                ScrapedArticle(
                    url=url,
                    title=title,
                    summary=summary,
                    source="pubmed",
                    topic=self.topic,
                )
            )

        return articles


def fetch_all_pubmed(existing_urls: set[str] | None = None) -> list[ScrapedArticle]:
    """Convenience function: run all configured PubMed queries."""
    all_articles: list[ScrapedArticle] = []
    seen_urls = existing_urls or set()

    for q in PUBMED_QUERIES:
        scraper = PubMedScraper(
            query=q["query"],
            topic=q["topic"],
            max_results=q["max_results"],
        )
        new = scraper.fetch(existing_urls=seen_urls)
        seen_urls.update(a.url for a in new)
        all_articles.extend(new)

    return all_articles
