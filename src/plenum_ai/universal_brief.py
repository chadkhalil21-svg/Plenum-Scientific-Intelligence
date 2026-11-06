"""Create bounded, source-linked interdisciplinary research QUESTIONS, not conclusions.

Combines entries from separate public institutions into reviewable design and
science prompts. Source headlines are untrusted reference strings and never
instructions. No unlicensed full text or private information is processed.
"""
from hashlib import sha256
import re

MAX_CONCEPTS = 12
TARGETS = (
    ("physical sciences", "a falsifiable numerical or laboratory comparison"),
    ("engineering", "a constrained design-and-validation experiment"),
    ("environment", "a measurable environmental intervention and independent controls"),
    ("art and design", "an original visualization or human-centered prototype"),
    ("music and acoustics", "an original sound-data study using newly composed material"),
    ("business", "a first-principles technical and economic feasibility study"),
    ("education", "a reproducible interactive scientific teaching prototype"),
    ("software", "a minimal program with tests and documented inputs"),
)

WORD = re.compile(r"[a-zA-Z0-9]{3,30}")


def _score(row, topic):
    title = str(row.get("title") or "")
    search = set(WORD.findall(topic.lower()))
    tokens = set(WORD.findall(title.lower()))
    return len(search & tokens)


def synthesize_horizon(snapshot, limit=8):
    if not isinstance(snapshot, dict) or snapshot.get("schema") != "plenum-public-horizon-snapshot-v1":
        raise ValueError("Expected Plenum public horizon schema")
    if not isinstance(limit, int) or not 1 <= limit <= MAX_CONCEPTS:
        raise ValueError("One to twelve bounded concepts")
    rows = snapshot.get("records")
    topic = snapshot.get("topic")
    if not isinstance(rows, list) or len(rows) > 200 or not isinstance(topic, str):
        raise ValueError("Invalid source report")
    filtered = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        url = item.get("url")
        if not isinstance(url, str) or not url.startswith("https://") or len(url) > 900:
            continue
        if not isinstance(item.get("category"), str) or not isinstance(item.get("title"), str):
            continue
        filtered.append(item)
    # Maximize distinct institutions/categories rather than amplifying
    # a single feed or selecting two articles from the same publisher.
    filtered.sort(key=lambda item: (-_score(item, topic), item["category"], item["source"], item["url"]))
    concepts = []
    seen_pairs = set()
    for one in filtered:
        for two in filtered:
            if len(concepts) >= limit:
                break
            if one["category"] == two["category"] or one["publisher"] == two["publisher"]:
                continue
            if one["url"] == two["url"]:
                continue
            canonical = tuple(sorted((one["url"], two["url"])))
            if canonical in seen_pairs:
                continue
            if sum(one["category"] in x["source_categories"] for x in concepts) >= 2:
                continue
            seen_pairs.add(canonical)
            target, work = TARGETS[len(concepts) % len(TARGETS)]
            concepts.append({
                "type": "unverified_cross_domain_research_question",
                "inspiration": [
                    {"category":p["category"], "publisher":p["publisher"],
                     "title_untrusted_reference_only":p["title"][:240],
                     "url":p["url"], "published":p.get("published") or ""}
                    for p in (one, two)
                ],
                "source_categories": [one["category"], two["category"]],
                "proposed_domain": target,
                "research_question": (
                    "Could independently verified methods or observations from "
                    "the two linked areas suggest "+work+"? "
                    "First read the permitted original sources and check relevance, "
                    "then define measurements and a falsifier."
                ),
                "required_evidence": [
                    "Read primary methods and check publication dates/rights",
                    "Verify that the phenomena are actually related",
                    "Define a quantitative outcome, negative control and baseline",
                    "Test on independently held-out evidence",
                ],
                "reference_pair_sha256": sha256(" | ".join(canonical).encode()).hexdigest(),
                "not_original_discovery": True,
                "novelty_or_patentability_verified": False,
                "external_code_executed": False,
                "copyrighted_content_copied": False,
            })
        if len(concepts) >= limit:
            break
    return {
        "schema": "plenum-interdisciplinary-inquiry-v1",
        "topic": topic, "source_record_count": len(filtered),
        "distinct_categories": sorted({x["category"] for x in filtered}),
        "concept_count": len(concepts),
        "concepts": concepts,
        "synthesis_method": "deterministic_source_diversity_and_reviewed_question_templates",
        "foundation_model_wrote_new_science": False,
        "scientific_discovery_verified": False,
        "new_program_deployed": False,
        "music_or_art_media_copied": False,
        "requires_human_scientific_review": True,
    }


def build_universal_brief(topic, online=False, opener=None, limit=8):
    from .world_horizon import scan_horizon
    kwargs = {"opener": opener} if opener is not None else {}
    snapshot = scan_horizon(topic, category="all", online=online, **kwargs)
    ideas = synthesize_horizon(snapshot, limit)
    return {
        "schema": "plenum-universal-brief-v1",
        "public_snapshot": snapshot,
        "cross_domain_ideas": ideas,
        "youtube_video_understanding_enabled": False,
        "automated_new_software_from_external_titles": False,
        "automatic_model_self_revision": False,
        "AGI_achieved": False,
    }
