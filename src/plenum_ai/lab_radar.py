"""New-to-our-index public laboratory signals; reuses world_horizon snapshot without API calls."""
from urllib.parse import urlsplit

CATEGORIES = ("universities","discoveries","journals","health","artificial_intelligence","physics","funding","software","environment","design")
INDEX_SCHEMA = "plenum-public-radar-seen-links-v1"
SCHEMA = "plenum-daily-public-lab-radar-v1"
MAX_SEEN, MAX_DIGEST = 1024, 30

def _safe_url(url):
    if not isinstance(url,str) or not 8<=len(url)<=900: return False
    try: p=urlsplit(url)
    except ValueError: return False
    return p.scheme=="https" and bool(p.hostname) and not p.username and not p.password

def validated_history(urls):
    if not isinstance(urls,list) or len(urls)>MAX_SEEN or len(urls)!=len(set(urls)):
        raise ValueError("Invalid public history")
    if any(not _safe_url(u) for u in urls): raise ValueError("Unsafe public index URL")
    return urls

def _rows(snapshot):
    if not isinstance(snapshot,dict) or snapshot.get("schema")!="plenum-public-horizon-snapshot-v1":
        raise ValueError("Original world-horizon snapshot required")
    records=snapshot.get("records")
    providers=snapshot.get("providers")
    if not isinstance(records,list) or len(records)>128 or not isinstance(providers,list):
        raise ValueError("Oversized/invalid research snapshot")
    if any(not isinstance(p,dict) or not isinstance(p.get("status"),str)
           or not isinstance(p.get("source"),str) for p in providers):
        raise ValueError("Invalid provider status")
    return [r for r in records if isinstance(r,dict) and
            r.get("category") in CATEGORIES and _safe_url(r.get("url")) and
            r.get("untrusted_external_content") is True and
            all(isinstance(r.get(k),str) for k in ("title","source","publisher"))]

def summarize(snapshot,previous=None):
    rows=_rows(snapshot)
    seen=set(validated_history([] if previous is None else previous))
    novel=[r for r in rows if r["url"] not in seen]
    grouped={cat:[r for r in novel if r["category"]==cat] for cat in CATEGORIES}
    selected=[]
    for idx in range(4):
        for cat in CATEGORIES:
            if len(selected)<MAX_DIGEST and len(grouped[cat])>idx:
                r=grouped[cat][idx]
                selected.append({
                    "category":cat,"publisher":r["publisher"][:150],
                    "source":r["source"][:100],"url":r["url"],
                    "title_untrusted":r["title"][:330],
                    "claimed_publication_date":str(r.get("published") or "")[:55],
                    "new_to_index_only":True,"lab_result_independently_verified":False,
                    "external_text_is_instructions":False})
    providers=snapshot["providers"]
    return {"schema":SCHEMA, "snapshot_utc":snapshot.get("snapshot_utc"),
       "first_scan_baseline":not bool(previous),
       "sources_attempted":len(providers),
       "sources_returning_records":sum(p["status"]=="retrieved_metadata" and
                                        bool(p.get("records")) for p in providers),
       "source_outages":[p["source"] for p in providers if p["status"]=="unavailable"],
       "new_public_links_before_limit":len({r["url"] for r in novel}),
       "signals":selected,"AGI_demonstrated":False,
       "independent_laboratory_breakthrough_verified":False,
       "full_text_licensed_and_read":False,
       "model_inference_used":False,
       "limitation":"New means unseen by this public index, not necessarily newly published. Source claims and dates are unverified; worldwide coverage is incomplete."}

def update_seen(previous,snapshot):
    old=validated_history([] if previous is None else previous)
    recent=[r["url"] for r in _rows(snapshot)]
    values=[]
    for url in recent+old:
        if url not in values: values.append(url)
        if len(values)>=MAX_SEEN: break
    return values
