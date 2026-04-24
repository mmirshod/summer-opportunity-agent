"""
telegram_handler.py
Sends formatted Telegram notifications for:
- New opportunities discovered
- Upcoming deadline reminders
- Daily summary report
- Error alerts
"""

import os
import requests
from datetime import datetime


TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"
MAX_MSG_LENGTH = 3800  # Telegram hard limit is 4096, keep buffer


def _send(text: str, parse_mode: str = "HTML") -> bool:
    """Send a single Telegram message. Returns True on success."""
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    url = TELEGRAM_API.format(token=token)
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }

    try:
        resp = requests.post(url, json=payload, timeout=15)
        if not resp.ok:
            print(f"  ⚠ Telegram error {resp.status_code}: {resp.text[:200]}")
            return False
        return True
    except Exception as e:
        print(f"  ⚠ Telegram request failed: {e}")
        return False


def _split_and_send(messages: list[str]):
    """Send a list of message chunks in order."""
    for msg in messages:
        if msg.strip():
            _send(msg)


def _chunk_messages(header: str, entries: list[str], footer: str = "") -> list[str]:
    """
    Split a list of entry strings into Telegram-sized messages.
    Each chunk starts with the header (first chunk only) and ends with footer (last chunk only).
    """
    chunks = []
    current = header

    for entry in entries:
        if len(current) + len(entry) > MAX_MSG_LENGTH:
            chunks.append(current)
            current = entry
        else:
            current += entry

    current += footer
    chunks.append(current)
    return chunks


def notify_new_opportunities(opportunities: list, sheet_url: str):
    """Notify about newly found opportunities."""
    if not opportunities:
        return

    today = datetime.now().strftime("%B %d, %Y")
    header = (
        f"🎯 <b>New Opportunities Found!</b>\n"
        f"📅 {today} · {len(opportunities)} new program{'s' if len(opportunities) > 1 else ''}\n"
        f"{'─' * 30}\n\n"
    )

    TYPE_EMOJI = {
        "internship": "💼",
        "summer_school": "🎓",
        "summer school": "🎓",
        "summer_camp": "⛺",
        "summer camp": "⛺",
        "fellowship": "🏆",
        "research_program": "🔬",
        "research program": "🔬",
    }

    entries = []
    for opp in opportunities:
        funding = opp.get("funding_status", "").replace("_", " ").title()
        cost_usd = float(opp.get("estimated_cost_usd", 0))
        deadline = opp.get("deadline", "TBD")
        opp_type = opp.get("type", "").lower().replace("_", " ")

        type_emoji = TYPE_EMOJI.get(opp_type, "📋")
        funding_emoji = "💚" if "fully" in funding.lower() else "💛"
        cost_str = " · <b>FREE</b>" if cost_usd == 0 else f" · ~${int(cost_usd)}"

        entry = (
            f"{type_emoji} <b>{opp.get('name', 'Unknown Program')}</b>\n"
            f"   🌍 {opp.get('host_organization', '')} — {opp.get('host_country', '')}\n"
            f"   {funding_emoji} {funding}{cost_str}\n"
            f"   📅 Deadline: <b>{deadline}</b>\n"
            f"   🔗 <a href='{opp.get('application_link', '')}'>Apply Here</a>\n\n"
        )
        entries.append(entry)

    footer = f"\n📊 <a href='{sheet_url}'>View All in Google Sheets →</a>"
    chunks = _chunk_messages(header, entries, footer)
    _split_and_send(chunks)


def notify_deadlines(upcoming: list, sheet_url: str):
    """Send deadline reminder notifications."""
    if not upcoming:
        return

    today = datetime.now().strftime("%B %d, %Y")
    header = (
        f"⏰ <b>Deadline Reminders</b>\n"
        f"📅 {today} · {len(upcoming)} deadline{'s' if len(upcoming) > 1 else ''} approaching\n"
        f"{'─' * 30}\n\n"
    )

    entries = []
    for opp in upcoming:
        days_left = opp.get("days_left", 0)

        if days_left == 0:
            urgency = "🔴 <b>TODAY IS THE DEADLINE!</b>"
        elif days_left <= 3:
            urgency = f"🔴 <b>URGENT — {days_left} day{'s' if days_left > 1 else ''} left!</b>"
        elif days_left <= 7:
            urgency = f"🟠 <b>{days_left} days left</b>"
        else:
            urgency = f"🟡 {days_left} days left"

        link = opp.get("Application Link", "#")
        name = opp.get("Name", "Unknown")
        org = opp.get("Host Organization", "")
        country = opp.get("Country", "")
        deadline = opp.get("Deadline", "")
        funding = opp.get("Funding Status", "")

        entry = (
            f"{urgency}\n"
            f"📌 <b>{name}</b>\n"
            f"   🌍 {org} — {country}\n"
            f"   💰 {funding}\n"
            f"   📅 Deadline: <b>{deadline}</b>\n"
            f"   🔗 <a href='{link}'>Apply Now</a>\n\n"
        )
        entries.append(entry)

    footer = f"\n📊 <a href='{sheet_url}'>View All in Google Sheets →</a>"
    chunks = _chunk_messages(header, entries, footer)
    _split_and_send(chunks)


def send_daily_summary(
    new_count: int,
    deadline_count: int,
    total_count: int,
    sheet_url: str,
):
    """Send a brief daily status summary."""
    today = datetime.now().strftime("%A, %B %d, %Y")

    status_new = f"🆕 <b>{new_count}</b> new opportunit{'ies' if new_count != 1 else 'y'} found" if new_count > 0 else "✅ No new opportunities today (everything already tracked)"
    status_deadline = f"⏰ <b>{deadline_count}</b> deadline{'s' if deadline_count != 1 else ''} approaching" if deadline_count > 0 else "✅ No urgent deadlines"

    msg = (
        f"📊 <b>Daily Agent Report</b>\n"
        f"📅 {today}\n"
        f"{'─' * 30}\n\n"
        f"{status_new}\n"
        f"{status_deadline}\n"
        f"📋 Total tracked: <b>{total_count}</b> opportunities\n\n"
        f"📊 <a href='{sheet_url}'>Open Google Sheet →</a>"
    )
    _send(msg)


def send_error_alert(error: str):
    """Send an error notification."""
    msg = (
        f"❌ <b>Agent Error</b>\n"
        f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}\n\n"
        f"<code>{error[:500]}</code>\n\n"
        f"Please check GitHub Actions logs."
    )
    _send(msg)
