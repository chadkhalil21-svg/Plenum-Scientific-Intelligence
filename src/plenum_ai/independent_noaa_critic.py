"""Different-family scientific critic for frozen real NOAA proposals.

A reviewed SmolLM2-1.7B model critiques Qwen3-1.7B hypotheses using
development-only data. Model-generated alternatives are separately scored
against heldout real observations, with no automatic promotion.

The challenge uses an already published historical archive, so results are
RETROSPECTIVE and are not a new blind prospective benchmark.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path

from . import noaa_revision_agent as original

CRITIC_MODEL = "HuggingFaceTB/SmolLM2-1.7B-Instruct"
CRITIC_REVISION = "31b70e2e869a7173562077fd711b654946d38674"
ORIGINAL_REVISION = "4ccd3fcbd3634721b46d23967fb44bb356a4dc49"
ARCHIVED_RUN_ID = "42321911614"
FROZEN_SCHEMA = "plenum-noaa-frozen-proposals-v1"
CRITIC_SCHEMA = "plenum-independent-noaa-critic-v1"
AUDIT_SCHEMA = "plenum-independent-noaa-critic-audit-v1"
MIN_DEV_GAIN_M = 0.0001


def _sha(value):
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def extract_public_proposals(archived):
    """Extract only the originally sealed proposer record, no holdout audit."""
    if not isinstance(archived, dict) or archived.get("source_revision") != ORIGINAL_REVISION:
        raise ValueError("Unexpected historical source revision")
    proposal = archived.get("public_proposal")
    _check_original(proposal)
    return {"schema": FROZEN_SCHEMA, "source_revision": ORIGINAL_REVISION,
            "archive_run_id": ARCHIVED_RUN_ID,
            "proposal": proposal, "proposal_sha256": _sha(proposal),
            "includes_holdout_measurements": False,
            "historical_previously_public": True}


def _check_original(p):
    if (not isinstance(p, dict)
            or p.get("schema") != original.SCHEMA
            or p.get("model") != original.MODEL
            or p.get("model_revision") != original.REVISION
            or p.get("heldout_measurements_accessed") is not False
            or p.get("model_promoted") is not False):
        raise ValueError("Unrecognized original model research")
    cases = p.get("cases")
    if not isinstance(cases, list) or [
        (c.get("station"), c.get("holdout_day")) for c in cases
    ] != list(original.CASES):
        raise ValueError("Incomplete frozen original research cases")
    for entry in cases:
        if entry.get("holdout_seen") is not False:
            raise ValueError("Original model observed test records")
        if original.digest({k:v for k,v in entry.items()
                            if k != "seal_sha256"}) != entry.get("seal_sha256"):
            raise ValueError("Original sealed hypothesis was changed")


def _check_frozen(frozen):
    if (not isinstance(frozen, dict) or frozen.get("schema") != FROZEN_SCHEMA
            or frozen.get("source_revision") != ORIGINAL_REVISION
            or frozen.get("archive_run_id") != ARCHIVED_RUN_ID
            or frozen.get("includes_holdout_measurements") is not False
            or frozen.get("historical_previously_public") is not True):
        raise ValueError("Original evidence manifest is invalid")
    _check_original(frozen.get("proposal"))
    if frozen.get("proposal_sha256") != _sha(frozen["proposal"]):
        raise ValueError("Original evidence manifest digest changed")


def _development(frozen_case, fetcher):
    """Only requests the precommitted pre-holdout NOAA date range."""
    station, day = frozen_case["station"], frozen_case["holdout_day"]
    obs, _ = fetcher(station, day, False)
    if original.dev_evidence_digest(obs, day) != frozen_case[
            "development_observations_sha256"]:
        raise ValueError("NOAA development measurements differ from historical seal")
    fit, dev = original._train_dev(obs, day)
    if (len(fit) != frozen_case["train_hours"]
            or len(dev) != frozen_case["development_hours"]):
        raise ValueError("NOAA development time coverage changed")
    reference = original._metrics(obs, fit, dev)
    for key, value in reference.items():
        if not original._near(frozen_case["reference_dev_mae_m"].get(key),
                              original._rounded(value)):
            raise ValueError("Historical reference scores did not reproduce")
    selected = frozen_case["selected_candidate"]
    measured = original._score(obs, fit, dev, selected)
    expected = frozen_case.get("selected_development_mae_m")
    if (measured is None) != (expected is None) or (
            measured is not None and not original._near(
                expected, original._rounded(measured))):
        raise ValueError("Historical Qwen model score did not reproduce")
    return obs, fit, dev, measured, reference


def critic_prompt(case, original_error, baseline_errors):
    return (
        "You are a DIFFERENT, independent-model scientific reviewer, not the "
        "original hypothesis proposer. Only historical DEVELOPMENT measurements "
        "are available. Do not claim to have seen the held-out forecast day.\n"
        "NOAA site: " + case["public_station"] + "; historical day: " +
        case["holdout_day"] + "\n"
        "Qwen3 model's prior proposed mixture parameters: " +
        json.dumps(case["selected_candidate"]) + "\n"
        "Qwen development mean absolute error (meters): " +
        str(original._rounded(original_error)) + "\n"
        "Development-only reference errors (meters): " + json.dumps(
            {key:original._rounded(value) for key,value in baseline_errors.items()}) + "\n"
        "Critically challenge potential overfitting and propose your own continuous "
        "alternative. Formula is FIXED by the experiment: forecast = "
        "(1-alpha)*24h_persistence + alpha*(train_mean + "
        "gain*(four_constituent_harmonic - train_mean)). "
        "Return exactly ONE JSON object, no markdown: keys alpha numeric [0,1], "
        "gain numeric [0.6,1.4], hypothesis string explaining your critical "
        "alternative, falsifier string describing how it could fail. "
        "Do not execute code, invent observations, or claim scientific discovery."
    )


class SmolLM2Critic:
    def __init__(self):
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM
        torch.set_num_threads(2)
        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(
            CRITIC_MODEL, revision=CRITIC_REVISION, trust_remote_code=False)
        self.model = AutoModelForCausalLM.from_pretrained(
            CRITIC_MODEL, revision=CRITIC_REVISION, trust_remote_code=False,
            use_safetensors=True, torch_dtype=torch.bfloat16,
            low_cpu_mem_usage=True).to("cpu").eval()

    def generate(self, prompt):
        rendered = self.tokenizer.apply_chat_template(
            [{"role":"user", "content":prompt}], tokenize=False,
            add_generation_prompt=True)
        batch = self.tokenizer(rendered, return_tensors="pt",
                               truncation=True, max_length=1200)
        with self.torch.inference_mode():
            result = self.model.generate(
                **batch, max_new_tokens=190, do_sample=False,
                pad_token_id=self.tokenizer.eos_token_id)
        return self.tokenizer.decode(
            result[0][batch["input_ids"].shape[1]:],
            skip_special_tokens=True).strip()


def critique(frozen, generate, fetcher=original.fetch_observations,
             critic_model=CRITIC_MODEL, critic_revision=CRITIC_REVISION):
    _check_frozen(frozen)
    if (not callable(generate) or not callable(fetcher)
            or critic_model != CRITIC_MODEL or critic_revision != CRITIC_REVISION):
        raise ValueError("An authorized independent model is required")
    rows = []
    for case in frozen["proposal"]["cases"]:
        obs, fit, dev, original_error, baseline_errors = _development(case, fetcher)
        raw = generate(critic_prompt(case, original_error, baseline_errors))
        parsed = original.parse_candidate(raw)
        critic_error = original._score(obs, fit, dev, parsed["candidate"])
        better_dev = (critic_error is not None and original_error is not None
                      and critic_error + MIN_DEV_GAIN_M < original_error)
        rows.append({
            "station": case["station"], "day": case["holdout_day"],
            "original_selected": case["selected_candidate"],
            "original_development_mae_m": original._rounded(original_error),
            "critic_status": parsed["status"],
            "critic_alternative": parsed["candidate"],
            "critic_development_mae_m": original._rounded(critic_error),
            "critic_response_sha256": sha256(
                raw.encode("utf-8") if isinstance(raw, str) else b"").hexdigest(),
            "counterproposal_better_on_development": better_dev,
            "recommended_candidate": (
                parsed["candidate"] if better_dev else case["selected_candidate"]),
            "holdout_seen": False,
        })
    return {
        "schema": CRITIC_SCHEMA,
        "critic_model": critic_model, "critic_revision": critic_revision,
        "model_family_distinct_from_original": True,
        "original_model": original.MODEL, "original_revision": original.REVISION,
        "original_proposal_sha256": frozen["proposal_sha256"],
        "critique_calls": len(rows), "critiques": rows,
        "heldout_observations_seen_by_critic": False,
        "retrospective_public_historical_data": True,
        "original_hypotheses_changed": False,
        "autonomous_model_promotion": False,
        "independent_reviewer_is_human": False,
        "AGI_demonstrated": False,
    }


def audit(frozen, criticism, fetcher=original.fetch_observations):
    _check_frozen(frozen)
    if (not isinstance(criticism, dict)
            or criticism.get("schema") != CRITIC_SCHEMA
            or criticism.get("critic_model") != CRITIC_MODEL
            or criticism.get("critic_revision") != CRITIC_REVISION
            or criticism.get("original_proposal_sha256") != frozen["proposal_sha256"]
            or criticism.get("heldout_observations_seen_by_critic") is not False
            or criticism.get("autonomous_model_promotion") is not False
            or criticism.get("critique_calls") != len(original.CASES)):
        raise ValueError("Critic manifest or attribution invalid")
    rows = criticism.get("critiques")
    cases = frozen["proposal"]["cases"]
    if (not isinstance(rows, list) or len(rows) != len(cases)
            or [(r.get("station"), r.get("day")) for r in rows] !=
               [(c["station"], c["holdout_day"]) for c in cases]):
        raise ValueError("Critic case identity or order changed")
    results = []
    for case, row in zip(cases, rows):
        # Recompute development-only results and validate counterproposal
        # selection BEFORE calculating withheld-date outcomes.
        obs, fit, dev, old_error, baseline_dev = _development(case, fetcher)
        alt = row.get("critic_alternative")
        checked = original.parse_candidate(json.dumps(alt)) if alt is not None else None
        if alt is not None and (checked["candidate"] != alt or row.get("critic_status")!="valid"):
            raise ValueError("Critic proposed an invalid model")
        if alt is None and row.get("critic_status")=="valid":
            raise ValueError("Invalid critic labeled successful")
        alt_error = original._score(obs, fit, dev, alt)
        for measured, stored in ((old_error, row.get("original_development_mae_m")),
                                 (alt_error, row.get("critic_development_mae_m"))):
            if (measured is None) != (stored is None) or (
                    measured is not None and not original._near(
                        stored, original._rounded(measured))):
                raise ValueError("Critic development metrics were changed")
        choose_alt = (alt_error is not None and old_error is not None
                      and alt_error + MIN_DEV_GAIN_M < old_error)
        wanted = alt if choose_alt else case["selected_candidate"]
        if (row.get("original_selected") != case["selected_candidate"]
                or row.get("counterproposal_better_on_development") is not choose_alt
                or row.get("recommended_candidate") != wanted
                or row.get("holdout_seen") is not False):
            raise ValueError("Counterproposal recommendation was altered")
        # Having validated sealed development records, access the real held-out
        # data only in this independent audit job, never in the critic job.
        full, _ = fetcher(case["station"], case["holdout_day"], True)
        if original.dev_evidence_digest(full, case["holdout_day"]) != case[
                "development_observations_sha256"]:
            raise ValueError("NOAA development observations changed in audit")
        cutoff = original.cutoff_date(case["holdout_day"])
        from datetime import timedelta
        train = sorted(t for t in full if cutoff-timedelta(days=16)<=t<cutoff)
        targets = sorted(t for t in full if cutoff<=t<cutoff+timedelta(days=1)
                         and t-timedelta(days=1) in full)
        if len(train)<350 or len(targets)<20 or set(train) & set(targets):
            raise ValueError("Insufficient NOAA test observations")
        base = original._metrics(full, train, targets)
        original_test = original._score(
            full, train, targets, case["selected_candidate"])
        alternative_test = original._score(full, train, targets, alt)
        selected_test = original._score(full, train, targets, wanted)
        strongest = min(base.values())
        results.append({
            "station": case["station"], "day": case["holdout_day"],
            "critic_status": row["critic_status"],
            "development_selected_counterproposal": choose_alt,
            "original_test_mae_m": original._rounded(original_test),
            "critic_alternative_test_mae_m": original._rounded(alternative_test),
            "revised_test_mae_m": original._rounded(selected_test),
            "strongest_reference_mae_m": original._rounded(strongest),
            "original_beats_best_baseline": original_test < strongest,
            "critic_alternative_beats_original": (
                alternative_test is not None and alternative_test < original_test),
            "revised_beats_original": selected_test < original_test,
            "revised_beats_strongest_baseline": selected_test < strongest,
            "previously_public_retrospective": True,
        })
    return {
        "schema": AUDIT_SCHEMA, "source_proposal_sha256": frozen["proposal_sha256"],
        "critic_report_sha256": _sha(criticism),
        "critic_model": CRITIC_MODEL,
        "cases": results, "total_cases": len(results),
        "valid_counterproposals": sum(x["critic_alternative_test_mae_m"] is not None for x in results),
        "development_recommended_changes": sum(x["development_selected_counterproposal"] for x in results),
        "actual_holdout_improvements": sum(x["revised_beats_original"] for x in results),
        "wins_vs_strongest_baseline": sum(x["revised_beats_strongest_baseline"] for x in results),
        "development_evidence_reproduced": True,
        "separate_model_family_used": True,
        "historical_public_data_not_prospectively_blind": True,
        "new_scientific_discovery_verified": False,
        "general_intelligence_verified": False,
        "auto_model_promotion": False,
    }


def _write(path, data):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False,
                            allow_nan=False)+"\n", encoding="utf-8")


def main():
    parser=argparse.ArgumentParser()
    sub=parser.add_subparsers(dest="command",required=True)
    x=sub.add_parser("extract")
    x.add_argument("--archived",required=True)
    x.add_argument("--out",required=True)
    x=sub.add_parser("critique")
    x.add_argument("--frozen",required=True)
    x.add_argument("--out",required=True)
    x=sub.add_parser("audit")
    x.add_argument("--frozen",required=True)
    x.add_argument("--critic",required=True)
    x.add_argument("--out",required=True)
    args=parser.parse_args()
    if args.command=="extract":
        result=extract_public_proposals(json.loads(
            Path(args.archived).read_text("utf-8")))
    elif args.command=="critique":
        frozen=json.loads(Path(args.frozen).read_text("utf-8"))
        runtime=SmolLM2Critic()
        result=critique(frozen,runtime.generate)
        print("Independent model critiques:",result["critique_calls"],
              "valid counterproposals:",sum(x["critic_alternative"] is not None
                                            for x in result["critiques"]))
    else:
        frozen=json.loads(Path(args.frozen).read_text("utf-8"))
        criticism=json.loads(Path(args.critic).read_text("utf-8"))
        result=audit(frozen,criticism)
        print("Independently audited:",result["total_cases"],
              "holdout improvements:",result["actual_holdout_improvements"],
              "wins against best baseline:",result["wins_vs_strongest_baseline"])
    _write(args.out,result)


if __name__=="__main__":
    main()
