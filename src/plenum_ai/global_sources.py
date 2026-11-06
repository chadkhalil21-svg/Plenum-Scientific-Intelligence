"""Five-source federated scientific bibliography (public metadata only).

Integrates the existing concurrently queried OpenAlex, Europe PMC and Semantic
Scholar providers with arXiv Atom and US DOE OSTI JSON. Every API failure is
reported by provider. Nothing is mistaken for a verified full-text conclusion.

Materials Project is listed separately as credentials_required: its official
API normally requires the user's personal MP_API_KEY. Never put that key in a
public GitHub repo, output artifact, URL or telemetry log.
"""
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET
import json
import re

from .federated_sources import search_federated

MAX_BYTES = 250_000
ATOM = "{http://www.w3.org/2005/Atom}"
ARXIV = "{http://arxiv.org/schemas/atom}"


def _get(url, opener=urlopen):
    request = Request(url, headers={
        "User-Agent": "PlenumScientificIntelligence/1.3 bounded-public-literature",
        "Accept": "application/atom+xml, application/json",
    })
    with opener(request, timeout=18) as stream:
        data = stream.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("Literature metadata response exceeds bounded limit")
    return data


def arxiv_query_url(query):
    if not isinstance(query, str) or not 1 <= len(query.strip()) <= 250:
        raise ValueError("Invalid arXiv query")
    safe_words = re.findall(r"[a-zA-Z0-9-]{2,45}", query)[:8]
    if not safe_words:
        raise ValueError("arXiv search needs alphanumeric words")
    return "https://export.arxiv.org/api/query?" + urlencode({
        "search_query": " AND ".join("all:" + token for token in safe_words),
        "start": 0, "max_results": 3,
    })


def parse_arxiv(data):
    if b"<!DOCTYPE" in data.upper() or b"<!ENTITY" in data.upper():
        raise ValueError("Untrusted XML DTD/entity in arXiv response")
    root = ET.fromstring(data)
    if root.tag != ATOM + "feed":
        raise ValueError("Expected arXiv Atom feed")
    records = []
    for entry in root.findall(ATOM + "entry")[:3]:
        title = " ".join((entry.findtext(ATOM + "title") or "").split())
        ident = (entry.findtext(ATOM + "id") or "").strip()
        if len(title) < 3 or (not ident.startswith("https://arxiv.org/abs/")
                               and not ident.startswith("http://arxiv.org/abs/")):
            continue
        ident = ident.replace("http://arxiv.org/", "https://arxiv.org/", 1)
        doi = entry.findtext(ARXIV + "doi")
        doi = ("https://doi.org/" + doi.strip()) if doi else None
        date = (entry.findtext(ATOM + "published") or "")[:4]
        records.append({
            "source": "arxiv", "id": ident, "title": title,
            "year": int(date) if date.isdecimal() else None,
            "doi": doi, "url": ident,
        })
    return records


def osti_query_url(query):
    if not isinstance(query, str) or not 1 <= len(query.strip()) <= 250:
        raise ValueError("Invalid OSTI query")
    return "https://www.osti.gov/api/v1/records?" + urlencode({
        "q": query, "rows": 3, "page": 1,
    })


def parse_osti(data):
    obj = json.loads(data)
    if isinstance(obj, list):
        results = obj
    elif isinstance(obj, dict) and isinstance(obj.get("records"), list):
        results = obj["records"]
    else:
        raise ValueError("Unknown OSTI records response format")
    records = []
    for entry in results[:3]:
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("title") or "").strip()
        ident = entry.get("osti_id")
        if not name or ident is None:
            continue
        doi = str(entry.get("doi") or "").strip()
        if doi:
            doi = doi if doi.startswith("https://doi.org/") else "https://doi.org/" + doi
        pub = str(entry.get("publication_date") or "")
        year = pub[:4]
        records.append({
            "source": "osti", "id": str(ident), "title": name,
            "year": int(year) if year.isdecimal() else None,
            "doi": doi or None,
            "url": "https://www.osti.gov/biblio/" + str(ident),
        })
    return records


def _provider_run(name, query, opener):
    if name == "arxiv":
        url = arxiv_query_url(query)
        parse = parse_arxiv
    elif name == "osti":
        url = osti_query_url(query)
        parse = parse_osti
    else:
        raise ValueError("Provider not allowlisted")
    rows = parse(_get(url, opener=opener))
    return {"provider": name, "status": "retrieved_metadata", "records": rows,
            "query_url": url, "citation_verified": False}


def _merged(records):
    result = {}
    for item in records:
        doi = str(item.get("doi") or "").lower().strip()
        if doi and doi.startswith("https://doi.org/"):
            key = "doi:" + doi
        else:
            key = ("title:" + " ".join(str(item.get("title") or "").lower().split())
                   + " year:" + str(item.get("year")))
        if key not in result:
            result[key] = {**item, "also_indexed_by": [item["source"]]}
        elif item["source"] not in result[key]["also_indexed_by"]:
            result[key]["also_indexed_by"].append(item["source"])
    return list(result.values())


def global_literature(query, offline=True, fetcher=None, opener=urlopen):
    if not isinstance(query, str) or not 1 <= len(query.strip()) <= 250:
        raise ValueError("Public query must be 1..250 characters")
    if offline:
        return {
            "providers": [{"provider": p, "status": "skipped_offline", "records": []}
                          for p in ("openalex", "europepmc", "semanticscholar", "arxiv", "osti")],
            "records": [], "all_providers_healthy": None,
            "scientific_truth_verified": False,
            "materials_project_status": "not_requested_requires_private_API_key",
        }
    def current():
        if fetcher is None:
            return search_federated(query, offline=False)
        return search_federated(query, offline=False, fetcher=fetcher)
    def one(name):
        try:
            return _provider_run(name, query, opener)
        except Exception as exc:
            return {"provider": name, "status": "unavailable",
                    "error_type": type(exc).__name__, "records": []}
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(current),
                   pool.submit(one, "arxiv"),
                   pool.submit(one, "osti")]
        first, arxiv, osti = (future.result() for future in futures)
    providers = list(first["providers"]) + [arxiv, osti]
    records = _merged([item for p in providers for item in p["records"]])
    return {
        "providers": providers, "records": records,
        "all_providers_healthy": all(p["status"] == "retrieved_metadata" for p in providers),
        "scientific_truth_verified": False,
        "materials_project_status": "not_requested_requires_private_API_key",
        "limitations": [
            "Read-only metadata, not independent scientific verification.",
            "Some sources overlap and record identifiers can vary.",
            "Rate limits and transient provider failures remain visible.",
            "Materials Project API requires a separate user-provided credential.",
        ],
    }
