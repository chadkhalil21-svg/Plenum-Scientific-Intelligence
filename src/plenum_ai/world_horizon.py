"""Read-only, bounded public horizon scanner across research and civilization.

Public data/news feeds are *not* a privileged university, military or
corporate connection. Their text is untrusted and never an agent instruction.
No subscription, payment, scraping of gated pages, geopolitical targeting,
external execution or unpublished patent material is accessed.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen, build_opener
from xml.etree import ElementTree as ET
import json
import re
from .china_sources import cas_research_articles, china_affiliated_works, CN_NOTE

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
    # Official public search2 is an unauthenticated, read-only search POST.
    # https://www.grants.gov/api/common/search2
    "grants_gov_search": {"category":"funding", "type":"grants_search",
        "url":"https://api.grants.gov/v1/api/search2", "publisher":"Grants.gov public opportunity search"},
    "nature_journal_news": {"category":"journals", "type":"feed",
        "url":"https://www.nature.com/nature.rss", "publisher":"Nature Portfolio"},
    # ScienceDaily is a SECONDARY news alert, never proof of the underlying experiment.
    # Follow each headline to original lab announcements, papers and methods.
    "sciencedaily_latest": {"category":"discoveries", "type":"feed",
        "url":"https://www.sciencedaily.com/rss/all.xml",
        "publisher":"ScienceDaily science news (secondary reporting)"},
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
    "china_cas_research": {"category":"discoveries", "type":"china_cas_html",
        "url":"https://english.cas.cn/newsroom/",
        "publisher":"Chinese Academy of Sciences, public institutional research news"},
    "china_openalex_works": {"category":"journals", "type":"china_openalex",
        "url":"https://api.openalex.org/works",
        "publisher":"OpenAlex, China-affiliated scholarly publications"},
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


def funding_survey_subject(query):
    """Recognize a source survey, not an eligibility or application request."""
    match=re.fullmatch(r"(?:Survey|Review) public ([A-Za-z][A-Za-z -]{2,70}) funding sources",query,re.I)
    if not match:
        return None
    words=tuple(re.findall(r"[a-z]+",match.group(1).lower()))
    if not 1<=len(words)<=4:
        return None
    # Preserve meaningful terms. Never substitute an arbitrary model query.
    return tuple("agriculture" if word=="agricultural" else word for word in words)


def funding_title_matches(subject,title):
    if not subject or not isinstance(title,str):
        return False
    words=set(re.findall(r"[a-z]+",title.lower()))
    return all((word in words or word+"s" in words or
                (word=="agriculture" and "agricultural" in words)) for word in subject)


def paper_survey_subject(query):
    """Extract a literal public scholarly topic, not the request's boilerplate."""
    match=re.fullmatch(r"(?:Survey|Review) public ([A-Za-z][A-Za-z -]{2,70}) papers",query,re.I)
    if not match:
        return None
    words=tuple(re.findall(r"[a-z]+",match.group(1).lower()))
    return words if 1<=len(words)<=5 else None


def paper_title_matches(subject,title):
    if not subject or not isinstance(title,str):
        return False
    words=set(re.findall(r"[a-z]+",title.lower()))
    return all(bool(words.intersection(
        {term,term+"s"} | ({"compute","computational","computation","computations"} if term=="computing" else set())
        )) for term in subject)


def request_url(key, query, *, paper_alternative=False):
    if key not in SOURCES:
        raise ValueError("Unapproved public source")
    definition = SOURCES[key]
    base = definition["url"]
    kind = definition["type"]
    if kind in ("feed", "usgs", "china_cas_html", "grants_search"):
        return base
    if kind == "china_openalex":
        start=(datetime.now(timezone.utc)-timedelta(days=30)).date().isoformat()
        return base + "?" + urlencode({
            "filter":"institutions.country_code:CN,from_publication_date:"+start,
            "sort":"publication_date:desc","per_page":4,
            "select":"id,title,doi,publication_date,authorships"
        })
    if kind == "crossref":
        subject=paper_survey_subject(query)
        if subject:
            return base + "?" + urlencode({("query.bibliographic" if paper_alternative else "query.title"):" ".join(subject),"rows":20,
                "filter":"type:journal-article","select":"DOI,title,container-title,published,URL,publisher"})
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


def fetch_public(key, query, opener=urlopen, *, paper_alternative=False):
    url = request_url(key, clean_query(query), paper_alternative=paper_alternative)
    expected = urlsplit(SOURCES[key]["url"]).netloc
    if urlsplit(url).netloc != expected:
        raise ValueError("Public source host mismatch")
    if SOURCES[key]["type"]=="grants_search":
        subject=funding_survey_subject(query)
        if not subject:
            return []
        request=Request(url,data=json.dumps({"rows":25,"keyword":" ".join(subject),
                          "oppStatuses":"posted|forecasted"}).encode("utf-8"),
                        headers={"Content-Type":"application/json","Accept":"application/json",
                                 "User-Agent":"PlenumPublicFundingSurvey/1"},method="POST")
    else:
        request = Request(url, headers={
            "User-Agent":"PlenumScientificIntelligence/1.8 read-only-public-signals",
            "Accept":"application/json,text/html,application/rss+xml,application/atom+xml,application/xml",
        })
    from .chief_of_staff_pilot import NoRedirects
    client=build_opener(NoRedirects).open if opener is urlopen else opener
    with client(request,timeout=13) as response:
        if getattr(response,"status",200)!=200 or (hasattr(response,"geturl") and response.geturl()!=url):
            raise ValueError("Unexpected public provider response")
        data=response.read(MAX_BYTES+1)
    if len(data)>MAX_BYTES:
        raise ValueError("Public provider exceeded response byte limit")
    return parse_public(key,data,query=query)


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


