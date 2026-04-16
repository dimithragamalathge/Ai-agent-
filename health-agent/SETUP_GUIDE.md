# Complete Setup Guide — iPad + PythonAnywhere

Everything runs in your browser. No laptop, no downloads, no installs on your device.
Follow each step in order. Takes about 45–60 minutes total.

---

## What You'll End Up With

```
pythonanywhere.com  →  always-on web app  →  yourusername.pythonanywhere.com
                                              (your private review dashboard)

Daily at 8 AM  →  pipeline runs  →  scrapes health news  →  Claude writes posts
               →  Canva designs images  →  posts appear in your dashboard
               →  you review on iPad  →  tap Publish  →  live on Instagram
```

---

## PART 1 — Create Your PythonAnywhere Account

**Time: 5 minutes**

1. On your iPad, open Safari and go to **pythonanywhere.com**

2. Tap **Pricing & signup** → tap **Create a Beginner account** (free)

3. Fill in:
   - Username: pick something short, e.g. `healthagent` (this becomes your URL)
   - Email: your email
   - Password: a strong password
   
4. Verify your email and log in

5. You'll see a dashboard with tabs: **Consoles, Files, Web, Tasks, Databases**

---

## PART 2 — Get the Code from GitHub

**Time: 5 minutes**

1. In PythonAnywhere, tap the **Consoles** tab

2. Under "Start a new console", tap **Bash**
   - A terminal window opens in your browser — this is your IDE terminal

3. Type this command exactly and press Enter:
   ```
   git clone https://github.com/dimithragamalathge/Ai-agent- repo
   ```
   
4. Then navigate into the project:
   ```
   cd repo/health-agent
   ```

5. Confirm it worked — type `ls` and press Enter.
   You should see files like `main.py`, `config.py`, `requirements.txt`

---

## PART 3 — Create a Virtual Environment & Install Packages

**Time: 5 minutes**

Still in the same Bash console, type these commands one at a time:

```bash
python3.11 -m venv venv
```
*(Creates an isolated Python environment)*

