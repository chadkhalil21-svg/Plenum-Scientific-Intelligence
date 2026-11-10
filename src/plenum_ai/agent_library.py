"""On-demand, integrity-verified fetch of dormant MIT-licensed agency roles.

This never runs a model, tool, command, or upstream agent prompt. The returned
source text is UNTRUSTED content. No installation occurs unless the caller
separately supplies a reviewed, new and isolated output destination.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "integrations/agent-catalog/agency-agents.index.json"
SOURCES = ROOT / "integrations/agent-catalog/upstream-sources.json"
PREFIX = "https://raw.githubusercontent.com/msitarzewski/agency-agents/"
MAX_SIZE = 120_000
RE_NAME = re.compile(r"^[a-z0-9/_-]+\.md$")
RE_SHA = re.compile(r"^[a-f0-9]{40}$")


def load_index(path=INDEX):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    source = d.get("source", {})
    roles = d.get("profiles")
    if (d.get("schema") != "plenum-upstream-specialist-index-v1"
        or source.get("repository") != "msitarzewski/agency-agents"
        or source.get("license") != "MIT"
        or not RE_SHA.fullmatch(source.get("commit", ""))
        or not isinstance(roles, list) or len(roles) != 283
        or d.get("count") != len(roles)):
        raise PermissionError("Only exact reviewed MIT agent catalogue accepted")
    seen = set()
    for role in roles:
        path = role.get("path", "")
        if (not RE_NAME.fullmatch(path)
            or path in seen or not RE_SHA.fullmatch(role.get("blob_sha", ""))
            or role.get("status") != "catalogued_idle"):
            raise PermissionError("Unreviewed agent identity or duplicate detected")
        seen.add(path)
    return d


def fetch_role(role_path, *, index=None, transport=None):
    index = load_index() if index is None else index
    sha = index["source"]["commit"]
    choices = {x["path"]: x for x in index["profiles"]}
    if role_path not in choices:
        raise PermissionError("Role absent from reviewed catalogue")
    if not RE_NAME.fullmatch(role_path) or not RE_SHA.fullmatch(sha):
        raise PermissionError("Untrusted agent resource")
    url = PREFIX + sha + "/" + role_path
    if transport is None:
        def transport(url):
            request = urllib.request.Request(url, headers={
                "User-Agent": "PlenumAgentCatalogue/1",
                "Accept": "text/plain",
            })
            with urllib.request.urlopen(request, timeout=20) as response:
                if response.status != 200:
                    raise RuntimeError("Upstream role unavailable")
                return response.read(MAX_SIZE + 1)
    body = transport(url)
    if not isinstance(body, bytes) or not 1 <= len(body) <= MAX_SIZE:
        raise ValueError("Invalid or excessively large persona file")
    git_sha = hashlib.sha1(
        b"blob " + str(len(body)).encode("ascii") + b"\0" + body
    ).hexdigest()
    if git_sha != choices[role_path]["blob_sha"]:
        raise PermissionError("Upstream persona integrity mismatch")
    return body.decode("utf-8")



def load_sources(path=SOURCES):
    """Validate the existing free-first REFERENCE registry without imports/network."""
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    entries = d.get("entries")
    if (d.get("schema") != "plenum-upstream-tool-sources-v1"
            or not isinstance(entries, list) or not 10 <= len(entries) <= 100):
        raise PermissionError("Unreviewed source catalogue or unexpected registry size")
    seen = set()
    states = {"existing_runtime", "existing_adapter", "existing_workflow",
              "existing_config", "indexed_metadata", "indexed_knowledge",
              "optional_desktop", "method_reused", "candidate",
              "research_only", "discovery_only"}
    for entry in entries:
        if not isinstance(entry, dict):
            raise PermissionError("Invalid source record")
        rid, repo = entry.get("id"), entry.get("repository")
        tags = entry.get("tags")
        if (not isinstance(rid, str)
                or not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,60}", rid)
                or rid in seen or not isinstance(repo, str)
                or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo)
                or not isinstance(tags, list) or not 1 <= len(tags) <= 15
                or not all(isinstance(x, str)
                           and re.fullmatch(r"[a-z0-9][a-z0-9-]{1,39}", x)
                           for x in tags)
                or entry.get("plenum_reuse_state") not in states
                or entry.get("default_execution") != "never_install_automatically"
                or not isinstance(entry.get("license"), str)
                or not isinstance(entry.get("free_cost_class"), str)):
            raise PermissionError("Unreviewed external source or activation permission")
        seen.add(rid)
    return d


def suggest_sources(objective: str, *, index=None, limit: int = 6) -> list[dict]:
    """Deterministic catalogue lookup, NOT a tool install or external action."""
    if (not isinstance(objective, str) or not 3 <= len(objective) <= 180
            or not 1 <= limit <= 10):
        raise ValueError("Require a bounded public topic and result count")
    words = set(re.findall(r"[a-z0-9]+", objective.lower()))
    index = load_sources() if index is None else index
    ranked = []
    for entry in index["entries"]:
        hits = words.intersection(entry["tags"])
        if not hits:
            continue
        existing = entry["plenum_reuse_state"].startswith("existing")
        ranked.append((len(hits), existing, entry["id"], entry))
    ranked.sort(key=lambda x: (-x[0], -int(x[1]), x[2]))
    return [{
        "id": entry["id"],
        "repository": entry["repository"],
        "source_url": "https://github.com/" + entry["repository"],
        "license": entry["license"],
        "plenum_reuse_state": entry["plenum_reuse_state"],
        "cost_class": entry["free_cost_class"],
        "matched_capabilities": sorted(words.intersection(entry["tags"])),
        "activation": "SOURCE_REFERENCE_ONLY_NOT_INSTALLED",
        "model_calls": 0,
        "additional_paid_services_enabled": False,
    } for _, _, _, entry in ranked[:limit]]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--fetch", help="Reviewed upstream division/name.md")
    parser.add_argument("--out", help="New owner-reviewed local file path for --fetch")
    parser.add_argument("--sources", action="store_true", help="List verified free-first upstream source metadata without activating any tools")
    parser.add_argument("--suggest-source", help="Find relevant upstream agent/engineering source metadata; never install")
    args = parser.parse_args()
    if args.sources or args.suggest_source:
        if args.list or args.fetch or args.out or (args.sources and args.suggest_source):
            parser.error("Source lookup cannot combine with persona fetch or other modes")
        if args.sources:
            entries=load_sources()["entries"]
            print(json.dumps({"registered_sources":len(entries),
                              "sources":[{"id":e["id"],"repository":e["repository"],
                                          "state":e["plenum_reuse_state"]} for e in entries],
                              "active_models_created":0,
                              "new_paid_services_enabled":False},indent=2))
        else:
            print(json.dumps({"topic":args.suggest_source,
                              "suggestions":suggest_sources(args.suggest_source),
                              "source_lookup_only":True},indent=2))
        return
    index = load_index()
    if args.list and args.fetch:
        parser.error("Choose only one operation")
    if args.list or not args.fetch:
        print(json.dumps({
            "schema": index["schema"], "source": index["source"],
            "catalogued_profiles": len(index["profiles"]),
            "installed_profiles": 0, "running_profiles": 0,
            "status": "VERIFIED_SOURCE_INDEX_IDLE"
        }, indent=2))
        return
    if not args.out:
        parser.error("Explicit new destination required to retrieve a persona")
    dst = Path(args.out)
    if dst.is_symlink() or dst.exists() or not dst.parent.is_dir():
        parser.error("Destination must be a new file in an existing trusted folder")
    text = fetch_role(args.fetch, index=index)
    # The caller must then separately review the untrusted persona source.
    with dst.open("x", encoding="utf-8") as f:
        f.write("<!-- UNTRUSTED UPSTREAM PERSONA, NOT INSTALLED OR EXECUTED -->\n")
        f.write(text)
    print("SOURCE_PROFILE_FETCHED_INTEGRITY_VERIFIED_NOT_ACTIVATED")


if __name__ == "__main__":
    main()
