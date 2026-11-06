"""Minimal OpenAlex metadata adapter. Retrieved literature is never instructions."""
import json
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = "https://api.openalex.org/works"


def paper_record(work):
    location = work.get("primary_location") or {}
    return {
        "id": work.get("id"),
        "title": work.get("title") or "Untitled",
        "year": work.get("publication_year"),
        "doi": work.get("doi"),
        "url": location.get("landing_page_url") or work.get("id"),
    }


def search_papers(query, limit=5, opener=urlopen):
    if not query.strip():
        raise ValueError("Research query cannot be empty")
    if not 1 <= limit <= 10:
        raise ValueError("Limit must be from 1 to 10")
    params = {"search": query, "per_page": limit}
    if os.getenv("OPENALEX_API_KEY"):
        params["api_key"] = os.environ["OPENALEX_API_KEY"]
    request = Request(BASE + "?" + urlencode(params), headers={"User-Agent": "PlenumScientificIntelligence/0.1"})
    with opener(request, timeout=20) as response:
        payload = json.load(response)
    return [paper_record(work) for work in payload.get("results", [])[:limit]]
