"""
Claude-powered article selector.
Given a list of scraped articles, picks the 3 most Instagram-worthy ones.
"""

import json
import logging

import anthropic

import config
from scraper.base import ScrapedArticle

logger = logging.getLogger(__name__)

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client


SYSTEM_PROMPT = f"""You are a social media content strategist for a health and lifestyle
Instagram account called {config.BRAND_NAME}. Your job is to identify which health articles
will resonate most with an Instagram audience aged 25–45 who are health-conscious,
time-poor, and motivated by practical, science-backed advice.

You prioritise articles that:
- Have an immediately understandable, surprising, or actionable finding
- Cover topics people care about daily (food, sleep, stress, energy, longevity)
- Are grounded in science but explainable in simple language
- Have strong visual storytelling potential (could be turned into carousel slides)

You avoid articles that:
- Are too niche or technical for a general audience
- Cover tragic news without actionable takeaways
- Are opinion pieces with no scientific backing
"""


def select_best_articles(
    articles: list[ScrapedArticle], n: int = 3
) -> list[ScrapedArticle]:
    """
    Use Claude to select the `n` most engaging articles from the list.
    Returns the selected ScrapedArticle objects in ranked order.
    """
    if not articles:
        return []

    if len(articles) <= n:
        return articles

    # Build the article list for the prompt
    numbered = "\n".join(
        f"{i+1}. [{a.source.upper()}] {a.title}\n   {a.summary[:200]}"
        for i, a in enumerate(articles)
    )

    prompt = f"""Here are {len(articles)} recent health articles.
Select the best {n} for our Instagram audience and return ONLY a valid JSON object.

ARTICLES:
{numbered}

Return this exact JSON format (no markdown, no extra text):
{{
  "selected": [
    {{
      "index": <1-based article number>,
      "reason": "<one sentence why this will perform well on Instagram>"
    }}
  ]
}}

Select exactly {n} articles ranked by Instagram engagement potential (best first)."""

    client = _get_client()
    try:
        response = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=512,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        data = json.loads(raw)
        selected_indices = [item["index"] - 1 for item in data["selected"]]

        selected = []
        for idx in selected_indices:
            if 0 <= idx < len(articles):
                selected.append(articles[idx])

        logger.info("Claude selected %d articles from %d candidates", len(selected), len(articles))
        return selected

    except (json.JSONDecodeError, KeyError, IndexError) as exc:
        logger.error("Article selection parse error: %s — falling back to first %d", exc, n)
        return articles[:n]
    except anthropic.APIError as exc:
        logger.error("Claude API error during selection: %s", exc)
        return articles[:n]
