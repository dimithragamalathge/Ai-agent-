---
name: dr-dimithra-content
description: Create Instagram posts, Reels, and monthly content plans for Dr. Dimithra G's medical education page (@Dr.dimithra). Use this skill whenever the user wants to: create an Instagram post, story, carousel, reel, or short video for their medical page; plan out the month's content calendar; or schedule and organise posts and reels in Notion. Trigger on phrases like "make a post about", "create a reel on", "plan my content for the month", "content calendar", "reel for", "carousel on", "schedule my posts", "plan next month", "what should I post this week", "Notion content plan", "post for awareness day", "health tip post", "explain [condition]", "debunk [myth]", or any request involving Instagram content, content planning, or medical social media — even vague ones like "I want to post about X" or "help me plan my Instagram". Always use this skill before creating any Instagram content or content calendar.
---
 
# Dr. Dimithra Content Skill
 
Creates Instagram **posts, Reels, and monthly content plans** for **Dr. Dimithra G · @Dr.dimithra** — a warm, approachable medical education page.
 
---
 
## Brand Identity
 
- **Name:** Dr. Dimithra G
- **Handle:** @Dr.dimithra
- **Style:** Warm & approachable — soft colors, friendly tone, not clinical or cold
- **Audience:** General public with moderate health literacy
- **Tone:** Knowledgeable doctor-friend, never a textbook or fear-mongering
- **Caption depth:** Use medical terms, always briefly explain them
---
 
## Mode Selection
 
When the user's request arrives, identify the mode:
 
| User Intent | Mode |
|---|---|
| "make a post", "carousel", "story", "health tip post" | → **MODE A: Instagram Post** |
| "make a reel", "short video", "reel script", "60-second video" | → **MODE B: Instagram Reel** |
| "plan the month", "content calendar", "what should I post", "schedule posts", "Notion calendar" | → **MODE C: Monthly Content Plan** |
| Mixed (e.g. "plan the month and make the first reel") | → Run MODE C first, then the relevant content mode |
 
If unclear, ask ONE short question.
 
---
 
## MODE A — Instagram Post
 
### Step 1 — Identify Content Request
 
Extract:
- **Topic** (e.g. "Type 2 Diabetes", "Myth: antibiotics for a cold")
- **Content type** (tip, explainer, myth-bust, Q&A, awareness)
- **Format** — if not specified, use the Format Guide below
**Format Guide:**
 
| Content Type | Best Format |
|---|---|
| Quick tip / myth bust | Single square post (1:1) |
| Step-by-step / list | Carousel (multiple slides) |
| Awareness day | Story (9:16) OR square post |
| Q&A | Carousel (question on slide 1, answers on slides 2–3+) |
| Condition explainer | Carousel (3–6 slides) |
 
---
 
### Step 2 — Write the Caption
 
```
[Hook line — bold statement, surprising fact, or relatable question]
 
[2–4 sentences of educational content. Use moderate medical depth: mention terms like
"inflammation", "insulin resistance", "hypertension" etc. but explain each in plain language.]
 
[1–2 practical takeaway sentences]
 
[Relevant emojis throughout — warm and human, not excessive]
 
[Hashtags — 8–12, mix of broad and niche]
 
[CTA — one of the approved endings below]
```
 
**Approved CTAs:**
- "Save this post 📌"
- "Share this with someone who needs to hear it 💙"
- "Follow for more health tips you can actually use"
- "Tag a friend who needs this 💬"
---
 
### Step 3 — Create the Canva Design
 
Use the **Canva `generate-design` tool** with this prompt template:
 
```
Create a warm, approachable Instagram [FORMAT] for a medical education page.
 
Branding: Include "Dr. Dimithra G" and "@Dr.dimithra" on the design (footer or subtle placement).
 
Style: Soft warm colors (peach, warm beige, dusty rose, sage green, or soft sky blue).
Clean modern sans-serif fonts. Friendly icons or simple medical illustrations.
No harsh clinical whites or cold blues. Feels like advice from a trusted doctor friend.
 
Content: [INSERT KEY TEXT / SLIDE TITLES]
 
Layout: [DESCRIBE LAYOUT — e.g. "Bold headline at top, 3 icon-bullet points in middle, brand name at bottom"]
```
 
**Canva design_type mapping:**
- Single square post → `design_type: "instagram_post"`
- Story → `design_type: "your_story"`
- Carousel cover → `design_type: "instagram_post"` (user duplicates slides in Canva)
---
 
### Step 4 — Deliver Post Output
 
