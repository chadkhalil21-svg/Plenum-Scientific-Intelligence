"""Validate and summarize a public-safe, source-linked AGI continuity ledger.

The strategic state lives on the separate research-memory branch. It contains
NO confidential research or personal data. No silent continuous awareness
is implied: future sessions must fetch the state before making status claims.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

SCHEMA="plenum-agi-program-continuity-v1"
ALLOWED_STATUS={
    "verified_foundation", "measured_failure", "scheduled", "planned",
    "not_achieved", "running_unverified", "verified_diagnostic",
    "correction_merged_for_future_runs", "measured_regression",
}
TRUSTED="https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/"
MAX_BYTES=250000
MAX_EVIDENCE=128
MAX_DECISIONS=100
MAX_ACTION_CHARS=700



def _count(value, maximum=100000):
    """Only bounded nonnegative integer counts, never booleans or estimates."""
    return type(value) is int and 0 <= value <= maximum


def _validate_result(score):
    """Accept only actual scored results or the separately labeled diagnostics.

    The continuity ledger stores an append-only mixture of real independent
    scores and observational diagnostics. A diagnostic must not be mistaken
    for the verified answer-accuracy ratio it investigated.
    """
    if not isinstance(score, dict):
        raise ValueError("Non-object evidence measurement")
    comparative={
        "attempted", "one_shot_correct", "react_correct", "delta_correct",
        "repairs", "regressions", "actual_tool_calls", "actual_tool_responses",
    }
    if set(score)==comparative:
        counts=("attempted", "one_shot_correct", "react_correct", "repairs",
                "regressions", "actual_tool_calls", "actual_tool_responses")
        if (any(not _count(score[k]) for k in counts)
            or score["attempted"] == 0
            or type(score["delta_correct"]) is not int
            or not -100000 <= score["delta_correct"] <= 100000
            or score["one_shot_correct"] > score["attempted"]
            or score["react_correct"] > score["attempted"]
            or score["repairs"] > score["attempted"]-score["one_shot_correct"]
            or score["regressions"] > score["one_shot_correct"]
            or score["actual_tool_responses"] > score["actual_tool_calls"]
            or score["delta_correct"] != score["react_correct"]-score["one_shot_correct"]
            or score["react_correct"] != score["one_shot_correct"]+score["repairs"]-score["regressions"]):
            raise ValueError("Inconsistent matched coding regression audit")
        return
    if "correct" in score or "attempted" in score:
        correct, attempted=score.get("correct"), score.get("attempted")
        if not (_count(correct) and _count(attempted)
                and correct <= attempted):
            raise ValueError("Inconsistent independent benchmark score")
        if set(score)-{"correct","attempted","by_family"}:
            raise ValueError("Unreviewed independent score fields")
        families=score.get("by_family")
        if families is not None:
            if not isinstance(families,dict) or not 1<=len(families)<=20:
                raise ValueError("Missing or unbounded benchmark families")
            summed_correct=summed_attempted=0
            for key, family in families.items():
                if (not isinstance(key,str) or not 1<=len(key)<=80
                    or not isinstance(family,dict)
                    or set(family)!={"correct","attempted"}
                    or not _count(family["correct"]) or not _count(family["attempted"])
                    or family["correct"]>family["attempted"]):
                    raise ValueError("Invalid independent domain breakdown")
                summed_correct+=family["correct"]
                summed_attempted+=family["attempted"]
            if (summed_correct!=correct or summed_attempted!=attempted):
                raise ValueError("Domain scores do not reconcile to total")
        return
    expected={
        "baseline_correct", "baseline_attempted",
        "outputs_at_128_token_cap", "correct_among_at_cap",
    }
    if set(score)!=expected:
        raise ValueError("Unreviewed or missing diagnostic count fields")
    if any(not _count(v) for v in score.values()):
        raise ValueError("Negative, boolean or noninteger diagnostic")
    if not (score["correct_among_at_cap"] <= score["outputs_at_128_token_cap"]
            <= score["baseline_attempted"]
            and score["correct_among_at_cap"] <= score["baseline_correct"]
            <= score["baseline_attempted"]):
        raise ValueError("Diagnostic subsets contradict observed total")

def validate(value):
    if not isinstance(value,dict) or value.get("schema")!=SCHEMA:
        raise ValueError("Unknown public continuity ledger format")
    if (value.get("confidential_documents_copied") is not False
        or value.get("AGI_achieved") is not False
        or value.get("automatic_model_promotion") is not False):
        raise ValueError("Public ledger cannot claim AGI or include confidential content")
    mission=value.get("mission")
    if not isinstance(mission,str) or not 20<=len(mission)<=500:
        raise ValueError("Missing bounded public mission")
    date=value.get("last_reviewed_utc")
    try:
        timestamp=datetime.fromisoformat(date.replace("Z","+00:00"))
    except (TypeError,AttributeError,ValueError) as error:
        raise ValueError("Invalid UTC review timestamp") from error
    if timestamp.tzinfo is None or timestamp.utcoffset().total_seconds()!=0:
        raise ValueError("Review time must be UTC")
    items=value.get("evidence")
    if not isinstance(items,list) or not items or len(items)>MAX_EVIDENCE:
        raise ValueError("Missing bounded source-linked evidence")
    seen=set()
    for row in items:
        if not isinstance(row,dict) or row.get("status") not in ALLOWED_STATUS:
            raise ValueError("Invalid evidence status")
        identifier=row.get("id")
        link=row.get("url")
        if (not isinstance(identifier,str) or not identifier.isascii()
            or not 1<=len(identifier)<=64 or identifier in seen
            or not isinstance(link,str) or not link.startswith(TRUSTED)
            or len(link)>500):
            raise ValueError("Duplicate evidence or unreviewed source")
        seen.add(identifier)
        score=row.get("result")
        if score is not None:
            _validate_result(score)
        if row.get("AGI_demonstrated") is not False:
            raise ValueError("Experiment cannot imply AGI")
    goals=value.get("next_actions")
    if not isinstance(goals,list) or not 1<=len(goals)<=12:
        raise ValueError("Missing ordered, bounded next actions")
    for i,row in enumerate(goals,1):
        if (not isinstance(row,dict)
            or row.get("priority")!=i
            or not isinstance(row.get("action"),str)
            or not 8<=len(row["action"])<=MAX_ACTION_CHARS):
            raise ValueError("Unprioritized or ambiguous next action")
    decisions=value.get("decisions")
    if not isinstance(decisions,list) or not decisions or len(decisions)>MAX_DECISIONS:
        raise ValueError("Missing decisions and outcomes")
    for d in decisions:
        if not isinstance(d,dict) or not all(isinstance(d.get(k),str)
                                             and 4<=len(d[k])<=400
                                             for k in ("decision","reason")):
            raise ValueError("Invalid durable decision note")
    return value


def load(path):
    p=Path(path)
    if not p.is_file() or p.stat().st_size>MAX_BYTES:
        raise ValueError("Missing or oversized canonical public state")
    return validate(json.loads(p.read_text(encoding="utf-8")))


def brief(state):
    s=validate(state)
    lines=["Plenum Scientific Intelligence | durable public program state",
           "Reviewed UTC: "+s["last_reviewed_utc"],
           "Mission: "+s["mission"],
           "Verified AGI: NO",
           "Source-linked evidence:"]
    for item in s["evidence"]:
        measurement=item.get("result")
        if measurement is None:
            ratio=""
        elif "correct" in measurement:
            ratio=" ("+str(measurement["correct"])+"/"+str(measurement["attempted"])+")"
        elif "one_shot_correct" in measurement:
            ratio=(" (matched one-shot "+str(measurement["one_shot_correct"])+"/"+
                   str(measurement["attempted"])+", tool-using "+
                   str(measurement["react_correct"])+"/"+str(measurement["attempted"])+
                   ", delta "+str(measurement["delta_correct"])+")")
        else:
            ratio=(" (diagnostic baseline "+
                   str(measurement["baseline_correct"])+"/"+
                   str(measurement["baseline_attempted"])+
                   "; "+str(measurement["outputs_at_128_token_cap"])+
                   " at token cap)")
        lines.append("  - "+item["id"]+": "+item["status"]+ratio)
    lines.append("Next priorities:")
    for item in s["next_actions"]:
        lines.append("  "+str(item["priority"])+". "+item["action"])
    lines.append("This file is a checkpoint, not automatically consulted by new sessions.")
    return "\n".join(lines)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--state",required=True)
    p.add_argument("--print-brief",action="store_true")
    args=p.parse_args()
    state=load(args.state)
    print(brief(state) if args.print_brief else
          "Continuity ledger verified: "+str(len(state["evidence"]))+" evidence entries")


if __name__=="__main__":
    main()
