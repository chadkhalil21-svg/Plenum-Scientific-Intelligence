"""Searchable, local SQLite research index with explicit provenance and licenses.

Only title/identifiers are indexed by default. Text extraction is permitted
only with approved open-content licenses and must be deliberately requested.
No user-submitted text is silently published to the public GitHub repo.
"""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import re
import sqlite3

OPEN_CONTENT_LICENSES = frozenset({
    "CC0-1.0", "CC-BY-4.0", "CC-BY-3.0", "CC-BY-SA-4.0"
})
MAX_DOCUMENT_BYTES = 120_000
MAX_RESULTS = 20
TOKEN = re.compile(r"[A-Za-z0-9_]{2,30}")


def _connection(path):
    path = Path(path)
    if path.suffix not in (".sqlite", ".sqlite3", ".db"):
        raise ValueError("Use .sqlite, .sqlite3 or .db for the local index")
    if path.exists() and path.is_symlink():
        raise ValueError("Refusing symlink index")
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(path))
    connection.row_factory = sqlite3.Row
    connection.executescript("""
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS papers(
            key TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            doi TEXT,
            source TEXT NOT NULL,
            license TEXT,
            body TEXT NOT NULL,
            recorded_utc TEXT NOT NULL,
            body_sha256 TEXT NOT NULL
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS paper_search USING fts5(
            key UNINDEXED, title, body, tokenize='unicode61'
        );
    """)
    return connection


def _key(paper):
    source = str(paper.get("source", "")).strip()[:60]
    identifier = str(paper.get("doi") or paper.get("id") or paper.get("url") or "").strip().lower()[:240]
    if not source or not identifier:
        raise ValueError("Research source and stable DOI/id/url required")
    return sha256((source + "|" + identifier).encode()).hexdigest()


def upsert_paper(path, paper, fulltext=None):
    """Explicit local import; refuse rights-unknown full text."""
    if not isinstance(paper, dict):
        raise TypeError("Paper must be a dictionary")
    title = str(paper.get("title") or "").strip()
    url = str(paper.get("url") or "").strip()
    if not (2 <= len(title) <= 350 and url.startswith("https://")
            and len(url) <= 500):
        raise ValueError("Valid title and HTTPS source link required")
    license_id = str(paper.get("license") or "").upper().strip()
    text = str(fulltext or "")
    if text and license_id not in OPEN_CONTENT_LICENSES:
        raise ValueError("Full-text indexing requires a reviewed open license")
    if len(text.encode("utf-8")) > MAX_DOCUMENT_BYTES:
        raise ValueError("Full-text content exceeds bounded indexing limit")
    key = _key(paper)
    payload = {
        "key": key, "title": title, "url": url, "doi": str(paper.get("doi") or "")[:200],
        "source": str(paper["source"])[:60], "license": license_id or "unspecified",
        "body": text, "recorded_utc": datetime.now(timezone.utc).isoformat(),
        "body_sha256": sha256(text.encode()).hexdigest(),
    }
    with _connection(path) as conn:
        old = conn.execute("SELECT body_sha256, body FROM papers WHERE key=?", (key,)).fetchone()
        if old and old["body"] and not text:
            # A metadata refresh cannot silently erase an already licensed document.
            payload["body"], payload["body_sha256"] = old["body"], old["body_sha256"]
        conn.execute("""INSERT INTO papers
              (key,title,url,doi,source,license,body,recorded_utc,body_sha256)
              VALUES (:key,:title,:url,:doi,:source,:license,:body,:recorded_utc,:body_sha256)
              ON CONFLICT(key) DO UPDATE SET title=excluded.title,url=excluded.url,
              doi=excluded.doi,source=excluded.source,license=excluded.license,
              body=excluded.body,recorded_utc=excluded.recorded_utc,
              body_sha256=excluded.body_sha256
        """, payload)
        conn.execute("DELETE FROM paper_search WHERE key=?", (key,))
        conn.execute("INSERT INTO paper_search(key,title,body) VALUES(?,?,?)",
                     (key, title, payload["body"]))
    return {"id": key, "fulltext_indexed": bool(payload["body"]),
            "license": payload["license"]}


def index_federated(path, report):
    if not isinstance(report, dict) or not isinstance(report.get("records"), list):
        raise ValueError("Expected a federated search result with records")
    added, refused = 0, []
    for row in report["records"][:50]:
        try:
            upsert_paper(path, row)
            added += 1
        except (TypeError, ValueError, KeyError) as exc:
            refused.append({"source": str(row.get("source", ""))[:40],
                            "reason": type(exc).__name__})
    return {"metadata_records_indexed": added,
            "records_rejected": refused, "fulltext_added": False}


def search_index(path, query, limit=8):
    if not isinstance(limit, int) or not 1 <= limit <= MAX_RESULTS:
        raise ValueError("Invalid result count")
    terms = TOKEN.findall(query)[:10] if isinstance(query, str) else []
    if not terms:
        raise ValueError("Search must contain at least one word")
    # FTS query uses only safely quoted alphanumeric tokens.
    expression = " OR ".join('"' + term + '"' for term in terms)
    with _connection(path) as conn:
        rows = conn.execute("""
            SELECT p.key,p.title,p.doi,p.url,p.source,p.license,p.body,
                   p.body_sha256
            FROM paper_search JOIN papers p ON paper_search.key=p.key
            WHERE paper_search MATCH ?
            ORDER BY bm25(paper_search) LIMIT ?
        """, (expression, limit)).fetchall()
    return {
        "query": query,
        "results": [{
            "id": row["key"], "title": row["title"], "doi": row["doi"],
            "source": row["source"], "url": row["url"],
            "license": row["license"],
            "excerpt": row["body"][:320] if row["body"] else None,
            "fulltext_available_locally": bool(row["body"]),
            "content_sha256": row["body_sha256"] if row["body"] else None,
            "citation_verified": False,
        } for row in rows],
        "claim": "Local search index and document excerpts, not verified scientific conclusions",
    }


def import_verified_memory(path, memory_dir, max_files=1000):
    """Rebuild the local search index from public, checksum-verified GitHub memory.

    The research-memory branch remains the cross-run source of truth.
    This does not import privileged/private conversation content.
    """
    from .memory import verify
    root = Path(memory_dir)
    if not root.is_dir():
        raise FileNotFoundError("Public research memory directory not found")
    if not isinstance(max_files, int) or not 1 <= max_files <= 2000:
        raise ValueError("Invalid bounded memory import size")
    added, invalid, seen = 0, 0, 0
    for file in sorted(root.glob("*.json"))[:max_files]:
        seen += 1
        try:
            record = json.loads(file.read_text(encoding="utf-8"))
            verify(record)
            for item in record["sources"]:
                document = {"source": "reviewed-memory", "id": item.get("id"),
                            "title": item.get("title"), "url": item.get("url"),
                            "doi": item.get("doi")}
                if document["title"] and document["url"] and document["id"]:
                    upsert_paper(path, document)
                    added += 1
        except (OSError, TypeError, ValueError, KeyError, json.JSONDecodeError):
            invalid += 1
    return {
        "memory_files_examined": seen,
        "valid_paper_references_indexed": added,
        "invalid_or_rejected_records": invalid,
        "private_data_imported": False,
        "fulltext_imported": False,
        "source_of_truth": "public content-addressed research-memory branch",
    }
