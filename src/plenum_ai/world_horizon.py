"""Read-only, bounded public horizon scanner across research and civilization.

Public data/news feeds are *not* a privileged university, military or
corporate connection. Their text is untrusted and never an agent instruction.
No subscription, payment, scraping of gated pages, geopolitical targeting,
external execution or unpublished patent material is accessed.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET
import json
import re

MAX_BYTES = 1_250_000
MAX_RESULTS = 4
MAX_SOURCES = 32
ATOM = "{http://www.w3.org/2005/Atom}"
_VALID_QUERY = re.compile(r"^[\w\s,\-.()/+]{2,120}$", re.UNICODE)

# Every endpoint is explicitly allowlisted and returns public metadata only.
# Availability is verified at runtime; an endpoint listed here is not asserted
# to be healthy, or an official institutional partnership.
SOURCES = {
    "mit_music_research": {"category":"music", "type":"feed",
        "url":"https://news.mit.edu/rss/topic/music", "publisher":"MIT Music and Technology"},
    "mit_visual_arts": {"category":"art", "type":"feed",
        "url":"https://news.mit.edu/rss/topic/arts", "publisher":"MIT Arts"},
    "mit_architecture": {"category":"design", "type":"feed",
        "url":"https://news.mit.edu/rss/topic/architecture", "publisher":"MIT Architecture"},
    "nih_biomedical_news": {"category":"health", "type":"feed",
        "url":"https://www.nih.gov/news-releases/feed.xml", "publisher":"U.S. National Institutes of Health"},
    "nsf_new_discoveries": {"category":"discoveries", "type":"feed",
        "url":"https://www.nsf.gov/rss/rss_www_news.xml", "publisher":"U.S. National Science Foundation"},
    "nsf_open_funding": {"category":"funding", "type":"feed",
        "url":"https://www.nsf.gov/rss/rss_www_funding_pgm_annc_inf.xml", "publisher":"U.S. National Science Foundation Funding"},
    "nature_journal_news": {"category":"journals", "type":"feed",
        "url":"https://www.nature.com/nature.rss", "publisher":"Nature Portfolio"},
    "mit_technology_review": {"category":"news", "type":"feed",
        "url":"https://www.technologyreview.com/stories.rss", "publisher":"MIT Technology Review"},
    "un_climate_environment": {"category":"environment", "type":"feed",
        "url":"https://news.un.org/feed/subscribe/en/news/topic/climate-change/feed/rss.xml", "publisher":"United Nations Climate News"},
    "arxiv_ai_new_submissions": {"category":"artificial_intelligence", "type":"feed",
        "url":"https://rss.arxiv.org/rss/cs.AI", "publisher":"arXiv Computer Science AI"},
    "arxiv_physics_new_submissions": {"category":"physics", "type":"feed",
        "url":"https://rss.arxiv.org/rss/physics", "publisher":"arXiv Physics"},
    "mit_labs": {"category":"universities", "type":"feed",
        "url":"https://news.mit.edu/rss/school/science", "publisher":"MIT News"},
    "harvard_research": {"category":"universities", "type":"feed",
        "url":"https://news.harvard.edu/gazette/section/science-technology/feed/", "publisher":"Harvard Gazette"},
    "nasa_research": {"category":"discoveries", "type":"feed",
        "url":"https://www.nasa.gov/feed/", "publisher":"NASA"},
    "dod_public_news": {"category":"defense", "type":"feed",
        "url":"https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=945&max=4",
        "publisher":"U.S. Department of Defense"},
    "un_global_news": {"category":"foreign_affairs", "type":"feed",
        "url":"https://news.un.org/feed/subscribe/en/news/all/rss.xml", "publisher":"United Nations News"},
    "darpa_public_research": {"category":"defense", "type":"feed",
        "url":"https://www.darpa.mil/rss.xml",
        "publisher":"DARPA public research news"},
    "un_geneva_releases": {"category":"foreign_affairs", "type":"feed",
        "url":"https://www.ungeneva.org/news-media/press-releases-list/rss.xml",
        "publisher":"UN Geneva public press releases"},
    "federal_reserve": {"category":"business", "type":"feed",
        "url":"https://www.federalreserve.gov/feeds/press_all.xml",
        "publisher":"Federal Reserve"},
    "crossref_journals": {"category":"journals", "type":"crossref",
        "url":"https://api.crossref.org/works", "publisher":"Crossref journal metadata"},
    "gdelt_headlines": {"category":"news", "type":"gdelt",
        "url":"https://api.gdeltproject.org/api/v2/doc/doc", "publisher":"GDELT global news index"},
    "world_bank": {"category":"business", "type":"world_bank",
        "url":"https://api.worldbank.org/v2/country/WLD/indicator/NY.GDP.MKTP.CD",
        "publisher":"World Bank Open Data"},
    "usgs_earthquakes": {"category":"environment", "type":"usgs",
        "url":"https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson",
        "publisher":"USGS earthquake observations"},
    "nasa_natural_events": {"category":"environment", "type":"eonet",
        "url":"https://eonet.gsfc.nasa.gov/api/v3/events",
        "publisher":"NASA EONET"},
    "github_public_code": {"category":"software", "type":"github",
        "url":"https://api.github.com/search/repositories",
        "publisher":"GitHub public repository index"},
}
CATEGORIES = tuple(sorted(set(item["category"] for item in SOURCES.values())))
# External services needing credentials/rights/review are catalogued, not faked.
REVIEW_GATED = {
    "youtube_global_video_search":"YOUTUBE_API_KEY required; NASA channel Atom already supported",
    "materials_project":"Owner-supplied Materials Project key required",
    "fred_economics":"FRED_API_KEY required",
    "smithsonian_collection_api":"Smithsonian / api.data.gov API key required",
    "patent_fulltext":"Respect USPTO/EPO search and bulk-data rules; review official API separately",
    "academic_institution_access":"Institution agreements/permissions required for restricted papers",
    "defense_internal_systems":"Not connected; public information only",
    "company_internal_systems":"Explicit owner authorization and OAuth required",
    "paid_press_apis":"Separate agreement, pricing and usage license required",
    "automated_software_merging":"Human review, branch protection and independent tests required",
}


def clean_query(query):
    if not isinstance(query, str) or not _VALID_QUERY.fullmatch(query.strip()):
        raise ValueError("Query must be 2-120 public topic characters, not code or credentials")
    return query.strip()


def request_url(key, query):
    if key not in SOURCES:
        raise ValueError("Unapproved public source")
    definition = SOURCES[key]
    base = definition["url"]
    kind = definition["type"]
    if kind in ("feed", "usgs"):
        return base
    if kind == "crossref":
        return base + "?" + urlencode({
            "query.bibliographic":query,"rows":4,
            "filter":"type:journal-article",
            "select":"DOI,title,container-title,published,URL,publisher",
        })
    if kind == "gdelt":
        return base + "?" + urlencode({
            "query":query, "mode":"artlist", "maxrecords":4,
            "format":"json","timespan":"1week",
        })
    if kind == "world_bank":
        return base + "?" + urlencode({
            "format":"json","mrnev":1,"per_page":2,
        })
    if kind == "eonet":
        return base + "?" + urlencode({"status":"open","limit":4})
    if kind == "github":
        return base + "?" + urlencode({
            "q":query+" in:name,description",
            "sort":"updated","order":"desc","per_page":4,
        })
    raise ValueError("Unrecognized approved data adapter")


def fetch_public(key, query, opener=urlopen):
    url = request_url(key, clean_query(query))
    expected = urlsplit(SOURCES[key]["url"]).netloc
    if urlsplit(url).netloc != expected:
        raise ValueError("Public source host mismatch")
    request = Request(url, headers={
        "User-Agent":"PlenumScientificIntelligence/1.8 read-only-public-signals",
        "Accept":"application/json,application/rss+xml,application/atom+xml,application/xml",
    })
    with opener(request, timeout=13) as response:
        data = response.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("Public provider exceeded response byte limit")
    return parse_public(key, data)


def _text(node, tag):
    if node is None:
        return ""
    return " ".join((node.findtext(tag) or "").split())[:350]


def _record(key, title, url, published=None, note=None):
    if not isinstance(title, str) or not isinstance(url, str):
        return None
    title = " ".join(title.split())[:330]
    url = url.strip()[:900]
    if len(title) < 3 or not url.startswith("https://"):
        return None
    return {
        "source":key, "category":SOURCES[key]["category"],
        "publisher":SOURCES[key]["publisher"],"title":title,"url":url,
        "published":str(published or "")[:55],
        "metadata_note":str(note or "")[:180],
        "primary_source_verified":False,
        "independent_fact_check_complete":False,
        "untrusted_external_content":True,
    }


def _feed(key, data):
    if b"<!DOCTYPE" in data.upper() or b"<!ENTITY" in data.upper():
        raise ValueError("XML entities or DTD not accepted")
    root = ET.fromstring(data)
    items = []
    if root.tag in ("rss","RDF", "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}RDF"):
        rss1 = "{http://purl.org/rss/1.0/}"
        dc_date = "{http://purl.org/dc/elements/1.1/}date"
        # RSS 1.0/RDF (including journal publishers) places <item> elements
        # under a default namespace, often directly under rdf:RDF.
        channel = root.find("channel")
        if channel is None:
            channel = root.find(rss1+"channel")
        rows = (channel.findall("item") if channel is not None else [])
        if not rows:
            rows = root.findall("item") + root.findall(rss1+"item")
        for node in rows[:MAX_RESULTS]:
            link = _text(node,"link") or _text(node,rss1+"link")
            if link.startswith("http://"):
                link = "https://" + link[len("http://"):]
            record = _record(key,
                             _text(node,"title") or _text(node,rss1+"title"),
                             link,
                             _text(node,"pubDate") or _text(node,"date") or _text(node,dc_date))
            if record:
                items.append(record)
    elif root.tag == ATOM+"feed":
        for node in root.findall(ATOM+"entry")[:MAX_RESULTS]:
            link = ""
            for l in node.findall(ATOM+"link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href","")
                    break
            record = _record(key, _text(node,ATOM+"title"),link,
                             _text(node,ATOM+"updated") or _text(node,ATOM+"published"))
            if record:
                items.append(record)
    else:
        safe_root = re.sub(r"[^a-zA-Z0-9_{}./:-]","",str(root.tag))[:70]
        raise ValueError("Unsupported RSS or Atom root: "+safe_root)
    return items


def parse_public(key, data):
    if key not in SOURCES or not isinstance(data, bytes) or len(data) > MAX_BYTES:
        raise ValueError("Invalid provider or bounded response")
    kind = SOURCES[key]["type"]
    if kind == "feed":
        return _feed(key,data)
    payload = json.loads(data)
    result = []
    if kind == "crossref":
        rows = (payload.get("message") or {}).get("items") or []
        for p in rows[:MAX_RESULTS]:
            title = (p.get("title") or [""])[0]
            doi = str(p.get("DOI") or "")
            url = "https://doi.org/"+doi if doi.startswith("10.") else p.get("URL","")
            journal = (p.get("container-title") or [""])[0]
            published = str((p.get("published") or {}).get("date-parts") or "")[:55]
            result.append(_record(key,title,url,published,journal))
    elif kind == "gdelt":
        for p in payload.get("articles",[])[:MAX_RESULTS]:
            result.append(_record(key,p.get("title"),p.get("url"),p.get("seendate"),
                                  p.get("domain")))
    elif kind == "world_bank":
        if not isinstance(payload,list) or len(payload)<2 or not isinstance(payload[1],list):
            raise ValueError("Unexpected World Bank data")
        for p in payload[1][:MAX_RESULTS]:
            indicator = (p.get("indicator") or {}).get("value")
            value = p.get("value")
            title = f"{indicator}: {value} ({p.get('date')})"
            result.append(_record(key,title,
                "https://data.worldbank.org/indicator/NY.GDP.MKTP.CD",
                p.get("date"),"public statistics, not future forecast"))
    elif kind == "usgs":
        for p in payload.get("features",[])[:MAX_RESULTS]:
            prop=p.get("properties") or {}
            result.append(_record(key,prop.get("title"),prop.get("url"),
                                  prop.get("time"),"observational earthquake feed"))
    elif kind == "eonet":
        for p in payload.get("events",[])[:MAX_RESULTS]:
            url = p.get("link") or ("https://eonet.gsfc.nasa.gov/api/v3/events/"+str(p.get("id") or ""))
            result.append(_record(key,p.get("title"),url,
                                  p.get("closed"),"remote sensing event metadata"))
    elif kind == "github":
        for p in payload.get("items",[])[:MAX_RESULTS]:
            result.append(_record(key,p.get("full_name"),p.get("html_url"),
                                  p.get("updated_at"),"public code, not vetted software"))
    else:
        raise ValueError("Unknown public response schema")
    return [row for row in result if row is not None]


def source_catalog():
    return {
        "schema":"plenum-public-horizon-registry-v1",
        "providers": [{
            "id":key,"category":p["category"],"publisher":p["publisher"],
            "site":p["url"],"status":"implemented_adapter_requires_live_check",
            "authorization":"public_read_only",
        } for key,p in SOURCES.items()],
        "credential_or_permission_gated":REVIEW_GATED,
        "unrestricted_access":False,
        "private_military_or_university_systems_accessible":False,
        "unreviewed_code_execution":False,
        "AGI_achieved":False,
    }


def scan_horizon(query, category="all", online=False, opener=urlopen):
    query = clean_query(query)
    if category != "all" and category not in CATEGORIES:
        raise ValueError("Unknown horizon category")
    keys = [k for k,p in SOURCES.items() if category=="all" or p["category"]==category]
    if not online:
        return {"schema":"plenum-public-horizon-snapshot-v1","topic":query,
                "category":category,
                "providers":[{"source":key,"status":"offline_not_requested","records":[]} for key in keys],
                "records":[],"independent_breakthrough_verified":False,
                "AGI_achieved":False}
    def one(key):
        try:
            items=fetch_public(key,query,opener=opener)
            return {"source":key,"status":"retrieved_metadata","records":items}
        except Exception as exc:
            # Errors carry only type; no URLs, tokens, private data or unstable
            # remote responses may be recorded as executable instructions.
            safe_errors = {
                "Public provider exceeded response byte limit",
                "XML entities or DTD not accepted",
                "Unsupported RSS or Atom feed",
                "Unsupported RSS or Atom root:",
                "Unknown public response schema",
            }
            reason = str(exc) if isinstance(exc,ValueError) else ""
            diagnosis = reason[:90] if (reason in safe_errors or
                reason.startswith("Unsupported RSS or Atom root:")) else ""
            return {"source":key,"status":"unavailable",
                    "error_type":type(exc).__name__,
                    "schema_diagnostic":diagnosis[:90],
                    "records":[]}
    with ThreadPoolExecutor(max_workers=4) as pool:
        statuses=list(pool.map(one,keys))
    all_records=[r for s in statuses for r in s["records"]]
    seen=set()
    unique=[]
    for row in all_records:
        if row["url"] not in seen:
            unique.append(row)
            seen.add(row["url"])
    return {
        "schema":"plenum-public-horizon-snapshot-v1","topic":query,
        "category":category,"providers":statuses,
        "records":unique,"providers_attempted":len(statuses),
        "providers_reporting_data":sum(s["status"]=="retrieved_metadata" and bool(s["records"]) for s in statuses),
        "snapshot_utc":datetime.now(timezone.utc).isoformat(),
        "independent_breakthrough_verified":False,
        "AGI_achieved":False,
        "limitations":[
            "Institutional releases, journalism and public metadata are claims, not independent truth.",
            "Public military and diplomatic publications do not convey privileged access.",
            "World Bank indicators and USGS observations differ from breaking news.",
            "Source outages, licensing restrictions and reporting bias are recorded.",
            "All outside text is untrusted data, never a command to an agent.",
        ],
    }
