"""
search_handler.py
Uses Google Gemini 1.5 Flash (FREE tier) with Google Search grounding
to find summer 2026 opportunities for Uzbekistan students.
"""

import os
import json
import re
import time
from google import genai
from google.genai.types import GenerateContentConfig, GoogleSearch, Tool

# The new SDK automatically picks up the GEMINI_API_KEY environment variable.
client = genai.Client()

SEARCH_QUERIES = [
    "fully funded summer internship 2026 Uzbekistan international students",
    "summer school program 2026 Central Asia Uzbekistan full scholarship",
    "funded summer tech engineering internship 2026 international students Central Asia",
    "DAAD summer school 2026 fully funded Uzbekistan eligible",
    "ERASMUS+ summer school 2026 fully funded Uzbekistan",
    "summer research fellowship 2026 developing countries no application fee",
    "fully funded undergraduate summer program 2026 Uzbekistan",
    "United Nations summer 2026 internship Uzbekistan youth",
    "summer institute 2026 international students fully funded Europe Uzbekistan",
    "free summer leadership program 2026 international students Uzbekistan"
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

MODEL_NAME = "gemini-1.5-flash"
DELAY_BETWEEN_QUERIES = 10
MAX_RETRIES = 3

def search_for_opportunities(query: str) -> list:
    """Run a single search query using Gemini + Google Search grounding, with retry."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # New GenAI syntax moves tools and system prompts into the config object
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=f"Search query: {query}\n\nFind real summer 2026 programs for students from Uzbekistan matching the criteria. Return a JSON array only.",
                config=GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    tools=[Tool(google_search=GoogleSearch())],
                    temperature=0.2, # Lower temp for more reliable JSON formatting
                )
            )

            text = response.text.strip()
            text = re.sub(r"```json\s*", "", text)
            text = re.sub(r"```\s*", "", text)
            text = text.strip()

            json_match = re.search(r"\[.*\]", text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return []

        except json.JSONDecodeError as e:
            print(f"  ⚠ JSON parse error for '{query}': {e}")
            return []
        except Exception as e:
            err = str(e)
            if "429" in err or "quota" in err.lower():
                wait = 30 * attempt
                print(f"  ⏳ Rate limited (attempt {attempt}/{MAX_RETRIES}), waiting {wait}s...")
                time.sleep(wait)
                if attempt == MAX_RETRIES:
                    print(f"  ⚠ Giving up on '{query}' after {MAX_RETRIES} attempts")
                    return []
            else:
                print(f"  ⚠ Search error for '{query}': {e}")
                return []
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

            if link in seen_links or name in seen_names:
                continue

            if float(opp.get("application_fee_usd", 0)) > 0:
                continue

            if opp.get("funding_status") != "fully_funded":
                if float(opp.get("estimated_cost_usd", 9999)) > 700:
                    continue

            if not opp.get("uzbekistan_eligible", False):
                continue

            seen_links.add(link)
            seen_names.add(name)
            all_opportunities.append(opp)
            added += 1

        print(f"     ✓ {added} new opportunities found")

        if i < len(SEARCH_QUERIES):
            time.sleep(DELAY_BETWEEN_QUERIES)

    print(f"\n  📋 Total unique opportunities: {len(all_opportunities)}")
    return all_opportunities