1. **🎨 Canva Design** — generated via Canva tool
2. **📝 Caption** — full ready-to-copy caption with hashtags and CTA
3. **💡 Post Tip** — 1–2 short notes (best time to post, suggested sticker, etc.)
---
 
## MODE B — Instagram Reel
 
### Step 1 — Parse the Request
 
Extract:
- **Topic** (e.g. "high blood pressure", "myth: antibiotics for colds")
- **Content type** — see Reel Content Types below
- **Urgency/tone** (alarming vs reassuring vs educational)
**Reel Content Types:**
 
| Type | Description |
|---|---|
| Condition explainer | "What is X?" — cause, symptoms, facts |
| Myth busting | Debunk a misconception |
| Symptom awareness | When to worry, what it could mean |
| Treatment & medication | What a drug/treatment does, how to use safely |
| Preventive health | Habits, screenings, lifestyle tips |
 
---
 
### Step 2 — Choose Length & Color Palette
 
**Reel Length Guide:**
 
| Length | Best For | Slide Count |
|---|---|---|
| 15–30 sec | Quick myth bust, single tip | 4–6 slides |
| 30–60 sec | Condition intro, symptom list | 7–10 slides |
| 60–90 sec | Full explainer, treatment guide | 10–15 slides |
 
**Color Guide (Topic-Based):**
 
| Topic Mood | Palette |
|---|---|
| Calm / preventive / wellness | Sage green + warm white + soft gold |
| Urgent / symptom awareness | Dusty rose + deep burgundy + ivory |
| Myth busting / surprising | Electric teal + warm navy + clean white |
| Condition explainer | Soft sky blue + peach + warm grey |
| Medication / treatment | Lavender + deep slate + soft white |
 
State your chosen length and palette in one line before proceeding.
 
---
 
### Step 3 — Write the Hook Line
 
The first 3 seconds must stop the scroll. Under 12 words. No medical jargon.
 
**Hook formulas:**
- Surprising stat: *"90% of people with high BP don't know they have it."*
- Challenge assumption: *"That headache might not be what you think it is."*
- Direct question: *"Are you taking your antibiotics correctly?"*
- Bold statement: *"This common habit is silently damaging your kidneys."*
---
 
### Step 4 — Write the Slide Script
 
Each slide = on-screen text + voiceover line.
 
```
SLIDE [N]
On-screen text: [Short, bold — max 10 words]
Voiceover: [Full natural sentence for TTS — 15–25 words, conversational]
Duration: ~[X] seconds
```
 
**Slide structures by content type** → see `/references/reel-structures.md`
 
**Voiceover tone rules:**
- Speak as a knowledgeable friend, not a textbook
- Use "you" and "your body"
- Short sentences — TTS reads better with natural pauses
- Explain any medical words immediately after using them
---
 
### Step 5 — Create the Canva Reel Cover
 
Use `generate-design` with `design_type: "your_story"` (9:16 vertical).
 
```
Create a warm, modern Instagram Reel cover slide (9:16 vertical) for a medical education page.
 
Branding: Include "Dr. Dimithra G" and "@Dr.dimithra" — subtle footer placement.
 
Style: [CHOSEN PALETTE]. Clean modern sans-serif fonts. Simple medical icons.
Warm and approachable. Motion-friendly layout (text-safe zones, nothing near edges).
 
Cover text: [HOOK LINE — large, bold, centered or top-third]
 
Layout: Hook line dominates. Small subtitle if needed. Brand name at bottom.
```
 
> **User note:** After generating the cover in Canva, duplicate the slide and update on-screen text for each subsequent slide using the script.
 
---
 
### Step 6 — Write the Reel Caption
 
```
[Hook line — slightly expanded from reel opening]
 
[2–3 sentences of educational context]
 
[1 practical takeaway]
 
[Relevant emojis]
 
💾 Save this reel — you'll want to come back to it.
 
[10–14 hashtags — broad + niche + condition-specific]
```
 
---
 
### Step 7 — Deliver Reel Output
 
1. **🎬 Reel Brief** — chosen length, palette, content type (2 lines)
2. **⚡ Hook Line**
3. **🎨 Canva Cover Design** — generated via Canva tool
4. **📋 Full Slide Script** — all slides with on-screen text + voiceover
5. **📝 Caption** — ready to copy with hashtags
6. **💡 Production Tip** — TTS tool recommendation or posting tip
**Recommended TTS tools for voiceover:**
- **ElevenLabs** (elevenlabs.io) — most natural, free tier available
- **Murf.ai** — warm, friendly doctor tones
- **Google TTS / Natural Reader** — free fallback
Suggest: warm, mid-paced, clear voice.
 
