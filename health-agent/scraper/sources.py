"""
RSS feed sources and PubMed query configuration.

Topics covered:
  - Latest research (date-restricted)
  - Pathological basis of common diseases (evergreen)
  - Healthy lifestyle & prevention (evergreen)
  - General medical education (evergreen)
  - Mental health & wellbeing (evergreen)
  - Nutrition & diet (evergreen)
"""

from dataclasses import dataclass


@dataclass
class FeedSource:
    name: str
    url: str
    topic: str
    max_articles: int = 5


RSS_SOURCES: list[FeedSource] = [
    FeedSource("healthline",      "https://www.healthline.com/rss/health-news",                          "general_wellness",  5),
    FeedSource("nih_news",        "https://newsinhealth.nih.gov/feed",                                   "general_wellness",  4),
    FeedSource("harvard_health",  "https://www.health.harvard.edu/blog/feed",                            "general_wellness",  4),
    FeedSource("medical_news_today", "https://www.medicalnewstoday.com/rss/news",                        "medical_research",  5),
    FeedSource("who_news",        "https://www.who.int/rss-feeds/news-english.xml",                     "medical_research",  4),
    FeedSource("webmd_diet",      "https://rss.webmd.com/rss/rss.aspx?RSSSource=RSS_PUBLIC&rssid=723",  "nutrition",         4),
    FeedSource("healthline_nutrition", "https://www.healthline.com/rss/nutrition",                      "nutrition",         4),
    FeedSource("psychology_today","https://www.psychologytoday.com/us/front/feed",                      "mental_health",     4),
    FeedSource("webmd_mental",    "https://rss.webmd.com/rss/rss.aspx?RSSSource=RSS_PUBLIC&rssid=1821", "mental_health",     3),
]

# ── PubMed queries ────────────────────────────────────────────────────────────
# reldate (days) = only search recent articles; omit for evergreen/general topics.
# max_results: keep low (2-3) so the pool stays varied across many queries.

PUBMED_QUERIES: list[dict] = [

    # ── Latest research (date-restricted to keep content fresh) ───────────────
    {"query": "randomized controlled trial nutrition diet health 2024",
     "topic": "nutrition", "max_results": 2, "reldate": 180},

    {"query": "mental health depression anxiety treatment efficacy 2024",
     "topic": "mental_health", "max_results": 2, "reldate": 180},

    {"query": "preventive medicine lifestyle intervention clinical trial",
     "topic": "general_wellness", "max_results": 2, "reldate": 180},

    {"query": "cardiovascular disease prevention new findings",
     "topic": "heart_health", "max_results": 2, "reldate": 180},

    # ── Pathological basis of common diseases (evergreen — no date limit) ─────
    {"query": "diabetes mellitus type 2 pathophysiology insulin resistance review",
     "topic": "common_diseases", "max_results": 3},

    {"query": "hypertension pathophysiology mechanisms blood pressure review",
     "topic": "common_diseases", "max_results": 3},

    {"query": "atherosclerosis coronary artery disease pathology review",
     "topic": "heart_health", "max_results": 3},

    {"query": "asthma COPD pathophysiology airway inflammation review",
     "topic": "respiratory", "max_results": 2},

    {"query": "chronic kidney disease pathophysiology progression review",
     "topic": "common_diseases", "max_results": 2},

    {"query": "thyroid disorders hypothyroidism hyperthyroidism pathophysiology",
     "topic": "common_diseases", "max_results": 2},

    {"query": "obesity metabolic syndrome pathophysiology adipose tissue",
     "topic": "nutrition", "max_results": 2},

    {"query": "cancer carcinogenesis tumour biology hallmarks review",
     "topic": "medical_research", "max_results": 2},

    {"query": "stroke cerebrovascular disease pathophysiology ischemia review",
     "topic": "neurology", "max_results": 2},

    {"query": "autoimmune disease mechanism immune dysregulation review",
     "topic": "medical_research", "max_results": 2},

    {"query": "liver disease NAFLD cirrhosis pathophysiology review",
     "topic": "common_diseases", "max_results": 2},

    # ── Healthy lifestyle & prevention (evergreen) ────────────────────────────
    {"query": "physical exercise health benefits cardiovascular metabolic review",
     "topic": "lifestyle", "max_results": 3},

    {"query": "sleep quality health outcomes chronic disease review",
     "topic": "lifestyle", "max_results": 3},

    {"query": "stress management cortisol health effects review",
     "topic": "mental_health", "max_results": 2},

    {"query": "Mediterranean diet health outcomes review meta-analysis",
     "topic": "nutrition", "max_results": 2},

    {"query": "gut microbiome health disease review",
     "topic": "nutrition", "max_results": 2},

    {"query": "vitamin D deficiency health effects review",
     "topic": "nutrition", "max_results": 2},

    {"query": "smoking cessation health benefits lung cardiovascular",
     "topic": "lifestyle", "max_results": 2},

    {"query": "alcohol consumption health risks liver cardiovascular review",
     "topic": "lifestyle", "max_results": 2},

    # ── General medical education & common knowledge (evergreen) ──────────────
    {"query": "antibiotic resistance stewardship patient education review",
     "topic": "medical_education", "max_results": 2},

    {"query": "vaccine immunisation public health efficacy review",
     "topic": "medical_education", "max_results": 2},

    {"query": "pain management non-opioid analgesic review",
     "topic": "medical_education", "max_results": 2},

    {"query": "diabetes patient education self-management glycaemic control",
     "topic": "common_diseases", "max_results": 2},

    {"query": "hypertension patient education lifestyle blood pressure control",
     "topic": "common_diseases", "max_results": 2},

    {"query": "mental health stigma awareness patient education review",
     "topic": "mental_health", "max_results": 2},

    {"query": "cancer screening early detection benefit review",
     "topic": "medical_education", "max_results": 2},

    {"query": "first aid emergency recognition symptoms myocardial infarction stroke",
     "topic": "medical_education", "max_results": 2},
]
