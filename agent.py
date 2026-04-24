"""
agent.py
Main entry point for the Summer Opportunity Agent.

Flow:
  1. Connect to Google Sheets
  2. Run web searches via OpenAI
  3. Add new opportunities to sheet
  4. Check for upcoming deadlines
  5. Send Telegram notifications
  6. Send daily summary
"""

import os
import sys
from datetime import datetime

from search_handler import run_all_searches
from sheets_handler import (
    get_sheet,
    get_existing_links,
    add_opportunities,
    get_upcoming_deadlines,
    get_total_count,
)
from telegram_handler import (
    notify_new_opportunities,
    notify_deadlines,
    send_daily_summary,
    send_error_alert,
)

SHEET_URL = (
    f"https://docs.google.com/spreadsheets/d/{os.environ.get('GOOGLE_SHEETS_ID', '')}"
)

# Alert on deadlines within this many days
DEADLINE_ALERT_DAYS = 14


def check_env():
    """Verify all required environment variables are set."""
    required = [
        "GEMINI_API_KEY",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
        "GOOGLE_SHEETS_ID",
        "GOOGLE_CREDENTIALS_JSON",
    ]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}"
        )


def main():
    start_time = datetime.now()
    print(f"\n{'=' * 50}")
    print(f"🚀 Summer Opportunity Agent")
    print(f"   Started: {start_time.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'=' * 50}\n")

    try:
        # 1. Validate environment
        check_env()

        # 2. Connect to Google Sheets
        print("📊 Connecting to Google Sheets...")
        worksheet = get_sheet()
        existing_links = get_existing_links(worksheet)
        print(f"   ✓ Connected | {len(existing_links)} existing opportunities\n")

        # 3. Search for opportunities
        print("🔍 Searching for opportunities...\n")
        opportunities = run_all_searches()

        # 4. Add new ones to sheet
        print("\n📥 Saving new opportunities to sheet...")
        new_opportunities = add_opportunities(worksheet, opportunities, existing_links)
        print(f"   ✓ {len(new_opportunities)} new opportunities added\n")

        # 5. Check upcoming deadlines
        print(f"⏰ Checking deadlines (next {DEADLINE_ALERT_DAYS} days)...")
        upcoming_deadlines = get_upcoming_deadlines(worksheet, DEADLINE_ALERT_DAYS)
        print(f"   ✓ {len(upcoming_deadlines)} upcoming deadlines found\n")

        # 6. Get total count
        total_count = get_total_count(worksheet)

        # 7. Send Telegram notifications
        print("📱 Sending Telegram notifications...")

        if new_opportunities:
            notify_new_opportunities(new_opportunities, SHEET_URL)
            print(f"   ✓ Sent new opportunities notification ({len(new_opportunities)} items)")

        if upcoming_deadlines:
            notify_deadlines(upcoming_deadlines, SHEET_URL)
            print(f"   ✓ Sent deadline reminders ({len(upcoming_deadlines)} items)")

        # Always send daily summary
        send_daily_summary(len(new_opportunities), len(upcoming_deadlines), total_count, SHEET_URL)
        print("   ✓ Sent daily summary")

        # Done
        elapsed = (datetime.now() - start_time).seconds
        print(f"\n{'=' * 50}")
        print(f"✅ Agent completed in {elapsed}s")
        print(f"{'=' * 50}\n")

    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        try:
            send_error_alert(str(e))
        except Exception:
            pass  # Don't crash on notification failure
        sys.exit(1)


if __name__ == "__main__":
    main()