```bash
source venv/bin/activate
```
*(Activates it — you'll see `(venv)` appear at the start of the line)*

```bash
pip install -r requirements.txt
```
*(Installs all needed packages — takes 1–2 minutes)*

When it finishes, type:
```bash
python main.py setup
```
You should see: `Database initialised.`

---

## PART 4 — Create Your .env Config File

**Time: 10 minutes**

1. In PythonAnywhere, tap the **Files** tab

2. Navigate to: `repo/health-agent/`
   (tap each folder name to go inside it)

3. You'll see `.env.example` — tap it to open it
   
4. Select all the text, copy it

5. Go back to the `health-agent/` folder

6. Tap **New file**, name it `.env` (with the dot), tap **OK**

7. Paste the text you copied and fill in the values below

### What to fill in right now:

```
INSTAGRAM_HANDLE=@your_actual_instagram_handle
BRAND_NAME=Your Account Name

ANTHROPIC_API_KEY=sk-ant-...    ← from console.anthropic.com

CANVA_REDIRECT_URI=https://yourusername.pythonanywhere.com/canva/callback
  ↑ Replace "yourusername" with YOUR PythonAnywhere username

DASHBOARD_PASSWORD=pick-a-password-only-you-know

FLASK_SECRET_KEY=    ← generate this in Step 4b below
```

### Step 4b — Generate a secret key:

Go back to the Bash console and type:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
Copy the long string it prints. Paste it as `FLASK_SECRET_KEY=` in your `.env`

**Leave these blank for now** — you'll fill them in later:
- `CANVA_CLIENT_ID`, `CANVA_CLIENT_SECRET`
- `INSTAGRAM_USER_ID`, `INSTAGRAM_ACCESS_TOKEN`
- The others at the bottom

8. Tap **Save** (top right of the file editor)

---

## PART 5 — Set Up the Web App (Your Dashboard)

**Time: 10 minutes**

1. Tap the **Web** tab in PythonAnywhere

2. Tap **Add a new web app** → tap **Next**

3. Choose **Manual configuration** (NOT "Flask") → tap **Next**

4. Choose **Python 3.11** → tap **Next**

5. You'll see a configuration page. Make these changes:

### Source code directory:
```
/home/yourusername/repo/health-agent
```
*(Replace `yourusername` with your PythonAnywhere username)*

### Working directory:
```
/home/yourusername/repo/health-agent
```

### Virtualenv:
```
/home/yourusername/repo/health-agent/venv
```

### WSGI configuration file:
Tap the link to the WSGI file. It opens a text editor.

**Delete everything** in that file and replace it with:

```python
import sys
import os
from pathlib import Path

project_root = Path('/home/yourusername/repo/health-agent')
sys.path.insert(0, str(project_root))

os.chdir(str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / '.env')

from dashboard.app import create_app
application = create_app()
```
*(Again replace `yourusername` with yours)*

Tap **Save**

### Static files:
Scroll down to the "Static files" section. Add:
- URL: `/static/`
- Directory: `/home/yourusername/repo/health-agent/dashboard/static`

6. Scroll back up and tap the big green **Reload** button

7. Tap the link to your site: `yourusername.pythonanywhere.com`

You should see a **password login page**. Enter the `DASHBOARD_PASSWORD` you set in `.env`.

**If you see the dashboard — Part 5 is complete!**

---

## PART 6 — Connect Canva

**Time: 10 minutes**

### Step 6a — Create a Canva Developer App

1. On your iPad, open a new tab and go to **canva.com/developers**

2. Tap **Get started** → log in with your paid Canva account

3. Tap **Create an integration**

4. Fill in:
   - Name: `Health Agent`
   - Description: `Personal Instagram content automation`

5. Under **OAuth 2.0 redirect URIs**, add:
   ```
   https://yourusername.pythonanywhere.com/canva/callback
   ```

6. Tap **Save**

7. Copy your **Client ID** and **Client Secret**

### Step 6b — Add to your .env

Go back to PythonAnywhere → Files → `health-agent/.env`

Fill in:
```
CANVA_CLIENT_ID=paste_client_id_here
CANVA_CLIENT_SECRET=paste_client_secret_here
```

Save the file, then go to the Web tab and tap **Reload**

### Step 6c — Authorise Canva

1. Go to your dashboard: `yourusername.pythonanywhere.com`
2. Log in
3. You'll see a blue banner: **"Connect Canva"** — tap it
4. Canva opens — tap **Allow**
5. You're redirected back to your dashboard
6. You'll see "Canva connected successfully!"

---

## PART 7 — Create Your Canva Templates

**Time: 15 minutes**

You need two templates. Open Canva on your iPad.

### Template 1: Single Post (1080×1080 px)

1. Tap **Create a design** → Custom size → `1080 x 1080 px`
2. Design your branded health post layout
3. Add text boxes and name them (tap text → "..." → rename):
   - One text box named: `hook`  *(for the grabbing first line)*
   - One text box named: `caption_preview`  *(short preview of the caption)*
   - One text box named: `brand_handle`  *(your @handle)*
4. Save and name it: `Health Single Post`

### Template 2: Carousel Slide (1080×1080 px)

1. Create another 1080×1080 design
2. Design a slide layout (cleaner, less text)
3. Add text boxes named:
   - `slide_heading`  *(bold point title)*
   - `slide_body`  *(1–2 sentences of explanation)*
   - `slide_number`  *(e.g. "2/5")*
   - `brand_handle`
4. Save and name it: `Health Carousel Slide`

### Get the template IDs

1. Go back to your dashboard
2. Since Canva is connected, you can find template IDs by going to the
   PythonAnywhere Bash console and running:
   ```bash
   cd /home/yourusername/repo/health-agent
   source venv/bin/activate
   python main.py list-templates
   ```
3. Copy the IDs and add to `.env`:
   ```
   CANVA_SINGLE_POST_TEMPLATE_ID=paste_id_here
   CANVA_CAROUSEL_TEMPLATE_ID=paste_id_here
   ```
4. Reload the web app

---

## PART 8 — Connect Instagram

**Time: 15 minutes**

This is the most involved step. Do it carefully.

### Step 8a — Make sure your account is a Business/Creator account

In Instagram → Profile → Settings → Account → Switch to Professional Account

### Step 8b — Link Instagram to a Facebook Page

In Instagram → Settings → Account → Linked Accounts → Facebook
Connect to a Facebook Page (create one if needed — it's free and takes 1 minute)

### Step 8c — Create a Facebook App

1. Go to **developers.facebook.com** on your iPad
2. Tap **My Apps** → **Create App**
3. Choose **Other** → **Business** → fill in name + email
4. In the app dashboard: tap **Add Product** → find **Instagram** → tap **Set up**

### Step 8d — Get your Access Token

1. In your Facebook App → Instagram → **API setup with Instagram login**
2. Tap **Generate Token** for your Instagram account
3. Make sure these permissions are checked:
   - `instagram_business_basic`
   - `instagram_business_content_publish`
4. Copy the token

### Step 8e — Make it long-lived (important!)

The token you just got expires in 1 hour. Make it last 60 days:

1. Open this URL in your browser (fill in your values):
```
https://graph.facebook.com/v22.0/oauth/access_token?grant_type=fb_exchange_token&client_id=YOUR_APP_ID&client_secret=YOUR_APP_SECRET&fb_exchange_token=SHORT_TOKEN
```
2. Copy the `access_token` from the JSON response

### Step 8f — Get your Instagram User ID

Open this URL (fill in your long-lived token):
```
https://graph.instagram.com/v22.0/me?fields=id,username&access_token=YOUR_LONG_TOKEN
```
Copy the `id` value.

### Step 8g — Add to .env

```
INSTAGRAM_USER_ID=paste_id_here
INSTAGRAM_ACCESS_TOKEN=paste_long_lived_token_here
```

Reload the web app.

---

## PART 9 — Set Up the Automatic Schedule

**Time: 5 minutes**

1. In PythonAnywhere, tap the **Tasks** tab

2. Under "Daily tasks", set the time to `08:00` (or whenever you want)

3. In the command box, enter:
```
/home/yourusername/repo/health-agent/venv/bin/python /home/yourusername/repo/health-agent/run_pipeline.py
```
*(Replace `yourusername` with yours — appears 2 times)*

4. Tap **Create**

The task now runs every day at 8 AM. The script checks if it's Mon/Wed/Fri
and only generates posts on those days.

---

## PART 10 — Test Everything

**Time: 5 minutes**

### Run the pipeline manually (first test):

In the PythonAnywhere Bash console:
```bash
cd /home/yourusername/repo/health-agent
source venv/bin/activate
python main.py run
```

Watch the output. You should see:
```
Step 1/5: Scraping health articles…
Scraped 35 new articles total
Step 2/5: Asking Claude to select the best articles…
Claude selected 3 articles
Step 3/5: Generating content for: ...
...
Pipeline complete: 3 post(s) added to review queue
```

### Open your dashboard:

Go to `yourusername.pythonanywhere.com` on your iPad.

You should see 3 posts in the review queue with:
- Generated captions
- Hashtags
- Canva-designed images (if Canva templates are configured)

### Review and publish a post:

1. Tap a post → read the caption
2. Edit anything you want
3. Tap **Approve**
4. Tap **Publish to Instagram Now**
5. Check Instagram — your post should appear within 30 seconds!

---

## Daily Workflow (Once Everything Is Set Up)

```
Mon/Wed/Fri 8AM  →  Pipeline runs automatically
                 →  3 posts appear in your dashboard

Open dashboard on iPad anytime that day
  →  Review each post (takes 5 minutes)
  →  Edit caption if needed
  →  Tap Publish
  →  Done ✓
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| "Wrong password" | Check DASHBOARD_PASSWORD in your .env |
| Web app shows error 500 | Go to PythonAnywhere → Web → "Error log" to see details |
| Pipeline ran but no posts | Check the task log in PythonAnywhere → Tasks |
| "Claude API error" | Check ANTHROPIC_API_KEY in .env is correct |
| Canva says "token expired" | Open dashboard → tap "Connect Canva" again |
| Instagram 401 error | Token expired — get a new one (every 60 days) |
| No images on posts | Check Canva template IDs are correct in .env |

---

## Keeping It Running

### Every 60 days — refresh your Instagram token:

In PythonAnywhere Bash console:
```bash
cd /home/yourusername/repo/health-agent
source venv/bin/activate
python main.py refresh-token
```

Copy the new token and update `INSTAGRAM_ACCESS_TOKEN` in your .env

### Getting code updates:

When new features are added to the project:
```bash
cd /home/yourusername/repo
git pull
cd health-agent
source venv/bin/activate
pip install -r requirements.txt
```

Then go to Web tab → Reload

---

*You're all set. The agent now runs 24/7 without needing your iPad on.*
