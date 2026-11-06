"""Read-only creative source discovery with explicit attribution and rights.

Openverse public media, Metropolitan Museum of Art Open Access, and
MusicBrainz music-work *metadata*. No copyrighted audio/image media is
downloaded, no music is played and no recording's rights are inferred
from MusicBrainz bibliographic metadata.
"""
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json

MAX_BYTES=260_000
MAX_QUERY=120


def _get(url,opener=urlopen):
    req=Request(url,headers={
        "User-Agent":"PlenumScientificIntelligence/1.4 source-metadata-not-downloader",
        "Accept":"application/json",
    })
    with opener(req,timeout=18) as res:
        body=res.read(MAX_BYTES+1)
    if len(body)>MAX_BYTES:
        raise ValueError("Creative source exceeds bounded size")
    return json.loads(body)


def _query(q):
    if not isinstance(q,str) or not 2<=len(q.strip())<=MAX_QUERY:
        raise ValueError("Public creative topic must be 2..120 characters")
    return q.strip()


def openverse_url(q,medium):
    _query(q)
    if medium not in ("images","audio"):
        raise ValueError("Only approved openly licensed media searches")
    return ("https://api.openverse.org/v1/"+medium+"/?"+
            urlencode({"q":q, "page_size":3}))


def parse_openverse(data,medium):
    if not isinstance(data,dict) or not isinstance(data.get("results"),list):
        raise ValueError("Invalid open-media JSON")
    result=[]
    for item in data["results"][:3]:
        if not isinstance(item,dict):
            continue
        name=str(item.get("title") or "Untitled").strip()
        url=str(item.get("foreign_landing_url") or "")
        license_id=str(item.get("license") or "").strip().lower()
        if not url.startswith("https://") or not license_id:
            continue
        result.append({
            "source":"openverse-"+medium,"tier":"open_media_metadata",
            "title":name[:250],"url":url[:600],
            "creator":str(item.get("creator") or "unspecified")[:200],
            "license":license_id[:40],
            "license_version":str(item.get("license_version") or "")[:20],
            "license_url":str(item.get("license_url") or "")[:500],
            "attribution":str(item.get("attribution") or "")[:600],
            "downloaded":False,
            "individual_usage_rights_independently_verified":False,
        })
    return result


def museum_search_url(q):
    _query(q)
    # Met moved searches to the new paginated 1.1 endpoint in October 2026.
    return "https://collectionapi.metmuseum.org/public/collection/v1.1/search?" + urlencode({
        "q":q,"hasImages":"true","limit":3,"offset":0
    })


def parse_museum_search(data):
    if not isinstance(data,dict) or not isinstance(data.get("objectIDs"),list):
        raise ValueError("Invalid Met Museum search")
    return [int(x) for x in data["objectIDs"][:3] if isinstance(x,int) and x>0]


def museum_object_url(ident):
    if not isinstance(ident,int) or ident<=0:
        raise ValueError("Positive museum identifier required")
    return "https://collectionapi.metmuseum.org/public/collection/v1/objects/"+str(ident)


def parse_museum_object(item):
    if not isinstance(item,dict) or not item.get("isPublicDomain") or not item.get("objectID"):
        return None
    link=str(item.get("objectURL") or "")
    if not link.startswith("https://www.metmuseum.org/"):
        return None
    return {
        "source":"met-open-access","tier":"museum_object_metadata",
        "title":str(item.get("title") or "Untitled")[:250],
        "url":link[:600],
        "artist":str(item.get("artistDisplayName") or "")[:180],
        "medium":str(item.get("medium") or "")[:120],
        "object_date":str(item.get("objectDate") or "")[:80],
        "public_domain_flag":True,"metadata_license":"CC0",
        "image_downloaded":False,
        "rights_of_third_party_details_not_verified":True,
    }


def musicbrainz_url(q):
    _query(q)
    return "https://musicbrainz.org/ws/2/work/?" + urlencode({
        "query":q,"fmt":"json","limit":3
    })


