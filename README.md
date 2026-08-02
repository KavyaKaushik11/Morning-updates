# Morning News Agent

Sends you a daily email (World / South Africa / Tech / Finance headlines + an affirmation),
delivered by GitHub Actions every morning — no laptop required.

## What it does
1. Calls the Claude API with **web search** enabled to pull today's actual news
   from reputable sources (BBC, Reuters, AP, NPR, Guardian).
2. Structures it into 4 sections + a closing affirmation.
3. Emails it to you via Gmail SMTP.
4. Runs automatically every morning via a GitHub Actions cron job.

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
1. Create a new **private** GitHub repo (private, since it'll reference your email address).
2. Upload these files, keeping the folder structure:
   ```
   news_agent.py
   requirements.txt
   .github/workflows/daily-news.yml
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
2. Click **Daily Morning Brief** on the left.
3. Click **Run workflow** (dropdown, top right) → **Run workflow**.
4. Watch it run — should take ~30-60 seconds. Check your inbox.

If it fails, click into the run to see the error log — most common issues are a typo
in a secret name or 2-Step Verification not being enabled before creating the app password.

## Step 5 — Let it run on schedule
Once the manual test works, you're done — it'll fire automatically every morning at
**06:00 SAST (04:00 UTC)**.

To change the time: edit the `cron:` line in `.github/workflows/daily-news.yml`.
Cron format is `minute hour * * *` in **UTC**. E.g. for 6:30am SAST → `30 4 * * *`.

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