def parse_public(key, data, query=None):
    if key not in SOURCES or not isinstance(data, bytes) or len(data) > MAX_BYTES:
        raise ValueError("Invalid provider or bounded response")
    kind = SOURCES[key]["type"]
    if kind == "feed":
        return _feed(key,data)
    if kind == "china_cas_html":
        return [r for title,url,date in cas_research_articles(data)
                if (r:=_record(key,title,url,date,"CAS institutional announcement, not independent research validation"))]
    if kind == "china_openalex":
        return [r for title,url,date in china_affiliated_works(data)
                if (r:=_record(key,title,url,date,CN_NOTE))]
    payload = json.loads(data)
    result = []
    if kind=="grants_search":
        if not isinstance(payload,dict) or payload.get("errorcode")!=0 or not isinstance(payload.get("data"),dict):
            raise ValueError("Unexpected Grants.gov search schema")
        rows=payload["data"].get("oppHits")
        if not isinstance(rows,list) or len(rows)>25:
            raise ValueError("Unexpected Grants.gov result count")
        subject=funding_survey_subject(query) if query else None
        seen=set()
        for row in rows:
            if not isinstance(row,dict) or row.get("oppStatus") not in ("posted","forecasted"):
                continue
            ident=str(row.get("id",""))
            title=row.get("title")
            agency=row.get("agencyName")
            if (not re.fullmatch(r"[1-9][0-9]{0,11}",ident) or ident in seen
                    or not isinstance(title,str) or not isinstance(agency,str) or not agency.strip()
                    or (subject and not funding_title_matches(subject,title))):
                continue
            record=_record(key,title,"https://www.grants.gov/search-results-detail/"+ident,
                           row.get("openDate"),row["oppStatus"]+"; "+agency[:80]+"; close "+str(row.get("closeDate",""))[:20])
            if record:
                result.append(record)
                seen.add(ident)
            if len(result)>=MAX_RESULTS:
                break
    elif kind == "crossref":
        rows = (payload.get("message") or {}).get("items") or []
        subject=paper_survey_subject(query) if query else None
        seen_dois=set()
        if subject:
            # Reuse the contract's exact readback DOI policy rather than
            # admitting identifiers its independent verifier must reject.
            from .chief_contract_plan import DOI_RE
        for p in rows[:20 if subject else MAX_RESULTS]:
            title = (p.get("title") or [""])[0]
            doi = str(p.get("DOI") or "")
            if subject:
                doi=doi.lower()
                if not DOI_RE.fullmatch(doi) or doi in seen_dois:
                    continue
                if len(result)>=MAX_RESULTS:
                    break
            url = "https://doi.org/"+doi if doi.startswith("10.") else p.get("URL","")
            journal = (p.get("container-title") or [""])[0]
            published = str((p.get("published") or {}).get("date-parts") or "")[:55]
            row=_record(key,title,url,published,journal)
            if subject:
                if row is None or not paper_title_matches(subject,row["title"]):
                    continue
                seen_dois.add(doi)
            result.append(row)
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
    if paper_survey_subject(query) and category in ("all","journals"):
        keys=["crossref_journals"]
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
    # The same approved Crossref endpoint supports a broader bibliographic
    # index. Change query strategy exactly once after no accepted title
    # results or a failed first request; do not broaden the subject gate.
    if keys==["crossref_journals"] and paper_survey_subject(query) and not statuses[0]["records"]:
        first=statuses[0]
        try:
            items=fetch_public("crossref_journals",query,opener=opener,paper_alternative=True)
            statuses[0]={"source":"crossref_journals","status":"retrieved_metadata",
                         "records":items,"query_strategy":"bibliographic_recovery",
                         "first_attempt":first}
        except (OSError,ValueError,TypeError,KeyError,AttributeError,RuntimeError) as exc:
            statuses[0]={"source":"crossref_journals","status":"unavailable",
                         "records":[],"query_strategy":"bibliographic_recovery",
                         "error_type":type(exc).__name__,"first_attempt":first}
    all_records=[r for s in statuses for r in s["records"]]
    seen=set()
    unique=[]
    for row in all_records:
        if row["url"] not in seen:
            unique.append(row)
            seen.add(row["url"])
    if category=="funding" and funding_survey_subject(query):
        # The legacy broad NSF feed remains visible in provider diagnostics,
        # but cannot masquerade as a requested subject survey.
        unique=[row for row in unique if row["source"]=="grants_gov_search"
                and funding_title_matches(funding_survey_subject(query),row["title"])]
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
