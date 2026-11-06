"""Durable public-only research metadata memory, not a scientific truth database."""
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def make_record(report, improvement, run_id="", revision=""):
    question = str(report.get("question") or "").strip()
    if not 0 < len(question) <= 600:
        raise ValueError("Missing or oversized public question")
    sources = []
    if report.get("source_status") == "retrieved_metadata":
        ids = set()
        for paper in report["literature_and_hypotheses"].get("papers", [])[:10]:
            paper_id = str(paper.get("id") or "")[:160]
            if not paper_id or paper_id in ids:
                continue
            ids.add(paper_id)
            sources.append({
                "id": paper_id, "title": str(paper.get("title") or "")[:300],
                "year": paper.get("year") if isinstance(paper.get("year"), int) else None,
                "doi": str(paper.get("doi") or "")[:180],
                "url": str(paper.get("url") or "")[:350]
            })
    payload = {
        "schema": "plenum-memory-v1",
        "recorded_utc": datetime.now(timezone.utc).isoformat(),
        "question": question,
        "run_id": str(run_id)[:80],
        "revision": str(revision)[:80],
        "source_status": str(report.get("source_status"))[:80],
        "sources": sources,
        "prior_memory_ids": list(report.get("prior_memory_ids") or [])[:5],
        "simulation_benchmark_passed": bool(report.get("numeric_benchmark_verified")),
        "scientific_discovery_verified": False,
        "hypotheses_status": "unverified",
        "candidate_ranker_weight": improvement.get("candidate", {}).get("weight"),
        "candidate_holdout_accuracy": improvement.get("candidate", {}).get("holdout_accuracy"),
        "independent_audit_passed": bool(improvement.get("independent_audit", {}).get("passed")),
        "candidate_deployed": False,
    }
    digest = hashlib.sha256(canonical(payload).encode("utf-8")).hexdigest()
    return dict(payload, id=digest[:24], sha256=digest)


def verify(record):
    if not isinstance(record, dict) or len(canonical(record).encode("utf-8")) > 25000:
        raise ValueError("Invalid record or record too large")
    payload = {k: v for k, v in record.items() if k not in ("id", "sha256")}
    digest = hashlib.sha256(canonical(payload).encode("utf-8")).hexdigest()
    if record.get("schema") != "plenum-memory-v1" or record.get("sha256") != digest or record.get("id") != digest[:24]:
        raise ValueError("Checksum or schema mismatch")
    if not 0 < len(str(record.get("question") or "")) <= 600 or not isinstance(record.get("sources"), list) or len(record["sources"]) > 10:
        raise ValueError("Invalid public metadata")
    if record.get("scientific_discovery_verified") is not False or record.get("candidate_deployed") is not False:
        raise ValueError("Unreviewed results cannot be promoted or deployed")
    return True


def save(record, directory):
    verify(record)
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / (record["id"] + ".json")
    if destination.exists():
        current = json.loads(destination.read_text(encoding="utf-8"))
        verify(current)
        if current != record:
            raise ValueError("Existing content-addressed entry changed")
        return str(destination), False
    destination.write_text(json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return str(destination), True


def recall(directory, query, limit=3):
    if not directory or not Path(directory).is_dir():
        return []
    words = set(re.findall(r"[a-z0-9]+", query.casefold()))
    ranked = []
    for file in sorted(Path(directory).glob("*.json"))[:2000]:
        try:
            record = json.loads(file.read_text(encoding="utf-8"))
            verify(record)
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            continue
        context = record["question"] + " " + " ".join(str(p["title"]) for p in record["sources"])
        overlap = len(words & set(re.findall(r"[a-z0-9]+", context.casefold())))
        if overlap:
            ranked.append((overlap, record["recorded_utc"], record))
    ranked.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return [item[2] for item in ranked[:max(0, min(limit, 5))]]
