# Morning News Agent

Sends you a daily email (World / South Africa / Tech / Finance headlines + an affirmation)
and a matching podcast episode you can play on your phone, delivered by GitHub Actions
every morning — no laptop required.

## What it does
1. Calls the OpenAI Responses API with **web search** enabled to pull today's actual news
   from reputable sources (BBC, Reuters, AP, NPR, Guardian).
2. Structures it into 4 sections + a closing affirmation.
3. Emails it to you via Gmail SMTP.
4. Converts that same brief into a spoken-word audio episode (no second AI call) and
   publishes it to a podcast RSS feed you can subscribe to in any podcast app.
5. Runs automatically every morning via a GitHub Actions cron job.

---

## Step 1 — Create a Gmail App Password
Regular Gmail passwords won't work for SMTP automation. You need an **App Password**:

1. Go to your Google Account → **Security**.
2. Turn on **2-Step Verification** if it isn't already on (required for App Passwords).
3. Go to **Security → App passwords** (search "App passwords" in the account search bar if you can't find it).
4. Create one named e.g. `news-agent`. Google gives you a 16-character password.
5. Copy it — you'll paste it into GitHub as a secret in Step 3 (you won't see it again).

## Step 2 — Get an OpenAI API key
1. Go to https://platform.openai.com/api-keys.
2. Create a new key and copy it.
3. This uses your OpenAI API credits (uses model `gpt-5.4` with the built-in `web_search`
   tool). Web search carries a small per-call fee on top of tokens, but at one call/day
   this should still only be cents a month.

## Step 3 — Create the GitHub repo
1. Create a new GitHub repo. Note: the podcast feed needs GitHub Pages, which on the
   free plan only works on **public** repos — this repo is public. Your email address
   and secrets stay protected either way (see "Podcast / RSS feed" below).
2. Upload these files, keeping the folder structure:
   ```
   news_agent.py
   podcast.py
   requirements.txt
   .github/workflows/daily-new.yml
   ```
3. Go to your repo → **Settings → Secrets and variables → Actions → New repository secret**.
   Add these 4 secrets:

   | Secret name           | Value                                  |
   |-----------------------|-----------------------------------------|
   | `OPENAI_API_KEY`      | your key from Step 2                    |
   | `GMAIL_ADDRESS`       | the Gmail address sending the email     |
   | `GMAIL_APP_PASSWORD`  | the 16-character app password from Step 1 |
   | `RECIPIENT_EMAIL`     | where you want the brief sent (can be the same Gmail address) |

## Step 4 — Test it manually
1. Go to your repo's **Actions** tab.
2. Click **Daily Morning Brief** on the left (this is the only workflow — it handles
   both the email and the podcast episode in one run).
3. Click **Run workflow** (dropdown, top right) → **Run workflow**.
4. Watch it run — should take under a couple of minutes. Check your inbox, and check
   the feed URL below once it finishes.

If it fails, click into the run to see the error log — most common issues are a typo
in a secret name or 2-Step Verification not being enabled before creating the app password.

## Step 5 — Let it run on schedule
Once the manual test works, you're done — it'll fire automatically every morning around
**05:47 SAST (03:47 UTC)**.

That's deliberately not a round hour: GitHub Actions scheduled runs queue behind every
other repo firing at popular times like `0 4 * * *`, which caused multi-hour delays.
GitHub doesn't guarantee exact timing for scheduled workflows, but avoiding round hours
meaningfully cuts the delay.

To change the time: edit the `cron:` line in `.github/workflows/daily-new.yml`.
Cron format is `minute hour * * *` in **UTC**.

## Podcast / RSS feed
Every run also builds an audio episode (OpenAI TTS, reusing the same brief text — no
extra AI call) and publishes it to the `gh-pages` branch as a podcast feed.

Subscribe to this URL in any podcast app (Apple Podcasts, Overcast, Spotify, etc.):
```
https://kavyakaushik11.github.io/Morning-updates/feed.xml
```

Notes:
- Episodes older than 30 days are pruned automatically so the feed doesn't grow forever.
- The feed and audio files are public (anyone with the link could access them), since
  GitHub Pages requires that on the free plan. Your GitHub Secrets (API keys, email
  credentials) are never exposed by this — they stay encrypted regardless of repo or
  Pages visibility.
- To change the voice or wording, edit `TTS_VOICE` / `brief_to_script()` in `podcast.py`.

---

## Local testing (optional, on your Mac)
If you want to test locally before pushing to GitHub:

```bash
cd news-agent
pip install -r requirements.txt

export OPENAI_API_KEY="your-key"
export GMAIL_ADDRESS="you@gmail.com"
export GMAIL_APP_PASSWORD="your-16-char-app-password"
export RECIPIENT_EMAIL="you@gmail.com"

python news_agent.py
```

## Customizing further
- **Change topics**: edit the `USER_PROMPT` string in `news_agent.py`.
- **Change tone/sources**: edit `SYSTEM_PROMPT`.
- **Change email styling**: edit `build_email_html()`.
