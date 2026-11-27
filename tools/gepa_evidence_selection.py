"""Read-only GEPA v0.1.4 selection of qualified engineering candidates.

Selection is advisory for future reflection, never production admission or proof
of learning. No inference, historical replay, candidate execution, or writes to
the workforce. Source archives are authenticated by their provider SHA-256.
"""
import argparse
import hashlib
import json
import random
import re
import zipfile
from pathlib import Path
from vendor.gepa_selection.gepa_utils import select_program_candidate_from_pareto_front

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def read_evidence(path, expected):
    path=Path(path)
    if (not re.fullmatch(r"[0-9a-f]{64}",expected) or path.is_symlink()
            or not path.is_file() or not 0<path.stat().st_size<=2_000_000):
        raise ValueError("Invalid evidence input")
    raw=path.read_bytes()
    if digest(raw)!=expected:
        raise ValueError("Provider digest mismatch")
    with zipfile.ZipFile(path) as z:
        names=z.namelist()
        if (len(names)!=len(set(names)) or len(names)>40 or
                sum(i.file_size for i in z.infolist())>4_000_000 or z.testzip() is not None):
            raise ValueError("Invalid evidence archive")
        def one(suffix):
            matches=[n for n in names if n.endswith("/"+suffix)]
            if len(matches)>1: raise ValueError("Ambiguous evidence")
            return json.loads(z.read(matches[0])) if matches else None
        native=one("native-result.json")
        verdict=one("independent-verdict.json")
        report=one("candidate-report.json")
        if not all(isinstance(x,dict) for x in (native,verdict,report)):
            return {"archive_sha256":expected,"eligible":False,"reason":"missing_completed_candidate_or_verdict"}
        # A passing candidate still requires semantic review. This selector
        # never changes admission, authority, or held-out evaluation scope.
        if (native.get("exit_status")!="Submitted" or native.get("paid_inference") is not False
                or native.get("production_written") is not False
                or verdict.get("existing_focused_tests_passed") is not True
                or verdict.get("task_acceptance_passed") is not True
                or verdict.get("network_disabled_for_candidate") is not True
                or verdict.get("production_written") is not False
                or report.get("human_review_required") is not True):
            return {"archive_sha256":expected,"eligible":False,"reason":"not_independently_qualified"}
        patch=[n for n in names if n.endswith(".patch")]
        patch_sha=report.get("candidate_artifact_sha256")
        if len(patch)!=1 or digest(z.read(patch[0]))!=patch_sha or verdict.get("candidate_artifact_sha256")!=patch_sha:
            raise ValueError("Candidate identity mismatch")
        binding=tuple([native.get("issue"),report.get("task"),report.get("source_file"),
                       report.get("source_sha256"),verdict.get("task_acceptance_test")])
        if type(binding[0]) is not int or not all(isinstance(s,str) and s for s in binding[1:]):
            raise ValueError("Missing comparable objective")
        if binding[3]!=native.get("original_source_sha256"):
            raise ValueError("Original source mismatch")
        calls=native.get("reserved_model_calls")
        elapsed=native.get("elapsed_seconds")
        if type(calls) is not int or not 1<=calls<=1000 or type(elapsed) not in (int,float) or not 0<elapsed<100000:
            raise ValueError("Invalid measured costs")
        return {"archive_sha256":expected,"eligible":True,"binding":binding,
                "patch_sha256":patch_sha,"calls":calls,"elapsed":elapsed}

def select(rows):
    if len({r["archive_sha256"] for r in rows})!=len(rows):
        raise ValueError("Duplicate archive")
    eligible=[r for r in rows if r["eligible"]]
    if not eligible:
        return {"status":"NO_ELIGIBLE_CANDIDATE","selected":None,"upstream_called":False,
                "production_admitted":False,"learning_demonstrated":False,"records":rows}
    if len({tuple(r["binding"]) for r in eligible})!=1:
        raise ValueError("Different frozen tasks cannot be ranked together")
    if len({r["patch_sha256"] for r in eligible})!=len(eligible):
        raise ValueError("Duplicate candidate")
    # Both criteria maximize efficiency; qualification above is mandatory.
    # GEPA's actual Pareto selector chooses a non-dominated reflection seed.
    max_calls=max(r["calls"] for r in eligible)
    max_elapsed=max(r["elapsed"] for r in eligible)
    scores=[(1-r["calls"]/max_calls + 1-r["elapsed"]/max_elapsed)/2 for r in eligible]
    front={k:{i for i,r in enumerate(eligible) if r[k]==min(x[k] for x in eligible)}
           for k in ("calls","elapsed")}
    idx=select_program_candidate_from_pareto_front(front,scores,random.Random(0))
    return {"status":"REVIEW_ONLY_REFLECTION_SEED","selected":eligible[idx]["patch_sha256"],
            "upstream_called":True,"production_admitted":False,"learning_demonstrated":False,"records":rows}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--evidence",nargs=2,action="append",required=True,metavar=("ZIP","SHA256"))
    a=p.parse_args()
    print(json.dumps(select([read_evidence(path,sha) for path,sha in a.evidence]),sort_keys=True))
