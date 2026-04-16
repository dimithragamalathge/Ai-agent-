"""
Claude-powered Instagram content generator.
Takes a single article and returns a fully structured post ready for design.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Any

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


@dataclass
class GeneratedPost:
    """All content needed to create one Instagram post."""
    post_type: str                       # "stat" | "tips" | "myth_fact" | "quote"
    format: str                          # "single" | "carousel"
    hook: str                            # Short attention-grabbing first line
    caption: str                         # Full Instagram caption (150–200 words)
    hashtags: list[str]                  # 20 hashtags
    slides: list[dict] = field(default_factory=list)
    content_warning: str | None = None

    # stat fields
    stat_number: str = ""
    stat_label: str = ""
    stat_context: str = ""
    stat_source: str = ""

    # tips fields
    tips_title: str = ""
    tips: list[dict] = field(default_factory=list)   # [{number, heading, body, bonus}]
    tips_cta: str = ""

    # myth_fact fields
    myth: str = ""
    fact_headline: str = ""
    fact_body: str = ""

    # quote fields
    quote_text: str = ""
    quote_attribution: str = ""
    quote_context: str = ""


SYSTEM_PROMPT = f"""You are an expert Instagram content creator for {config.BRAND_NAME},
a friendly, science-backed health and lifestyle account.

Your tone is warm and approachable (like a knowledgeable friend, not a doctor),
empowering, clear (no jargon), and concise.

Choose the best post type for each article:
- "stat"      → article has a compelling statistic or research finding
- "tips"      → article has multiple actionable tips, foods, habits, or steps
- "myth_fact" → article debunks a common myth or corrects a misconception
- "quote"     → article contains a powerful insight or quote worth amplifying

Captions always start with the hook, use short paragraphs, and end with a CTA.
Hashtags: mix niche (#GutHealthTips) with broad (#WellnessJourney).
Always include #HealthyLiving #WellnessTips #{config.BRAND_NAME.replace(" ", "")}
Total hashtags: exactly 20.
"""


def generate_post(article: ScrapedArticle) -> GeneratedPost:
    """
    Generate a complete Instagram post from a single scraped article.
    Automatically picks post_type and format based on content.
    """
    prompt = f"""Create an Instagram post for this health article.

SOURCE: {article.source.upper()}
TOPIC: {article.topic}
TITLE: {article.title}
SUMMARY: {article.summary}

Return ONLY a valid JSON object (no markdown fences, no extra text):

{{
  "post_type": "stat" | "tips" | "myth_fact" | "quote",
  "format": "single" | "carousel",
  "hook": "...",
  "caption": "150-200 word Instagram caption starting with hook, ending with CTA",
  "hashtags": ["#Tag1", ...],
  "content_warning": null,

  "stat_number": "e.g. 73% — only for post_type=stat",
  "stat_label": "short label below the number",
  "stat_context": "one sentence why this matters",
  "stat_source": "Source Name, Year",

  "tips_title": "e.g. 5 Foods That Fight Inflammation — only for post_type=tips",
  "tips": [
    {{"number": "01", "heading": "Food Name", "body": "2-3 sentences explanation", "bonus": "Try it in: ..."}}
  ],
  "tips_cta": "Save this for your next grocery run",

  "myth": "The myth statement in quotes — only for post_type=myth_fact",
  "fact_headline": "Short punchy fact headline",
  "fact_body": "2-3 sentence explanation",

  "quote_text": "The quote — only for post_type=quote",
  "quote_attribution": "Person Name",
  "quote_context": "One line insight"
}}

Rules:
- hook: max 15 words, no emoji, surprising stat or bold claim
- hashtags: exactly 20 items
- for "stat": format must be "single"
- for "tips": format must be "carousel", provide 4-6 tips
- for "myth_fact": format must be "carousel" (2 slides: myth + fact)
- for "quote": format must be "single"
- populate ONLY the fields for the chosen post_type; set others to empty string/list"""

    client = _get_client()
    try:
        response = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        data: dict[str, Any] = json.loads(raw)

        post_type = data.get("post_type", "tips")

        # Build slides for carousel types so downstream code still works
        slides: list[dict] = []
        if post_type == "tips":
            for t in data.get("tips", []):
                slides.append({"heading": t.get("heading", ""), "body": t.get("body", "")})
        elif post_type == "myth_fact":
            slides = [
                {"heading": "MYTH",  "body": data.get("myth", "")},
                {"heading": "FACT",  "body": data.get("fact_body", "")},
            ]

        return GeneratedPost(
            post_type=post_type,
            format=data.get("format", "single"),
            hook=data.get("hook", ""),
            caption=data.get("caption", ""),
            hashtags=data.get("hashtags", []),
            slides=slides,
            content_warning=data.get("content_warning"),
            stat_number=data.get("stat_number", ""),
            stat_label=data.get("stat_label", ""),
            stat_context=data.get("stat_context", ""),
            stat_source=data.get("stat_source", ""),
            tips_title=data.get("tips_title", ""),
            tips=data.get("tips", []),
            tips_cta=data.get("tips_cta", ""),
            myth=data.get("myth", ""),
            fact_headline=data.get("fact_headline", ""),
            fact_body=data.get("fact_body", ""),
            quote_text=data.get("quote_text", ""),
            quote_attribution=data.get("quote_attribution", ""),
            quote_context=data.get("quote_context", ""),
        )

    except (json.JSONDecodeError, KeyError) as exc:
        logger.error("Post generation parse error for %r: %s", article.title, exc)
        return GeneratedPost(
            post_type="tips",
            format="single",
            hook=article.title[:80],
            caption=f"{article.title}\n\n{article.summary[:500]}\n\n"
                    f"Follow {config.INSTAGRAM_HANDLE} for more.",
            hashtags=["#HealthyLiving", "#WellnessTips", "#Health", "#Wellness",
                      "#HealthTips", "#HealthyLifestyle", "#MedicalResearch",
                      "#Nutrition", "#MentalHealth", "#ScienceBacked",
                      "#HealthNews", "#HealthyHabits", "#Prevention",
                      "#HealthEducation", "#WellnessJourney", "#Mindfulness",
                      "#HealthyMind", "#HealthyBody", "#EvidenceBased",
                      f"#{config.BRAND_NAME.replace(' ', '')}"],
            slides=[],
        )
    except anthropic.APIError as exc:
        logger.error("Claude API error during generation: %s", exc)
        raise
