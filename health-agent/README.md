# Health Content AI Agent

An AI-powered system that scrapes the latest health and medical news, generates
Instagram-ready content with Claude, designs posts using your Canva templates,
and lets you review and publish them — all from a simple web dashboard.

**Schedule:** Runs automatically 3x/week (Mon, Wed, Fri at 8 AM)
**Topics:** General wellness · Nutrition · Mental health · Medical research
**Post formats:** Single image · Carousel (Reels — Phase 2)

---

## How It Works

```
RSS Feeds + PubMed → Claude selects top 3 → Claude writes captions →
Canva designs images → Review dashboard → You approve → Instagram posts live
```

---

## Quick Setup (Step by Step)

### Step 1 — Install Python

You need Python 3.11 or newer.
- Download from: https://www.python.org/downloads/
- After installing, open a terminal and check: `python --version`

### Step 2 — Download the project

```bash
git clone <your-repo-url>
cd health-agent
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Create your config file

```bash
cp .env.example .env
```

Now open `.env` in any text editor (Notepad, TextEdit, VS Code) and fill in
your credentials one section at a time (see the sections below).

### Step 5 — Initialise the database

```bash
python main.py setup
```

This creates the local database and image folders. Safe to run multiple times.

### Step 6 — Verify everything works

```bash
python main.py verify
```

Fix any errors shown before continuing.

---

## Credential Setup Guides

### A) Claude API Key

1. Go to https://console.anthropic.com/
2. Click **API Keys** → **Create Key**
3. Copy the key (starts with `sk-ant-`)
4. Paste it into `.env` as `ANTHROPIC_API_KEY=sk-ant-...`

---

### B) Canva Connect API

1. Go to https://www.canva.com/developers/ and click **Get started**
2. Create a new integration → copy **Client ID** and **Client Secret**
3. Add to `.env`:
   ```
   CANVA_CLIENT_ID=your_client_id
   CANVA_CLIENT_SECRET=your_client_secret
   ```
4. Run the one-time auth flow:
   ```bash
   python main.py canva-auth
   ```
   Your browser will open. Approve the Canva access. Tokens are saved automatically.

5. Create your Canva templates:
   - In Canva, design a **1080×1080 px** template for single posts
     - Add a text element named `hook`
     - Add a text element named `caption_preview`
     - Add a text element named `brand_handle`
   - Design a **1080×1080 px** template for carousel slides
     - Add a text element named `slide_heading`
     - Add a text element named `slide_body`
     - Add a text element named `slide_number`
     - Add a text element named `brand_handle`

6. Find your template IDs:
   ```bash
   python main.py list-templates
   ```
   Copy the IDs into `.env`:
   ```
   CANVA_SINGLE_POST_TEMPLATE_ID=DEF...
   CANVA_CAROUSEL_TEMPLATE_ID=GHI...
   ```

> **Note on element names:** In Canva's editor, click a text box → go to the
> element panel → rename it to match the names above exactly. This is how the
> agent knows which text to fill in.

---

### C) Instagram Graph API

This requires a few steps. Take your time — it's worth it.

#### Step C1 — Convert to a Business or Creator account

1. Open Instagram → Profile → Settings → Account
2. Tap **Switch to Professional Account**
3. Choose **Creator** or **Business** (either works)

#### Step C2 — Link to a Facebook Page

1. Go to https://www.facebook.com/ and create a Page (or use an existing one)
2. In Instagram → Settings → Account → Linked Accounts → connect your Facebook

#### Step C3 — Create a Facebook App

1. Go to https://developers.facebook.com/apps/
2. Click **Create App** → choose **Other** → **Business**
3. Fill in app name and email
4. In the app dashboard: **Add Product** → **Instagram Graph API**

#### Step C4 — Add your Instagram account to the app

1. In the app dashboard → **Instagram** → **API setup with Instagram login**
2. Generate a **User Access Token** with these permissions:
   - `instagram_business_basic`
   - `instagram_business_content_publish`
3. Exchange for a **long-lived token** (valid 60 days):
   ```
   https://graph.facebook.com/v18.0/oauth/access_token
   ?grant_type=fb_exchange_token
   &client_id=YOUR_APP_ID
   &client_secret=YOUR_APP_SECRET
   &fb_exchange_token=YOUR_SHORT_TOKEN
   ```
4. Get your **Instagram User ID**:
   ```
   https://graph.instagram.com/v22.0/me?fields=id,username&access_token=YOUR_TOKEN
   ```

5. Add to `.env`:
   ```
   INSTAGRAM_USER_ID=123456789
   INSTAGRAM_ACCESS_TOKEN=EAA...long...token
   ```

> **Important:** For development/testing, you only need to add your own account
> as a test user in the app. Meta App Review is only required if other people
> will use this app to post from their accounts.

#### Step C5 — Refresh token reminder

Instagram tokens expire after 60 days. Refresh before they expire:
```bash
python main.py refresh-token
```

---

### D) PubMed API Key (optional but recommended)

1. Register free at: https://www.ncbi.nlm.nih.gov/account/
2. Go to **Settings** → **API Key Management** → **Create new key**
3. Add to `.env`: `PUBMED_API_KEY=your_key`

Without a key the agent still works, just slower (3 requests/second vs 10).

---

## Daily Usage

### Generate posts (manual)

```bash
python main.py run
```

Scrapes articles, selects the best 3, generates captions, creates Canva designs.
Takes 2–5 minutes. When done, open the dashboard.

### Review and publish

```bash
python main.py dashboard
```

Opens at http://localhost:5000. For each post you can:
- **Edit** the caption and hashtags
- **Approve** → marks ready to publish
- **Publish Now** → sends to Instagram immediately
- **Reject** → discards the post

### Start automated scheduling

```bash
python main.py schedule
```

Leave this running (or use a startup script). The pipeline runs automatically
every Mon/Wed/Fri at 8:00 AM. You'll see terminal output when new posts are ready.

To change the schedule, edit `.env`:
```
SCHEDULE_DAYS=tue,thu,sat
SCHEDULE_TIME=09:30
```

---

## Running Automatically on Startup (Optional)

### Mac/Linux (using cron)

```bash
crontab -e
```

Add this line (replace the path with your actual project path):
```
0 7 * * 1,3,5 cd /path/to/health-agent && python main.py run >> logs/pipeline.log 2>&1
```

### Windows (Task Scheduler)

1. Open **Task Scheduler** → **Create Basic Task**
2. Set trigger: Weekly, Monday/Wednesday/Friday at 8:00 AM
3. Action: Start a program → `python` → Arguments: `main.py run`
4. Start in: your `health-agent` folder path

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| `Missing required environment variable` | Open `.env` and fill in the missing value |
| `Canva token expired` | Run `python main.py canva-auth` again |
| `Instagram 401 error` | Run `python main.py refresh-token` |
| `No new articles found` | Wait a day — same articles are deduplicated |
| Images not showing in dashboard | Check `output/images/` folder exists and has files |
| Post shows "failed" status | Check terminal for error details |

---

## Project Structure

```
health-agent/
├── main.py              ← Start here (CLI)
├── scheduler.py         ← Automation logic
├── config.py            ← All settings (reads from .env)
├── .env                 ← Your private credentials (never share this!)
├── .env.example         ← Template for .env
├── requirements.txt     ← Python packages
│
├── scraper/             ← Fetches health articles
├── processor/           ← Claude AI content selection & generation
├── designer/            ← Canva API integration
├── publisher/           ← Instagram API posting
├── dashboard/           ← Web review interface
├── database/            ← Local SQLite storage
└── output/images/       ← Generated post images
```

---

## Phase 2 Roadmap

- **Reels/video:** Canva animated templates exported as MP4
- **Email alerts:** Get notified when new posts are queued
- **Analytics:** Track reach and engagement from Instagram Insights
- **Token auto-refresh:** Auto-renew Instagram token before 60-day expiry

---

## Important Notes

- **Never share your `.env` file** — it contains API keys and tokens
- **All posts require your manual approval** before going live
- **Instagram rate limit:** 100 posts per 24 hours (you're only doing 3/week)
- **Canva API:** Tokens expire every ~4 hours but auto-refresh silently

---

*Built with Claude (Anthropic), Canva Connect API, and Instagram Graph API.*