def parse_musicbrainz(data):
    if not isinstance(data,dict) or not isinstance(data.get("works"),list):
        raise ValueError("Invalid MusicBrainz works response")
    rows=[]
    for work in data["works"][:3]:
        name=str(work.get("title") or "").strip()
        mbid=str(work.get("id") or "")
        if not name or len(mbid)!=36:
            continue
        rows.append({
            "source":"musicbrainz","tier":"music_composition_metadata_only",
            "title":name[:250],
            "url":"https://musicbrainz.org/work/"+mbid,
            "type":str(work.get("type") or "")[:80],
            "music_notation_obtained":False,
            "recording_obtained":False,
            "permission_to_reproduce_music":False,
        })
    return rows


def library_of_congress_url(query):
    _query(query)
    return "https://www.loc.gov/search/?" + urlencode({
        "q":query.strip(),"fo":"json","c":3,"at":"results"
    })


def parse_library_of_congress(data):
    if not isinstance(data,dict) or not isinstance(data.get("results"),list):
        raise ValueError("Invalid Library of Congress catalog search")
    records=[]
    for obj in data["results"][:3]:
        if not isinstance(obj,dict):
            continue
        title=str(obj.get("title") or "").strip()
        loc=str(obj.get("id") or "")
        # The Library of Congress API sometimes returns http loc.gov IDs.
        if loc.startswith("http://www.loc.gov/"):
            loc="https://www.loc.gov/"+loc[len("http://www.loc.gov/"):]
        if not title or not loc.startswith("https://www.loc.gov/"):
            continue
        item_format=obj.get("original_format")
        if isinstance(item_format,list):
            item_format=", ".join(map(str,item_format))
        records.append({
            "source":"library-of-congress",
            "tier":"historic_cultural_catalog_metadata",
            "title":title[:250],"url":loc[:600],
            "date":str(obj.get("date") or "")[:50],
            "original_format":str(item_format or "")[:150],
            "rights_from_catalog_not_verified":True,
            "media_downloaded":False,
            "permission_to_reproduce_score_image_or_recording":False,
        })
    return records


def creative_discovery(query,opener=urlopen):
    _query(query)
    def job(name,func):
        try:
            records=func()
            return {"provider":name,"status":"retrieved_metadata","records":records}
        except Exception as exc:
            return {"provider":name,"status":"unavailable",
                    "error_type":type(exc).__name__,"records":[]}
    def met():
        ids=parse_museum_search(_get(museum_search_url(query),opener))
        rows=[]
        for ident in ids[:2]:
            parsed=parse_museum_object(_get(museum_object_url(ident),opener))
            if parsed:
                rows.append(parsed)
        return rows
    operations=[
        ("openverse-images",lambda:parse_openverse(
            _get(openverse_url(query,"images"),opener),"images")),
        ("openverse-audio",lambda:parse_openverse(
            _get(openverse_url(query,"audio"),opener),"audio")),
        ("metropolitan-museum",met),
        ("musicbrainz-works",lambda:parse_musicbrainz(
            _get(musicbrainz_url(query),opener))),
        ("library-of-congress",lambda:parse_library_of_congress(
            _get(library_of_congress_url(query),opener))),
    ]
    with ThreadPoolExecutor(max_workers=2) as pool:
        result=list(pool.map(lambda t:job(t[0],t[1]),operations))
    return {
        "schema":"plenum-creative-sources-v1",
        "query":query,
        "providers":result,
        "records":[record for provider in result for record in provider["records"]],
        "source_count":sum(v["status"]=="retrieved_metadata" for v in result),
        "assets_downloaded":False,
        "copyright_safety":"metadata links only; individual license verification required before reuse",
        "generative_ai_model_connected":False,
        "notes":[
            "MusicBrainz work listings do not license recordings, lyrics or scores.",
            "Openverse licenses and attribution are metadata, not legal guarantees.",
            "The Met collection search uses the October 2026 v1.1 paginated API.",
            "Library of Congress item pages do not themselves establish public-domain or media reuse rights.",
            "No copyrighted songs or other media were copied or played."
        ]
    }
