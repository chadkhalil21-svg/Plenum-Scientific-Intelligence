"""Detect new-to-Plenum public research records, with honest provenance.

"New" means absent from a bounded prior public observatory archive, not
newly discovered in the world, patentable or scientifically verified.
"""
from hashlib import sha256
from pathlib import Path
import json


def _identifier(item):
    if not isinstance(item,dict):
        return None
    url=item.get("doi") or item.get("url")
    if not isinstance(url,str) or not url.startswith("https://"):
        return None
    return sha256(url.lower().strip().encode("utf-8")).hexdigest()


def compare_discovery(snapshot,history_path,history_limit=120):
    if not isinstance(snapshot,dict) or snapshot.get("schema")!="plenum-cross-domain-research-pulse-v1":
        raise ValueError("Unsupported research snapshot")
    current=snapshot.get("records")
    if not isinstance(current,list) or len(current)>100:
        raise ValueError("Invalid record count")
    if not isinstance(history_limit,int) or not 1<=history_limit<=500:
        raise ValueError("History limit out of bounds")
    folder=Path(history_path)
    if folder.exists() and (folder.is_symlink() or not folder.is_dir()):
        raise ValueError("Only a directory of archive records may be used")
    files=sorted(folder.glob("*.json"))[-history_limit:] if folder.exists() else []
    ids=set()
    records_seen=0
    rejected=0
    for file in files:
        if file.is_symlink() or file.stat().st_size>700_000:
            rejected+=1
            continue
        try:
            record=json.loads(file.read_text(encoding="utf-8"))
            if record.get("schema")!="plenum-public-cross-domain-observatory-v1":
                raise ValueError("Unreviewed archive schema")
            previous=record["snapshot"]["records"]
            if not isinstance(previous,list) or len(previous)>100:
                raise ValueError("Invalid previous records")
            for row in previous:
                ident=_identifier(row)
                if ident:
                    ids.add(ident)
                    records_seen+=1
        except (OSError,KeyError,TypeError,ValueError):
            rejected+=1
    new=[]
    repeats=0
    for row in current:
        ident=_identifier(row)
        if not ident:
            continue
        if ident in ids:
            repeats+=1
            continue
        ids.add(ident)
        new.append({
            "title":str(row.get("title") or "")[:300],
            "url":str(row.get("url") or "")[:700],
            "source":str(row.get("source") or "")[:120],
            "tier":str(row.get("tier") or "")[:100],
            "published":str(row.get("published") or "")[:100],
            "record_id_sha256":ident,
            "breakthrough_verified":False,
        })
    return {
        "schema":"plenum-research-new-to-archive-v1",
        "current_report_time":snapshot.get("observed_at_utc"),
        "prior_archive_files_scanned":len(files),
        "prior_records_scanned":records_seen,
        "rejected_or_unreadable_archives":rejected,
        "new_to_this_archive":len(new),
        "previously_seen_in_this_archive":repeats,
        "items_first_observed_by_plenum":new,
        "novel_to_world_or_independent_science":False,
        "new_patentable_discoveries":False,
        "next_step":"Read primary papers, inspect methods, compare replication and check retractions",
    }
