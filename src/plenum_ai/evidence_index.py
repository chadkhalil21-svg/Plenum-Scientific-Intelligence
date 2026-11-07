"""Deterministic, read-only inventory of public Plenum research evidence.

Indexes existing evidence by path and content digest, never by an AI's claims.
It does not read private corporate documents or pronounce scientific validity.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path

SCHEMA = "plenum-public-evidence-index-v1"
MAX_ITEMS = 5000
MAX_JSON_BYTES = 3_000_000


def _canonical(data):
    return json.dumps(data, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False)


def build_index(root):
    root = Path(root)
    if not root.is_dir() or root.is_symlink():
        raise ValueError("Evidence directory missing or symbolic")
    files = sorted(root.rglob("*.json"), key=lambda p: p.as_posix())
    if len(files) > MAX_ITEMS:
        raise ValueError("Unexpectedly large evidence inventory")
    entries, incomplete = [], []
    for path in files:
        relative = path.relative_to(root)
        if path.is_symlink() or any(part in (".", "..") for part in relative.parts):
            raise ValueError("Unsupported evidence path")
        if path.stat().st_size > MAX_JSON_BYTES:
            incomplete.append({"path":relative.as_posix(),"reason":"oversized"})
            continue
        raw = path.read_bytes()
        try:
            document = json.loads(raw)
        except (ValueError,UnicodeDecodeError):
            incomplete.append({"path":relative.as_posix(),"reason":"unreadable_json"})
            continue
        if not isinstance(document, dict):
            incomplete.append({"path":relative.as_posix(),"reason":"nonobject_json"})
            continue
        entries.append({
            "track":relative.parts[0] if len(relative.parts)>1 else "unclassified",
            "path":"evidence/"+relative.as_posix(),
            "sha256":sha256(raw).hexdigest(),
            "size_bytes":len(raw)
        })
    tracks = sorted({entry["track"] for entry in entries})
    grouped = [{"track":track,
                "records":sum(e["track"]==track for e in entries),
                "paths":[e["path"] for e in entries if e["track"]==track]}
               for track in tracks]
    report = {
        "schema":SCHEMA,
        "kind":"read_only_public_record_inventory",
        "source":"research-memory/evidence",
        "mission_reference":"research-memory/state/AGI_PROGRAM.json",
        "record_count":len(entries),
        "records":entries,
        "groups":grouped,
        "unindexed_records":incomplete,
        "inventory_complete":len(incomplete)==0,
        "digest_sha256":sha256(_canonical(entries).encode("utf-8")).hexdigest(),
        "scientific_claims_verified_by_index":False,
        "AGI_demonstrated":False,
        "automatic_model_promotion":False,
        "confidential_corporate_data_included":False,
        "note":"An indexed file is not evidence its scientific claims are true. Refer to original independent audits."
    }
    return report


def save_index(root, target):
    report = build_index(root)
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False)+"\n"
    if target.exists() and target.read_text("utf-8") == content:
        return report, False
    target.write_text(content, encoding="utf-8")
    return report, True


def main():
    parser = argparse.ArgumentParser(description="Reconcile existing public research evidence")
    parser.add_argument("--root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    report, updated = save_index(args.root, args.out)
    print("Indexed public research records:", report["record_count"],
          "groups:", len(report["groups"]), "updated:", updated,
          "missing/invalid:",len(report["unindexed_records"]))
    if not report["inventory_complete"]:
        raise SystemExit("Evidence index incomplete; no false comprehensive success")


if __name__ == "__main__":
    main()
