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
    hook: str
    caption: str
    hashtags: list[str]
    slides: list[dict] = field(default_factory=list)
    content_warning: str | None = None

    # stat fields
    stat_number: str = ""
    stat_label: str = ""
    stat_context: str = ""
    stat_source: str = ""

    # tips — 7-slide carousel fields
    clinical_reality: str = ""           # Slide 2: empathy context
    breakdown_slides: list[dict] = field(default_factory=list)  # Slides 3-5
    prevention_bullets: list[str] = field(default_factory=list) # Slide 6
    cta_text: str = ""                   # Slide 7
    disclaimer: str = ""                 # Slide 7

    # myth_fact fields
    myth: str = ""
    fact_headline: str = ""
    fact_body: str = ""

    # quote fields
    quote_text: str = ""
    quote_attribution: str = ""
    quote_context: str = ""


SYSTEM_PROMPT = f"""You are the Instagram content creator for {config.BRAND_NAME} (@Dr.dimithra),
a warm, approachable medical education page for the general public.

Brand voice:
- Knowledgeable doctor-friend — never a textbook, never fear-mongering
- Warm and personal — use "you" and "your body", never cold or clinical
- Use medical terms but ALWAYS briefly explain them in plain language immediately after
- Audience: general public with moderate health literacy

Caption structure:
1. Hook — bold statement, surprising fact, or relatable question (under 12 words, no jargon)
2. 2–4 sentences of educational content; explain every medical term used
3. 1–2 practical takeaways the reader can act on today
4. Warm relevant emojis (not excessive)
5. End with ONE approved CTA:
   "Save this post 📌" | "Share this with someone who needs to hear it 💙" |
   "Follow for more health tips you can actually use" | "Tag a friend who needs this 💬"

Post types:
- "stat"      → striking statistic or research finding → single image
- "tips"      → educational carousel with data and action steps → 7-slide carousel
- "myth_fact" → debunks a myth → 2 slides
- "quote"     → powerful medical insight → single image

Hashtag pool (pick 20):
Broad: #HealthTips #MedicalEducation #DoctorOnInstagram #HealthAwareness #PublicHealth #HealthyLiving
Niche: #HealthLiteracy #KnowYourHealth #MedicalMyths #DoctorAdvice #PatientEducation #PreventiveMedicine
Engagement: #AskYourDoctor #HealthFacts #MedicalFacts #HealthyHabits
Always: #{config.BRAND_NAME.replace(" ", "").replace(".", "")} #DrDimithra + condition-specific tags
"""


def generate_post(article: ScrapedArticle, force_type: str | None = None) -> GeneratedPost:
    type_instruction = (
        f"\nYou MUST use post_type: \"{force_type}\" — do not choose a different type.\n"
        if force_type else ""
    )

    prompt = f"""Create an Instagram post for this health article.
{type_instruction}
SOURCE: {article.source.upper()}
TOPIC: {article.topic}
TITLE: {article.title}
SUMMARY: {article.summary}

Return ONLY a valid JSON object (no markdown fences, no extra text):

{{
  "post_type": "stat" | "tips" | "myth_fact" | "quote",
  "format": "single" | "carousel",
  "hook": "Under 12 words, no jargon",
  "caption": "150-200 word caption, hook first, CTA last",
  "hashtags": ["#Tag1", ...],
  "content_warning": null,

  // ── STAT fields (post_type=stat only) ──────────────────────────────────────
  "stat_number": "e.g. 1 in 3",
  "stat_label": "short label under the number",
  "stat_context": "one sentence why this matters",
  "stat_source": "Journal / Organisation, Year",

  // ── TIPS fields (post_type=tips only) — 7-slide carousel ──────────────────
  // Slide 1 is the hook (above). Then:
  "clinical_reality": "2-3 warm empathy sentences — who experiences this and why it matters",
  "breakdown_slides": [
    {{
      "type": "bar_chart",
      "title": "Short chart title",
      "takeaway": "The 'so what' insight shown in terracotta below chart",
      "categories": ["Label 1", "Label 2", "Label 3"],
      "values": [50, 75, 120],
      "highlight_index": 2,
      "note": "Values are illustrative/representative"
    }},
    {{
      "type": "text",
      "heading": "Key concept title",
      "body": "2-3 sentences explaining one core idea clearly"
    }}
  ],
  "prevention_bullets": ["Action step 1", "Action step 2", "Action step 3"],
  "cta_text": "Save this post 📌",
  "disclaimer": "This content is for educational purposes only. Always consult your doctor.",

  // ── MYTH/FACT fields (post_type=myth_fact only) ────────────────────────────
  "myth": "The myth statement in quotes",
  "fact_headline": "Short punchy fact headline",
  "fact_body": "2-3 sentence explanation",

  // ── QUOTE fields (post_type=quote only) ───────────────────────────────────
  "quote_text": "The quote",
  "quote_attribution": "Person Name / Source",
  "quote_context": "One line insight"
}}

Rules:
- hashtags: exactly 20
- tips breakdown_slides: 2-3 slides total (mix bar_chart and text types)
- bar_chart values: use illustrative representative numbers that show the concept clearly
- for "stat": format="single"; for "tips": format="carousel"; for "myth_fact": format="carousel"; for "quote": format="single"
- populate ONLY the fields for the chosen post_type"""

    client = _get_client()
    try:
        response = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=2500,
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

        # Build legacy slides list for compatibility
        slides: list[dict] = []
        if post_type == "tips":
            for bd in data.get("breakdown_slides", []):
                slides.append({"heading": bd.get("heading", bd.get("title", "")),
                                "body": bd.get("body", bd.get("takeaway", ""))})
        elif post_type == "myth_fact":
            slides = [
                {"heading": "MYTH", "body": data.get("myth", "")},
                {"heading": "FACT", "body": data.get("fact_body", "")},
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
            clinical_reality=data.get("clinical_reality", ""),
            breakdown_slides=data.get("breakdown_slides", []),
            prevention_bullets=data.get("prevention_bullets", []),
            cta_text=data.get("cta_text", "Save this post 📌"),
            disclaimer=data.get("disclaimer",
                "This content is for educational purposes only. Always consult your doctor."),
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
            hashtags=["#HealthTips", "#MedicalEducation", "#DoctorOnInstagram",
                      "#HealthAwareness", "#PublicHealth", "#HealthyLiving",
                      "#HealthLiteracy", "#KnowYourHealth", "#MedicalMyths",
                      "#DoctorAdvice", "#PatientEducation", "#PreventiveMedicine",
                      "#AskYourDoctor", "#HealthFacts", "#MedicalFacts",
                      "#HealthyHabits", "#HeartHealth", "#MentalHealthMatters",
                      "#DrDimithra",
                      f"#{config.BRAND_NAME.replace(' ', '').replace('.', '')}"],
            slides=[],
        )
    except anthropic.APIError as exc:
        logger.error("Claude API error during generation: %s", exc)
        raise
