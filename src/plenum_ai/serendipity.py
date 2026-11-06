"""Source-grounded speculative prompts combining science with creative disciplines.

The titles are data, never instructions. This produces questions, not scientific
facts, machine-discovered mechanisms, inventions or patentable claims.
"""
from hashlib import sha256

CREATIVE_TARGETS=(
    ("architecture","parametric facades and controllable natural lighting"),
    ("music","original rhythm and timbre as representations of measured data"),
    ("visual art","interpretable geometric forms and public scientific education"),
    ("product design","manufacturable low-waste human-centered objects"),
    ("aerospace engineering","lightweight structures and validated constraints"),
    ("agriculture","low-cost nutrient and environmental sensor systems"),
    ("fashion and textiles","recyclable safe materials and functional wearables"),
    ("education and games","interactive models of experimentally confirmed processes"),
)


def hypotheses_from_sources(snapshot,limit=8):
    if not isinstance(snapshot,dict) or snapshot.get("schema")!="plenum-cross-domain-research-pulse-v1":
        raise ValueError("Unrecognized public research report")
    if not isinstance(limit,int) or not 1<=limit<=8:
        raise ValueError("Maximum eight creative prompts per research pulse")
    rows=snapshot.get("records")
    if not isinstance(rows,list):
        raise ValueError("Invalid source record list")
    candidates=[
        row for row in rows
        if isinstance(row,dict)
        and row.get("tier") in (
            "journal_publication_metadata","preprint_not_peer_reviewed",
            "institutional_news_not_independent_verification")
        and isinstance(row.get("title"),str) and isinstance(row.get("url"),str)
        and row["url"].startswith("https://")
    ]
    ideas=[]
    seen=set()
    for row in candidates:
        source_url=row["url"]
        if source_url in seen:
            continue
        seen.add(source_url)
        target,application=CREATIVE_TARGETS[len(ideas)%len(CREATIVE_TARGETS)]
        title=row["title"][:220]
        ideas.append({
            "label":"speculative_question_unverified",
            "domain_to_explore":target,
            "possible_application":application,
            "research_title":title,
            "reference_url":source_url[:700],
            "reference_tier":row["tier"],
            "source_fingerprint_sha256":sha256(source_url.encode()).hexdigest(),
            "question":(
                "Could the actual measured methods or principles (if any) in the "
                "linked research be adapted to "+application+"? "
                "Read and verify the original methodology before proposing an experiment."
            ),
            "first_validation_action":"Retrieve permitted primary text, identify evidence and compare prior work",
            "second_validation_action":"Formulate falsifiable constraints and test independently",
            "new_invention_proven":False,
            "scientific_claim_verified":False,
            "original_paper_read":False,
        })
        if len(ideas)>=limit:
            break
    return {
        "schema":"plenum-source-linked-serendipity-v1",
        "source_snapshot_time":snapshot.get("observed_at_utc"),
        "idea_count":len(ideas),"ideas":ideas,
        "method":"deterministic_interdisciplinary_prompt_templates",
        "foundation_model_generated_hypotheses":False,
        "breakthrough_verified":False,
        "patentability_verified":False,
        "copyrighted_paper_contents_copied":False,
        "next_step":"Use a stronger evaluated reasoning model and independent scientific tools for candidate validation",
    }