---
 
## MODE C — Monthly Content Plan + Notion
 
Creates a structured monthly content calendar with a mix of posts and reels, then saves it to Notion.
 
### Step 1 — Gather Planning Context
 
Ask the user (or infer from the message):
- **Month** (e.g. "May 2025")
- **Posting frequency** — default is 3–4 posts/week if not stated
- **Any awareness days or themes** they want to include (optional — Claude will suggest if not provided)
- **Preferred content mix** — default: ~60% posts, ~40% reels
If the user says "just plan it" or similar, use all defaults and proceed.
 
---
 
### Step 2 — Build the Content Plan
 
Generate a full month calendar with this structure per entry:
 
```
Week [N] — [Date range]
 
[Day, Date] → [FORMAT: Post/Reel/Story] — [TOPIC] — [CONTENT TYPE]
[Day, Date] → [FORMAT: Post/Reel/Story] — [TOPIC] — [CONTENT TYPE]
...
```
 
**Planning rules:**
- Never post two reels back-to-back — alternate with posts
- Include at least 1 awareness day post per month (research relevant health awareness dates)
- Balance topics across: conditions, myths, symptoms, prevention, Q&A
- Leave at least 2 gap days per week (no post)
- Mark high-effort pieces (full explainer reels, carousels) on Mon/Wed/Fri
- Mark lighter posts (single tip, Q&A) on Tue/Thu
**Default awareness dates to check:**
- World Heart Day (Sep 29), World Diabetes Day (Nov 14), World Mental Health Day (Oct 10), World Cancer Day (Feb 4), World Stroke Day (Oct 29), International Women's Day (Mar 8), etc.
- Always verify the month and include relevant ones.
---
 
### Step 3 — Save to Notion
 
Use the **Notion MCP** (`https://mcp.notion.com/mcp`) to create the content calendar.
 
**Database schema to create (or reuse if it exists):**
 
| Property | Type | Notes |
|---|---|---|
| Title | Title | Topic / post name |
| Date | Date | Scheduled post date |
| Format | Select | Post / Reel / Story / Carousel |
| Content Type | Select | Explainer / Myth-bust / Tip / Q&A / Awareness / Prevention |
| Status | Select | Idea / In Progress / Ready / Posted |
| Caption Ready | Checkbox | — |
| Design Ready | Checkbox | — |
| Notes | Text | Hook idea, key points, awareness day name |
 
**Workflow:**
1. Search for an existing database named "Instagram Content Calendar" in Notion
2. If found → add new entries for the planned month
3. If not found → create a new Notion database with the schema above, then add all entries
4. After saving, return the Notion page link to the user
---
 
### Step 4 — Deliver Plan Output
 
1. **📅 Monthly Plan** — full calendar printed in chat (clean, scannable format)
2. **✅ Notion confirmation** — "Saved to your Notion Content Calendar" + link
3. **🎯 Highlight** — call out 2–3 high-priority pieces the user should create first
4. **💡 Offer** — "Want me to create any of these now? Just say which one."
---
 
## Approved Hashtag Pool
 
**Broad:** `#HealthTips` `#MedicalEducation` `#DoctorOnInstagram` `#HealthAwareness` `#PublicHealth` `#HealthyLiving`
 
**Niche/education:** `#MedTwitter` `#HealthLiteracy` `#KnowYourHealth` `#MedicalMyths` `#DoctorAdvice` `#PatientEducation` `#PreventiveMedicine`
 
**Engagement:** `#AskYourDoctor` `#HealthFacts` `#MedicalFacts` `#HealthyHabits`
 
**Reel-specific:** `#InstagramReels` `#HealthReels` `#ReelsHealth` `#LearnOnReels` `#MedReels`
 
Add condition-specific tags as relevant (e.g. `#DiabetesAwareness`, `#HeartHealth`, `#MentalHealthMatters`).
 
---
 
## Example Triggers
 
**Posts:**
- "Make a post about the myths around antibiotics"
- "Create a carousel explaining what hypertension is"
- "I need a World Diabetes Day story"
- "Health tip post for this week"
**Reels:**
- "Make a reel about the warning signs of a stroke"
- "Reel debunking the myth that cracking knuckles causes arthritis"
- "60-second reel on how to use an inhaler correctly"
- "Reel for World Heart Day"
**Content Planning:**
- "Plan my Instagram for May"
- "I need a content calendar for next month"
- "What should I post this week?"
- "Help me plan my posts and reels for June, save to Notion"
- "Schedule my content for the month"
 
