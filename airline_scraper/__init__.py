"""
Standalone ADK agent that scrapes https://www.schiphol.nl/en/airlines,
finds each airline's official EU261 compensation/claim page, and stores
the results in airlines_claims.json.

Run with:
    adk run airline_scraper
"""

import concurrent.futures
import json
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
from playwright.sync_api import sync_playwright

from google.adk.agents import Agent

SCHIPHOL_AIRLINES_URL = "https://www.schiphol.nl/en/airlines"
OUTPUT_FILE = "airlines_claims.json"
_BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _playwright_fetch(url: str) -> str:
    """Run Playwright in a thread-pool thread (avoids asyncio loop conflict)."""
    def _run():
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent=_BROWSER_UA)
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(5000)
            html = page.content()
            browser.close()
            return html

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(_run).result()


def scrape_schiphol_airlines() -> dict:
    """Scrape the full list of airlines operating from Schiphol airport.

    Returns:
        Dictionary with 'airlines' list, each entry having 'name' and
        'schiphol_url', plus a 'count'.
    """
    html = _playwright_fetch(SCHIPHOL_AIRLINES_URL)
    soup = BeautifulSoup(html, "html.parser")
    airlines = []
    seen = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        name = a.get_text(strip=True)
        if (
            "/en/airlines" in href
            and href.rstrip("/") != "/en/airlines"
            and name
            and name not in seen
        ):
            full_url = (
                "https://www.schiphol.nl" + href
                if href.startswith("/")
                else href
            )
            airlines.append({"name": name, "schiphol_url": full_url})
            seen.add(name)

    return {"airlines": airlines, "count": len(airlines)}


_THIRD_PARTY_DOMAINS = {
    "airadvisor", "claimcompass", "flightright", "bottonline",
    "airhelp", "claimdeck", "flightdelayclaims", "compensair",
    "euclaim", "refundme", "flightdelays",
}


def search_airline_claim_page(airline_name: str) -> dict:
    """Search for an airline's official EU261 compensation or claim submission page.

    Args:
        airline_name: Full name of the airline (e.g. 'British Airways').

    Returns:
        Dictionary with 'airline', 'claim_url', and 'claim_page_title'.
    """
    query = f"{airline_name} official EU261 compensation claim form"

    try:
        results = DDGS().text(query, max_results=10)

        for r in results:
            url = r.get("href", "")
            title = r.get("title", "")
            # Skip known third-party claim aggregators
            if any(d in url for d in _THIRD_PARTY_DOMAINS):
                continue
            if url.startswith("http"):
                return {
                    "airline": airline_name,
                    "claim_url": url,
                    "claim_page_title": title,
                }

        return {
            "airline": airline_name,
            "claim_url": None,
            "claim_page_title": None,
            "error": "No official results found",
        }

    except Exception as e:
        return {
            "airline": airline_name,
            "claim_url": None,
            "claim_page_title": None,
            "error": str(e),
        }


def save_to_json(airlines_data: list[dict]) -> dict:
    """Save the collected airline claim page data to airlines_claims.json.

    Args:
        airlines_data: List of dicts with airline name and claim URL.

    Returns:
        Dictionary confirming the file path and entry count.
    """
    output = {
        "generated_at": datetime.now().isoformat(),
        "source": SCHIPHOL_AIRLINES_URL,
        "airlines": airlines_data,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    return {"success": True, "file": OUTPUT_FILE, "count": len(airlines_data)}


root_agent = Agent(
    name="airline_scraper",
    model="gemini-2.5-flash",
    description=(
        "Scrapes Schiphol airport airlines and finds each airline's "
        "official EU261 claim page, then saves results to JSON."
    ),
    instruction="""You are a data collection agent. Execute these steps in order:

1. Call scrape_schiphol_airlines() to get the complete list of airlines at Schiphol.
2. For every airline in the returned list, call search_airline_claim_page(airline_name)
   to find their official EU261 compensation or claim submission page.
3. Build a results list where each entry is:
   {"name": <airline_name>, "claim_url": <url or null>, "claim_page_title": <title or null>}
4. Call save_to_json(airlines_data) with the complete results list.
5. Confirm how many airlines were processed and the output file name.

Process every airline without skipping any. If a claim page is not found,
include the entry with claim_url set to null.""",
    tools=[scrape_schiphol_airlines, search_airline_claim_page, save_to_json],
)
