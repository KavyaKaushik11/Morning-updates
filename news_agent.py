#!/usr/bin/env python3
"""
Morning News Agent
-------------------
Gathers a BBC Global News-style morning brief across four sections:
  1. World headlines (politics, disasters, conflict)
  2. South Africa news (Cape Town, Joburg, national)
  3. Tech news (big tech moves + startups)
  4. Finance / markets
...then closes with an original affirmation, and emails the result via Gmail SMTP.

Required environment variables (set as GitHub Secrets in production):
  OPENAI_API_KEY      - your OpenAI API key
  GMAIL_ADDRESS       - the Gmail address sending the email
  GMAIL_APP_PASSWORD  - a Gmail App Password (NOT your normal password)
  RECIPIENT_EMAIL     - where the brief should be sent (can be same as GMAIL_ADDRESS)
"""

import os
import json
import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

import requests

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")
RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL", GMAIL_ADDRESS)

MODEL = "gpt-5.4"

SYSTEM_PROMPT = """You are a careful morning news briefing assistant, styled after the BBC Global News \
podcast: factual, concise, and sourced from wire services and public broadcasters (BBC, Reuters, \
AP, NPR, The Guardian) rather than aggregators, blogs, or clickbait sites. You MUST use the web_search \
tool to find TODAY's actual current news before writing anything - never rely on prior knowledge, since \
it may be stale. Cross-check that a story is being reported by more than one reputable outlet before \
including it where possible. Do not include opinion pieces framed as news. Write in your own words - \
never quote sources directly. Respond with ONLY valid JSON, no markdown fences, no preamble."""

USER_PROMPT = """Build today's morning brief. Search the web for current news, then return a single JSON \
object with exactly these keys:

"global_headlines": array of exactly 5 objects {"headline": str, "detail": str (1-2 sentences)} - \
  top world political news, natural disasters, and war/conflict updates, similar in scope/tone to \
  BBC Global News.

"south_africa": array of exactly 5 objects {"headline": str, "detail": str} - important news about \
  Cape Town, Johannesburg, and South Africa nationally (politics, economy, infrastructure, major \
  incidents) - only significant items, not minor local stories.

"tech": array of exactly 5 objects {"headline": str, "detail": str} - notable changes at big tech \
  companies (product launches, leadership, major decisions) plus 1-2 interesting startups and what \
  they're building.

"finance": array of exactly 5 objects {"headline": str, "detail": str} - brief market moves, \
  economic projections, and notable financial news.

"affirmation": a short ORIGINAL 2-3 sentence affirmation (your own words, not a quote from any real \
  person) about self-belief, taking the leap, and having faith.

Return ONLY the JSON object."""


def call_openai_with_search():
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set")

    response = requests.post(
        "https://api.openai.com/v1/responses",
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL,
            "instructions": SYSTEM_PROMPT,
            "input": USER_PROMPT,
            "tools": [{"type": "web_search"}],
            "max_output_tokens": 4000,
        },
        timeout=120,
    )
    response.raise_for_status()
    data = response.json()

    # The Responses API gives a convenience field with the final assembled text,
    # but we build it manually here in case that's absent in a given response shape.
    full_text = data.get("output_text", "").strip()

    if not full_text:
        # Fall back to walking the output array for message text parts
        text_parts = []
        for item in data.get("output", []):
            if item.get("type") == "message":
                for part in item.get("content", []):
                    if part.get("type") == "output_text":
                        text_parts.append(part.get("text", ""))
        full_text = "\n".join(text_parts).strip()

    if not full_text:
        raise RuntimeError(f"No text content in OpenAI response: {json.dumps(data)[:500]}")

    # Strip any accidental markdown fences
    if full_text.startswith("```"):
        full_text = full_text.strip("`")
        if full_text.startswith("json"):
            full_text = full_text[4:]
        full_text = full_text.strip()

    return json.loads(full_text)


def section_html(title, items):
    rows = "".join(
        f"""<li style="margin-bottom:12px;">
                <strong style="color:#1a1a1a;">{item['headline']}</strong><br>
                <span style="color:#555;font-size:14px;">{item['detail']}</span>
            </li>"""
        for item in items
    )
    return f"""
    <h2 style="color:#0b4f6c;border-bottom:2px solid #0b4f6c;padding-bottom:4px;
               font-family:Arial,sans-serif;">{title}</h2>
    <ul style="list-style:none;padding-left:0;font-family:Arial,sans-serif;">{rows}</ul>
    """


def build_email_html(brief):
    today = datetime.now().strftime("%A, %d %B %Y")
    html = f"""
    <html>
    <body style="font-family:Arial,sans-serif;max-width:640px;margin:0 auto;padding:20px;">
        <h1 style="color:#0b4f6c;">Your Morning Brief</h1>
        <p style="color:#777;">{today}</p>

        {section_html("🌍 World Headlines", brief["global_headlines"])}
        {section_html("🇿🇦 South Africa", brief["south_africa"])}
        {section_html("💻 Tech", brief["tech"])}
        {section_html("📈 Markets & Finance", brief["finance"])}

        <div style="margin-top:30px;padding:20px;background:#f4f8f9;border-left:4px solid #0b4f6c;
                    border-radius:4px;">
            <p style="font-style:italic;color:#0b4f6c;font-size:16px;margin:0;">
                {brief["affirmation"]}
            </p>
        </div>

        <p style="color:#aaa;font-size:12px;margin-top:30px;">
            Sent by your personal news agent 🤖
        </p>
    </body>
    </html>
    """
    return html


def send_email(html_body):
    if not (GMAIL_ADDRESS and GMAIL_APP_PASSWORD and RECIPIENT_EMAIL):
        raise RuntimeError("GMAIL_ADDRESS, GMAIL_APP_PASSWORD, or RECIPIENT_EMAIL is not set")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Morning Brief - {datetime.now().strftime('%d %b %Y')}"
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = RECIPIENT_EMAIL
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, RECIPIENT_EMAIL, msg.as_string())


def main():
    print("Fetching today's news brief...")
    try:
        brief = call_openai_with_search()
    except Exception as e:
        print(f"Failed to fetch/parse news brief: {e}", file=sys.stderr)
        sys.exit(1)

    print("Building email...")
    html = build_email_html(brief)

    print("Sending email...")
    try:
        send_email(html)
    except Exception as e:
        print(f"Failed to send email: {e}", file=sys.stderr)
        sys.exit(1)

    print("Done - morning brief sent successfully.")


if __name__ == "__main__":
    main()
