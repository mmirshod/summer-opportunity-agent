"""
search_handler.py
Uses Google Gemini 2.0 Flash (FREE tier) with Google Search grounding
to find summer 2026 opportunities for Uzbekistan students.

Free tier limits: 1,500 requests/day, 15 RPM — plenty for daily runs.
Get your free API key at: https://aistudio.google.com/apikey
"""

import os
import json
import re
import time
import google.generativeai as genai

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Diverse queries to maximize coverage
SEARCH_QUERIES = [
    "fully funded summer internship 2026 Uzbekistan students apply",
    "summer school program 2026 open Central Asia Uzbekistan scholarship",
    "summer camp 2026 funded Uzbekistan eligible no application fee",
    "DAAD summer school 2026 Uzbekistan Central Asia",
    "ERASMUS+ summer school 2026 Uzbekistan eligible",
    "summer research fellowship 2026 developing countries Uzbekistan",
    "fully funded summer program 2026 undergraduate Uzbekistan",
    "United Nations summer 2026 internship Uzbekistan youth",
    "summer school Europe 2026 scholarship Uzbekistan no fee",
    "summer institute 2026 international students Uzbekistan funded",
]

SYSTEM_PROMPT = """You are an expert research assistant specializing in finding international academic and professional opportunities for students from Uzbekistan.

Your task: Use Google Search to find real, verified summer 2026 opportunities.

Return ONLY a raw JSON array — no markdown, no backticks, no explanation, no preamble.

Each item must follow this exact structure:
{
  "name": "Full Program Name",
  "type": "internship|summer_school|summer_camp|fellowship|research_program",
  "host_organization": "Organization or University Name",
  "host_country": "Country where program takes place",
  "description": "2-3 sentence description of what the program involves",
  "funding_status": "fully_funded|partially_funded|self_funded",
  "estimated_cost_usd": 0,
  "application_fee_usd": 0,
  "deadline": "YYYY-MM-DD (use best guess from page, or 'TBD')",
  "eligibility": "Who can apply — nationalities, year of study, etc.",
  "application_link": "https://direct-link-to-application-or-program-page",
  "uzbekistan_eligible": true
}

HARD FILTERS — only include opportunities where ALL of the following are true:
1. Open to students from Uzbekistan (or broadly Central Asia / all nationalities)
2. Takes place Summer 2026 (June, July, or August 2026)
3. Fully funded OR personal cost is under $700 total (accommodation + travel included where possible)
4. Application fee is exactly $0 — no exceptions
5. Deadline has NOT yet passed (today is April 2026)
6. The program actually exists — no hallucinated results, verify via search

If nothing matching is found, return: []"""

# Gemini model with Google Search grounding (free tier)
_model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    tools=["google_search_retrieval"],
    system_instruction=SYSTEM_PROMPT,
)


def search_for_opportunities(query: str) -> list:
    """Run a single search query using Gemini + Google Search grounding."""
    try:
        response = _model.generate_content(
            f"Search query: {query}\n\n"
            "Find real summer 2026 programs for students from Uzbekistan matching the criteria. "
            "Return a JSON array only."
        )

        text = response.text.strip()

        # Strip any accidental markdown fences
        text = re.sub(r"```json\s*", "", text)
        text = re.sub(r"```\s*", "", text)
        text = text.strip()

        # Extract JSON array
        json_match = re.search(r"\[.*\]", text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return []

    except json.JSONDecodeError as e:
        print(f"  ⚠ JSON parse error for '{query}': {e}")
        return []
    except Exception as e:
        print(f"  ⚠ Search error for '{query}': {e}")
        return []


def run_all_searches() -> list:
    """
    Run all search queries, deduplicate results,
    and apply final validation filters.
    """
    all_opportunities = []
    seen_links = set()
    seen_names = set()

    for i, query in enumerate(SEARCH_QUERIES, 1):
        print(f"  🔍 [{i}/{len(SEARCH_QUERIES)}] {query}")
        results = search_for_opportunities(query)
        added = 0

        for opp in results:
            link = opp.get("application_link", "").strip()
            name = opp.get("name", "").strip().lower()

            if not name or not link:
                continue

            # Deduplicate
            if link in seen_links or name in seen_names:
                continue

            # Hard filter: no application fee
            if float(opp.get("application_fee_usd", 0)) > 0:
                continue

            # Hard filter: cost under $700 for non-fully-funded
            if opp.get("funding_status") != "fully_funded":
                if float(opp.get("estimated_cost_usd", 9999)) > 700:
                    continue

            # Must be Uzbekistan eligible
            if not opp.get("uzbekistan_eligible", False):
                continue

            seen_links.add(link)
            seen_names.add(name)
            all_opportunities.append(opp)
            added += 1

        print(f"     ✓ {added} new opportunities found")

        # Rate limiting between searches
        if i < len(SEARCH_QUERIES):
            time.sleep(2)

    print(f"\n  📋 Total unique opportunities: {len(all_opportunities)}")
    return all_opportunities
