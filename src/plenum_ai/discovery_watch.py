"""Source-linked research discovery across journals, preprints, labs and video.

This is a *metadata monitoring* subsystem, not a claim that research is true.
Crossref journal publications, bioRxiv/medRxiv preprints, institutional
news feeds, and public NASA YouTube titles are different evidence tiers.

Requests are bounded and use named upstream hosts. XML entities/DTDs are
rejected. No paywalled text, video media or unauthorized transcripts are copied.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET
import json
import re

MAX_BYTES = 300_000
YT_ATOM = "{http://www.w3.org/2005/Atom}"
YT_NS = "{http://www.youtube.com/xml/schemas/2015}"
NASA_CHANNEL_ID = "UCLA_DiR1FfKNvjuUpBHmylQ"
# Verified public journal ISSNs; uses Crossref's journal endpoint, not publisher scraping.
JOURNALS = {
    "Nature": ("0028-0836", "multidisciplinary"),
    "Science": ("0036-8075", "multidisciplinary"),
    "PNAS": ("0027-8424", "multidisciplinary"),
    "Cell": ("0092-8674", "life_sciences"),
    "Nature Communications": ("2041-1723", "multidisciplinary"),
    "Physical Review Letters": ("0031-9007", "physics"),
    "Nature Physics": ("1745-2473", "physics"),
    "Nature Photonics": ("1749-4885", "photonics"),
    "Nature Materials": ("1476-1122", "materials"),
    "Nature Biotechnology": ("1087-0156", "biotechnology"),
    "The Lancet": ("0140-6736", "medicine"),
    "New England Journal of Medicine": ("0028-4793", "medicine"),
    "Science Advances": ("2375-2548", "multidisciplinary"),
    "Journal of the American Chemical Society": ("0002-7863", "chemistry"),
    "ACS Nano": ("1936-0851", "nanotechnology"),
    "IEEE Transactions on Pattern Analysis and Machine Intelligence": ("0162-8828", "computing"),
    "ACM Transactions on Graphics": ("0730-0301", "design"),
    "Design Studies": ("0142-694X", "design"),
    "Music Perception": ("0730-7829", "music"),
    "The Journal of Creative Behavior": ("0022-0175", "creativity"),
}
LAB_FEEDS = {
    "MIT News": "https://news.mit.edu/?format=feed&type=rss",
    "NASA Updates": "https://www.nasa.gov/feed/",
}
ALL_PROVIDER_NAMES = ("crossref", "biorxiv", "medrxiv", "mit_news",
                      "nasa_news", "nasa_youtube")
MAX_RECENT_DAYS = 30
YOUTUBE_CHANNELS = {"nasa": NASA_CHANNEL_ID}


def _read(url, opener=urlopen):
    req = Request(url, headers={
        "User-Agent": "PlenumScientificIntelligence/1.4 research-watch public-contact",
        "Accept": "application/xml, application/rss+xml, application/json",
    })
    with opener(req, timeout=16) as stream:
        raw = stream.read(MAX_BYTES+1)
    if len(raw) > MAX_BYTES:
        raise ValueError("Source exceeded strict metadata byte budget")
    return raw


def _xml(raw):
    upper = raw.upper()
    if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:
        raise ValueError("Untrusted XML declaration")
    return ET.fromstring(raw)


def _safe_source_link(url, allowed_hosts):
    if not isinstance(url,str):
        return None
    parsed = urlsplit(url.strip())
    if parsed.scheme != "https" or parsed.hostname not in allowed_hosts:
        return None
    return url.strip()[:700]


def crossref_url(issn, cutoff):
    if issn not in {item[0] for item in JOURNALS.values()}:
        raise ValueError("Journal ISSN must be on reviewed list")
    if not isinstance(cutoff,datetime) or cutoff.tzinfo is None:
        raise ValueError("A timezone-aware snapshot is required")
    earliest=(cutoff-timedelta(days=14)).date().isoformat()
    return "https://api.crossref.org/journals/" + issn + "/works?" + urlencode({
        "filter": "from-pub-date:"+earliest,
        "sort": "published", "order": "desc",
        "rows": 3, "select": "DOI,title,published,container-title,type,URL",
    })


def crossref_topic_url(topic,cutoff):
    if not isinstance(topic,str) or not 2<=len(topic.strip())<=160:
        raise ValueError("Public topic must contain 2..160 characters")
    if not isinstance(cutoff,datetime) or cutoff.tzinfo is None:
        raise ValueError("Timezone-aware cutoff required")
    earliest=(cutoff-timedelta(days=14)).date().isoformat()
    return "https://api.crossref.org/works?" + urlencode({
        "filter":"from-pub-date:"+earliest,
        "query.bibliographic":topic.strip(),
        "sort":"published","order":"desc","rows":3,
        "select":"DOI,title,published,container-title,type,URL",
    })


def parse_crossref(raw, journal, cutoff):
    payload=json.loads(raw)
    if not isinstance(payload,dict) or not isinstance(payload.get("message"),dict):
        raise ValueError("Crossref did not return a journal message")
    entries=payload["message"].get("items")
    if not isinstance(entries,list):
        raise ValueError("Invalid Crossref items")
    collected=[]
    for item in entries[:3]:
        if not isinstance(item,dict) or item.get("type")!="journal-article":
            continue
        doi=str(item.get("DOI") or "")
        if not doi.startswith("10.") or len(doi)>240:
            continue
        title=item.get("title") or []
        if not isinstance(title,list) or not title or not str(title[0]).strip():
            continue
        parts=(item.get("published") or {}).get("date-parts") or []
        date=None
        if parts and isinstance(parts[0],list) and parts[0]:
            try:
                value=(parts[0]+[1,1])[:3]
                date=datetime(int(value[0]),int(value[1]),int(value[2]),
                              tzinfo=timezone.utc).date().isoformat()
            except (ValueError,TypeError,OverflowError):
                pass
        link="https://doi.org/"+doi
        actual_journal=item.get("container-title") or []
        displayed_journal=(str(actual_journal[0])[:150]
                           if isinstance(actual_journal,list) and actual_journal
                           else journal)
        collected.append({
            "source":"crossref", "tier":"journal_publication_metadata",
            "journal":displayed_journal, "title":str(title[0])[:300],
            "doi":"https://doi.org/"+doi,
            "url":link, "published":date,
            "date_verified_by_publisher":False,
            "independently_peer_reviewed":False,
            "full_text_available":False,
        })
    return collected


def preprint_url(server,days=7):
    if server not in ("biorxiv","medrxiv") or not isinstance(days,int) or not 1<=days<=MAX_RECENT_DAYS:
        raise ValueError("Invalid preprint interval")
    return "https://api.biorxiv.org/details/"+server+"/"+str(days)+"d/0/json"


def parse_preprints(raw, server):
    p=json.loads(raw)
    items=p.get("collection") if isinstance(p,dict) else None
    if not isinstance(items,list):
        raise ValueError("Invalid preprint collection")
    result=[]
    for item in items[:5]:
        doi=str(item.get("doi") or "")
        title=str(item.get("title") or "").strip()
        if not doi.startswith("10.1101/") or not title:
            continue
        result.append({
            "source":server,"tier":"preprint_not_peer_reviewed",
            "title":title[:300], "doi":"https://doi.org/"+doi,
            "url":"https://doi.org/"+doi,
            "published":str(item.get("date") or "")[:10],
            "category":str(item.get("category") or "")[:80],
            "peer_reviewed":False,
            "claims_verified":False,
        })
    return result


def parse_newsfeed(raw, provider):
    if provider not in LAB_FEEDS:
        raise ValueError("Feed not allowlisted")
    root=_xml(raw)
    result=[]
    if root.tag=="rss":
        items=root.findall(".//channel/item")
        for item in items[:5]:
            link=_safe_source_link(item.findtext("link"), {"news.mit.edu","www.nasa.gov","nasa.gov"})
            title=" ".join((item.findtext("title") or "").split())
            if link and title:
                result.append({"source":provider,"tier":"institutional_news_not_independent_verification",
                               "title":title[:300], "url":link,
                               "published":(item.findtext("pubDate") or "")[:90],
                               "original_research_peer_review_confirmed":False})
    elif root.tag==YT_ATOM+"feed":
        for item in root.findall(YT_ATOM+"entry")[:5]:
            l=item.find(YT_ATOM+"link")
            link=_safe_source_link(l.get("href") if l is not None else None,
                                   {"news.mit.edu","www.nasa.gov","nasa.gov"})
            title=" ".join((item.findtext(YT_ATOM+"title") or "").split())
            if link and title:
                result.append({"source":provider,"tier":"institutional_news_not_independent_verification",
                               "title":title[:300],"url":link,
                               "published":(item.findtext(YT_ATOM+"published") or "")[:40],
                               "original_research_peer_review_confirmed":False})
    else:
        raise ValueError("Expected RSS or Atom news feed")
    return result


def youtube_url(channel="nasa"):
    if channel in YOUTUBE_CHANNELS:
        channel_id=YOUTUBE_CHANNELS[channel]
    elif isinstance(channel,str) and re.fullmatch(r"UC[A-Za-z0-9_-]{22}",channel):
        channel_id=channel
    else:
        raise ValueError("Provide a supported channel name or valid YouTube UC channel ID")
    return "https://www.youtube.com/feeds/videos.xml?" + urlencode({
        "channel_id":channel_id})


def parse_youtube(raw):
    root=_xml(raw)
    if root.tag!=YT_ATOM+"feed":
        raise ValueError("Invalid YouTube Atom feed")
    result=[]
    for e in root.findall(YT_ATOM+"entry")[:8]:
        video=(e.findtext(YT_NS+"videoId") or "").strip()
        if not re.fullmatch(r"[A-Za-z0-9_-]{11}",video):
            continue
        result.append({
            "source":"youtube-nasa","tier":"public_video_metadata",
            "title":" ".join((e.findtext(YT_ATOM+"title") or "").split())[:300],
            "url":"https://www.youtube.com/watch?v="+video,
            "video_id":video,
            "published":(e.findtext(YT_ATOM+"published") or "")[:40],
            "transcript_available_or_licensed":False,
            "video_downloaded":False,
            "laboratory_result_verified":False,
        })
    return result


def source_status(name, fn):
    try:
        records=fn()
        return {"provider":name,"status":"retrieved_metadata",
                "records":records,"count":len(records)}
    except Exception as exc:
        return {"provider":name,"status":"unavailable",
                "error_type":type(exc).__name__,"count":0,"records":[]}


def research_pulse(topic="scientific discovery",cutoff=None,opener=urlopen,
                   selected_journals=None):
    if not isinstance(topic,str) or not 2<=len(topic.strip())<=160:
        raise ValueError("Public topic length must be 2..160")
    cutoff=cutoff or datetime.now(timezone.utc)
    if cutoff.tzinfo is None:
        raise ValueError("Snapshot time must be timezone aware")
    roster=list(JOURNALS)
    if selected_journals is None:
        # Rotate journal choices across scheduled runs rather than always
        # searching a few privileged disciplines.
        idx=cutoff.toordinal()%len(roster)
        chosen=[roster[(idx+j)%len(roster)] for j in range(6)]
    else:
        chosen=list(selected_journals)
        if len(chosen)>8 or any(j not in JOURNALS for j in chosen):
            raise ValueError("Only eight approved journals per bounded run")
    tasks=[]
    for name in chosen:
        issn=JOURNALS[name][0]
        tasks.append(("crossref:"+name,lambda n=name,i=issn:
            parse_crossref(_read(crossref_url(i,cutoff),opener),n,cutoff)))
    # The cross-journal topic index covers papers beyond the rotating
    # highlighted journals, including specialized and regional publishers.
    tasks.append(("crossref:topic",lambda:parse_crossref(
        _read(crossref_topic_url(topic,cutoff),opener),
        "cross-disciplinary topic search",cutoff)))
    for server in ("biorxiv","medrxiv"):
        tasks.append((server,lambda s=server:parse_preprints(
            _read(preprint_url(s),opener),s)))
    for name,url in LAB_FEEDS.items():
        tasks.append((name,lambda n=name,u=url:parse_newsfeed(_read(u,opener),n)))
    def get_nasa_video():
        try:
            return parse_youtube(_read(youtube_url(),opener))
        except Exception:
            import os
            if not os.getenv("YOUTUBE_API_KEY"):
                raise
            from .youtube_api import from_environment
            return from_environment("NASA science research",
                                    channel=NASA_CHANNEL_ID)["videos"]
    tasks.append(("youtube-nasa",get_nasa_video))
    with ThreadPoolExecutor(max_workers=3) as pool:
        outcomes=list(pool.map(lambda job:source_status(job[0],job[1]),tasks))
    seen=set()
    dedup=[]
    for outcome in outcomes:
        for item in outcome["records"]:
            key=item.get("doi") or item.get("url")
            if not key or key in seen:
                continue
            seen.add(key)
            dedup.append(item)
    return {
        "schema":"plenum-cross-domain-research-pulse-v1",
        "topic":topic, "observed_at_utc":cutoff.astimezone(timezone.utc).isoformat(),
        "journal_selection_strategy":"rotating_six_of_twenty",
        "journal_coverage_in_this_run":chosen,
        "providers":outcomes,"records":dedup,"distinct_records":len(dedup),
        "sources_unavailable":[x["provider"] for x in outcomes if x["status"]=="unavailable"],
        "peer_review_verified":False,"breakthroughs_independently_confirmed":False,
        "all_science_journals_covered":False,
        "cross_journal_topic_query_enabled":True,
        "copyrighted_works_downloaded":False,"video_transcripts_downloaded":False,
        "external_actions_performed":False,
        "limitations":[
            "Research metadata and institutional announcements are not scientific truth.",
            "Journal indexing varies; date of publication may differ from deposit date.",
            "Preprints are not peer-reviewed; institutional statements are not independent evidence.",
            "A six-of-twenty rotating sample is not comprehensive worldwide surveillance.",
            "Video listings are not transcripts or scientific assessments."
        ]
    }
