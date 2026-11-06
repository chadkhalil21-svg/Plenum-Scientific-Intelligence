"""Federated read-only metadata retrieval from three scientific databases.

No restricted full-text scraping, external API payments or autonomous citation
claims. Each provider is independently queried in a bounded thread pool.
"""
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json

MAX_BODY = 240000
PROVIDERS = ("openalex", "europepmc", "semanticscholar")


def _read_json(url, opener=urlopen):
    req = Request(url, headers={"User-Agent":"PlenumScientificIntelligence/0.7 research-metadata"})
    with opener(req, timeout=12) as response:
        body = response.read(MAX_BODY + 1)
    if len(body) > MAX_BODY:
        raise ValueError("Metadata response exceeded safety limit")
    return json.loads(body)


def _normalize(provider, item):
    if provider == "openalex":
        loc = item.get("primary_location") or {}
        return {"source":provider, "id":item.get("id"),
                "title":item.get("title"), "year":item.get("publication_year"),
                "doi":item.get("doi"), "url":loc.get("landing_page_url") or item.get("id")}
    if provider == "europepmc":
        year=item.get("pubYear")
        try: year=int(year)
        except (ValueError, TypeError): year=None
        doi=item.get("doi")
        ref=item.get("source","MED") + "/" + str(item.get("id",""))
        return {"source":provider, "id":ref, "title":item.get("title"),
                "year":year, "doi":("https://doi.org/"+doi) if doi else None,
                "url":"https://europepmc.org/article/"+ref}
    if provider == "semanticscholar":
        doi=(item.get("externalIds") or {}).get("DOI")
        return {"source":provider,"id":item.get("paperId"),
                "title":item.get("title"),"year":item.get("year"),
                "doi":("https://doi.org/"+doi) if doi else None,
                "url":item.get("url")}
    raise ValueError("Invalid bibliographic provider")


def _get_provider(name, query, fetcher):
    encoded = urlencode({"query":query})
    if name == "openalex":
        url="https://api.openalex.org/works?"+urlencode({"search":query,"per_page":3})
        raw=fetcher(url).get("results",[])
    elif name == "europepmc":
        url=("https://www.ebi.ac.uk/europepmc/webservices/rest/search?" +
             urlencode({"query":query,"format":"json","pageSize":3,"resultType":"lite"}))
        raw=fetcher(url).get("resultList",{}).get("result",[])
    elif name == "semanticscholar":
        url=("https://api.semanticscholar.org/graph/v1/paper/search?" +
             urlencode({"query":query,"limit":3,"fields":"title,year,url,externalIds"}))
        raw=fetcher(url).get("data",[])
    else:
        raise ValueError("Unsupported provider")
    return {
        "provider":name, "status":"retrieved_metadata",
        "records":[_normalize(name,r) for r in raw[:3] if r.get("title")],
        "query_url":url, "citation_verified":False,
    }


def search_federated(query, offline=True, fetcher=_read_json):
    if not isinstance(query,str) or not 1<=len(query.strip())<=250:
        raise ValueError("Search query must contain 1..250 characters")
    if offline:
        return {"providers":[{"provider":p,"status":"skipped_offline","records":[]}
                             for p in PROVIDERS],
                "records":[], "all_providers_healthy":None,
                "scientific_truth_verified":False}
    def one(provider):
        try:
            return _get_provider(provider,query,fetcher)
        except Exception as exc:
            return {"provider":provider,"status":"unavailable",
                    "error_type":type(exc).__name__,"records":[]}
    with ThreadPoolExecutor(max_workers=3) as pool:
        outcomes=list(pool.map(one,PROVIDERS))
    # Prefer DOI identifiers, then title-year. Preserve source attribution.
    unique = {}
    for provider in outcomes:
        for record in provider["records"]:
            doi=(record.get("doi") or "").lower().strip()
            key=("doi:"+doi) if doi else (
                "title:"+str(record.get("title","")).lower().strip()
                +" year:"+str(record.get("year")))
            if key not in unique:
                unique[key]={**record,"also_indexed_by":[record["source"]]}
            elif record["source"] not in unique[key]["also_indexed_by"]:
                unique[key]["also_indexed_by"].append(record["source"])
    return {
        "providers":outcomes, "records":list(unique.values()),
        "all_providers_healthy":all(x["status"]=="retrieved_metadata" for x in outcomes),
        "scientific_truth_verified":False,
        "limitations":"Public metadata only. Provider rate limits and attribution; no full-text or experimental validation.",
    }
