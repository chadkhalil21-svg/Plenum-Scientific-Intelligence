"""Reject empty, instruction-echo and unsupported-reference model outputs.

This is a syntactic provenance screen, not a scientific-fact checker.
"""
import re


def assess_answer(answer, role):
    if not isinstance(answer, str) or len(answer.strip()) < 80:
        return {"acceptable": False, "reason": "empty_or_too_short"}
    forbidden = ("Scientific hypothesis proposer: Provide two falsifiable",
                 "Scientific hypothesis proposer: provide two falsifiable",
                 "Independent scientific critic: identify weaknesses",
                 "Independent scientific critic: Identify weaknesses")
    if any(x.casefold() in answer.casefold() for x in forbidden):
        return {"acceptable": False, "reason": "repeated_instruction"}
    if answer.count(answer[:45]) >= 3:
        return {"acceptable": False, "reason": "repetition"}
    if re.search(r"\b(?:references|citations|bibliography)\s*:", answer, re.I) or re.search(
        r"\[[0-9]+\]\s+[A-Z]", answer
    ) or re.search(r"\bet\s+al\.", answer, re.I):
        return {"acceptable": False, "reason": "unsupported_reference_style"}
    if re.search(r"https?://|doi\.org/|10\.\d{4,9}/", answer, re.I):
        return {"acceptable": False, "reason": "free_form_citation_requires_source_link_validation"}
    return {"acceptable": True, "reason": "basic_screen_only_not_source_or_scientific_validation"}
