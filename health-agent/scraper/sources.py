"""
RSS feed sources and topic mapping.
Add or remove entries here to control which sites are scraped.
"""

from dataclasses import dataclass


@dataclass
class FeedSource:
    name: str           # Identifier used in the database
    url: str            # RSS feed URL
    topic: str          # Category label
    max_articles: int = 5  # Max articles to pull per run


RSS_SOURCES: list[FeedSource] = [
    # General health & wellness
    FeedSource(
        name="healthline",
        url="https://www.healthline.com/rss/health-news",
        topic="general_wellness",
        max_articles=5,
    ),
    FeedSource(
        name="nih_news",
        url="https://newsinhealth.nih.gov/feed",
        topic="general_wellness",
        max_articles=4,
    ),
    FeedSource(
        name="harvard_health",
        url="https://www.health.harvard.edu/blog/feed",
        topic="general_wellness",
        max_articles=4,
    ),
    # Medical research & news
    FeedSource(
        name="medical_news_today",
        url="https://www.medicalnewstoday.com/rss/news",
        topic="medical_research",
        max_articles=5,
    ),
    FeedSource(
        name="who_news",
        url="https://www.who.int/rss-feeds/news-english.xml",
        topic="medical_research",
        max_articles=4,
    ),
    # Nutrition & diet
    FeedSource(
        name="webmd_diet",
        url="https://rss.webmd.com/rss/rss.aspx?RSSSource=RSS_PUBLIC&rssid=723",
        topic="nutrition",
        max_articles=4,
    ),
    FeedSource(
        name="healthline_nutrition",
        url="https://www.healthline.com/rss/nutrition",
        topic="nutrition",
        max_articles=4,
    ),
    # Mental health
    FeedSource(
        name="psychology_today",
        url="https://www.psychologytoday.com/us/front/feed",
        topic="mental_health",
        max_articles=4,
    ),
    FeedSource(
        name="webmd_mental",
        url="https://rss.webmd.com/rss/rss.aspx?RSSSource=RSS_PUBLIC&rssid=1821",
        topic="mental_health",
        max_articles=3,
    ),
]

# PubMed search terms mapped to topics
PUBMED_QUERIES: list[dict] = [
    {"query": "nutrition diet health randomized trial", "topic": "nutrition", "max_results": 3},
    {"query": "mental health depression anxiety treatment", "topic": "mental_health", "max_results": 3},
    {"query": "preventive medicine wellness lifestyle", "topic": "general_wellness", "max_results": 3},
    {"query": "clinical trial disease treatment breakthrough", "topic": "medical_research", "max_results": 3},
]
