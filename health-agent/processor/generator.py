"""
Claude-powered Instagram content generator.
Takes a single article and returns a fully structured post ready for design.
"""

import json
import logging
from dataclasses import dataclass, field

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
    format: str                          # "single" | "carousel"
    hook: str                            # Short attention-grabbing first line
    caption: str                         # Full Instagram caption (150–200 words)
    hashtags: list[str]                  # 20 hashtags
    slides: list[dict] = field(default_factory=list)  # [{heading, body}] for carousels
    content_warning: str | None = None   # e.g. "Contains mention of medication"


SYSTEM_PROMPT = f"""You are an expert Instagram content creator for {config.BRAND_NAME},
a friendly, science-backed health and lifestyle account.

Your tone is:
- Warm and approachable (like a knowledgeable friend, not a doctor)
- Empowering (helps people take action, not fear)
- Clear (no jargon — explain it in plain English)
- Concise (Instagram users scroll fast)

Your captions always:
- Start with a hook that stops the scroll in the first line
- Explain the science simply in 2–3 short paragraphs
- End with a clear CTA (Save this, Share with a friend, Comment below, etc.)
- Feel personal, not like a health article

Your hashtag selection:
- Mix niche tags (#GutHealthTips) with broad tags (#WellnessJourney)
- Always include: #HealthyLiving #WellnessTips #{config.BRAND_NAME.replace(" ", "")}
- Total: exactly 20 hashtags

For carousels (educational content):
- 4 to 6 slides
- Slide 1: Hook / title
- Slides 2–5: One key insight per slide (heading + 1–2 sentence body)
- Final slide: Takeaway + CTA
"""


def generate_post(article: ScrapedArticle) -> GeneratedPost:
    """
    Generate a complete Instagram post from a single scraped article.
    Automatically decides single vs carousel based on content richness.
    """
    prompt = f"""Create an Instagram post for this health article.

SOURCE: {article.source.upper()}
TOPIC: {article.topic}
TITLE: {article.title}
SUMMARY: {article.summary}

Return ONLY a valid JSON object in this exact format (no markdown fences, no extra text):
{{
  "format": "single" or "carousel",
  "hook": "...",
  "caption": "...",
  "hashtags": ["#Tag1", "#Tag2", ...],
  "slides": [
    {{"heading": "...", "body": "..."}},
    ...
  ],
  "content_warning": null or "..."
}}

Rules:
- Use "carousel" if there are 3+ distinct points to teach; otherwise "single"
- hook: max 15 words, no emoji, must be a pattern interrupt (surprising stat, bold claim, question)
- caption: 150–200 words total including hook. Start with hook. Use line breaks for readability.
- slides: only include if format is "carousel" (4–6 slides)
- hashtags: exactly 20 items"""

    client = _get_client()
    try:
        response = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()

        # Strip markdown code fences if Claude adds them
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        data = json.loads(raw)

        return GeneratedPost(
            format=data.get("format", "single"),
            hook=data.get("hook", ""),
            caption=data.get("caption", ""),
            hashtags=data.get("hashtags", []),
            slides=data.get("slides", []),
            content_warning=data.get("content_warning"),
        )

    except (json.JSONDecodeError, KeyError) as exc:
        logger.error("Post generation parse error for %r: %s", article.title, exc)
        # Minimal fallback so the pipeline doesn't die
        return GeneratedPost(
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
            content_warning=None,
        )
    except anthropic.APIError as exc:
        logger.error("Claude API error during generation: %s", exc)
        raise
