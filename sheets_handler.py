"""
sheets_handler.py
Handles all Google Sheets operations:
- Auto-creates and formats the sheet on first run
- Adds new opportunities (deduplicates by URL)
- Reads upcoming deadlines for alerts
"""

import os
import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta, date

SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

HEADERS = [
    "Name",
    "Type",
    "Host Organization",
    "Country",
    "Funding Status",
    "Est. Cost (USD)",
    "App Fee (USD)",
    "Deadline",
    "Eligibility",
    "Application Link",
    "Description",
    "Date Found",
    "Status",
    "Notes",
]

# Column letter map for formatting
HEADER_RANGE = "A1:N1"


def get_sheet() -> gspread.Worksheet:
    """Connect to Google Sheets and return the Opportunities worksheet."""
    creds_json = os.environ["GOOGLE_CREDENTIALS_JSON"]
    creds_dict = json.loads(creds_json)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    gc = gspread.authorize(creds)

    sheet_id = os.environ["GOOGLE_SHEETS_ID"]
    spreadsheet = gc.open_by_key(sheet_id)

    # Create worksheet if it doesn't exist
    try:
        worksheet = spreadsheet.worksheet("Opportunities")
        # Ensure header exists
        if worksheet.row_count == 0 or worksheet.cell(1, 1).value != "Name":
            worksheet.insert_row(HEADERS, index=1)
            _format_header(worksheet)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(
            title="Opportunities", rows=1000, cols=20
        )
        worksheet.append_row(HEADERS)
        _format_header(worksheet)

    return worksheet


def _format_header(worksheet: gspread.Worksheet):
    """Apply nice formatting to the header row."""
    try:
        worksheet.format(
            HEADER_RANGE,
            {
                "backgroundColor": {"red": 0.18, "green": 0.36, "blue": 0.68},
                "textFormat": {
                    "bold": True,
                    "fontSize": 11,
                    "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0},
                },
                "horizontalAlignment": "CENTER",
            },
        )
        # Freeze header row
        worksheet.freeze(rows=1)
    except Exception as e:
        print(f"  ⚠ Header formatting skipped: {e}")


def get_existing_links(worksheet: gspread.Worksheet) -> set:
    """Return all application links already in the sheet (for deduplication)."""
    try:
        records = worksheet.get_all_records()
        return {
            str(r.get("Application Link", "")).strip()
            for r in records
            if r.get("Application Link")
        }
    except Exception as e:
        print(f"  ⚠ Could not fetch existing links: {e}")
        return set()


def add_opportunities(
    worksheet: gspread.Worksheet,
    opportunities: list,
    existing_links: set,
) -> list:
    """
    Add new opportunities to the sheet.
    Returns the list of opportunities that were actually added (new only).
    """
    new_ones = []
    today_str = datetime.now().strftime("%Y-%m-%d")

    rows_to_add = []

    for opp in opportunities:
        link = str(opp.get("application_link", "")).strip()
        if not link or link in existing_links:
            continue

        funding = opp.get("funding_status", "").replace("_", " ").title()
        opp_type = opp.get("type", "").replace("_", " ").title()

        row = [
            opp.get("name", "Unknown Program"),
            opp_type,
            opp.get("host_organization", ""),
            opp.get("host_country", ""),
            funding,
            opp.get("estimated_cost_usd", 0),
            opp.get("application_fee_usd", 0),
            opp.get("deadline", "TBD"),
            opp.get("eligibility", ""),
            link,
            opp.get("description", ""),
            today_str,
            "Active",
            "",
        ]

        rows_to_add.append(row)
        existing_links.add(link)
        new_ones.append(opp)

    # Batch insert for efficiency
    if rows_to_add:
        for row in rows_to_add:
            worksheet.append_row(row, value_input_option="USER_ENTERED")

    return new_ones


def get_upcoming_deadlines(
    worksheet: gspread.Worksheet, days_ahead: int = 14
) -> list:
    """
    Return list of active opportunities with deadlines within `days_ahead` days.
    Each returned record has an extra 'days_left' key.
    """
    today = date.today()
    cutoff = today + timedelta(days=days_ahead)
    upcoming = []

    DATE_FORMATS = [
        "%Y-%m-%d",
        "%d %B %Y",
        "%B %d, %Y",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%B %Y",  # Month Year only — treat as last day of month
    ]

    try:
        records = worksheet.get_all_records()
        for record in records:
            if record.get("Status", "Active") != "Active":
                continue

            deadline_str = str(record.get("Deadline", "")).strip()
            if not deadline_str or deadline_str.lower() in ("tbd", "rolling", ""):
                continue

            parsed = None
            for fmt in DATE_FORMATS:
                try:
                    dt = datetime.strptime(deadline_str, fmt)
                    # For "Month Year" format, use last day of that month
                    if fmt == "%B %Y":
                        import calendar
                        last_day = calendar.monthrange(dt.year, dt.month)[1]
                        parsed = date(dt.year, dt.month, last_day)
                    else:
                        parsed = dt.date()
                    break
                except ValueError:
                    continue

            if parsed is None:
                continue

            days_left = (parsed - today).days
            if 0 <= days_left <= days_ahead:
                record = dict(record)
                record["days_left"] = days_left
                record["deadline_date"] = parsed
                upcoming.append(record)

    except Exception as e:
        print(f"  ⚠ Error checking deadlines: {e}")

    # Sort by urgency
    upcoming.sort(key=lambda x: x["days_left"])
    return upcoming


def get_total_count(worksheet: gspread.Worksheet) -> int:
    """Return total number of tracked opportunities."""
    try:
        records = worksheet.get_all_records()
        return len(records)
    except Exception:
        return 0
