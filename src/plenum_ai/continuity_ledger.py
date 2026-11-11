"""Validate and summarize a public-safe, source-linked AGI continuity ledger.

The strategic state lives on the separate research-memory branch. It contains
NO confidential research or personal data. No silent continuous awareness
is implied: future sessions must fetch the state before making status claims.
"""
import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path

SCHEMA="plenum-agi-program-continuity-v1"
ALLOWED_STATUS={
    "verified_foundation", "measured_failure", "scheduled", "planned",
    "not_achieved", "running_unverified", "verified_diagnostic",
    "correction_merged_for_future_runs", "measured_regression",
    # Explicitly observed historical statuses on the original research-memory
    # branch; preserve their distinct evidence grades rather than collapsing
    # a screenshot, mock test or diagnostic into scientific proof.
    "completed_ungraded_original_agent_attempt_with_real_repetition_failure",
    "configuration_merged_no_new_model_inference",
    "independently_scored_new_model_no_improvement",
    "independently_scored_real_model_result",
    "official-pricing-verified",
    "original_NOAA_documented_source_and_mock_adapter_tests_verified_no_real_data_or_forecast_yet",
    "scheduling_safeguard_merged_and_source_verified_not_prospective_science_result",
    "source_documented_and_adapter_contract_tests_verified_not_real_source_or_science_yet",
    "user_screenshot_confirmed",
    "verified_blocker",
    "verified_independent_new_candidate_negative",
    "verified_narrow_authenticated_public_demo",
    "verified_observational_historical_replay_not_operational_twin",
    "verified_original_archived_trace_diagnostic_no_new_model_inference",
    "verified_original_new_task_native_tool_use_and_final_submission",
    "verified_original_public_science_scoring_1_of_3",
}
TRUSTED="https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/"
MAX_BYTES=250000
MAX_EVIDENCE=128
MAX_DECISIONS=160
MAX_ACTION_CHARS=2000
MAX_DECISION_REASON_CHARS=3000
MAX_ID_CHARS=96
HISTORICAL_RESULT_FIELDS = {
    "world-model-action-conditioned-synthetic-20261108": frozenset(["heldout_horizon8_action_blind_rmse","heldout_horizon8_action_conditioned_rmse","heldout_horizon8_persistence_rmse","holdout_transitions","shifted_physics_horizon8_action_conditioned_rmse","train_transitions"]),
    "world-model-paired-intervention-synthetic-20261108": frozenset(["JEPA_trained","action_intervention","changed_physics_action_aware_effect_rmse","horizons_steps","nominal_action_aware_effect_rmse","nominal_action_blind_effect_rmse","paired_episodes","real_digital_twin_verified","real_world_causality_verified"]),
    "noaa-observation-shadow-twin-historical-replay-20261108": frozenset(["boston_frozen_harmonic_mae_m","boston_one_hour_persistence_mae_m","boston_shadow_mae_m","historical_replay_not_live_synchronization","next_hour_evaluations_each","noaa_stations","operational_digital_twin_verified","real_NOAA_measurements_retrieved","reference_study_day","residual_update_gain","training_samples_each","virginia_key_frozen_harmonic_mae_m","virginia_key_one_hour_persistence_mae_m","virginia_key_shadow_mae_m"]),
    "gpqa-original-science-qwen06b-one-of-three-20261108": frozenset(["attempted","biology_correct","chemistry_correct","correct","paid_model_api_calls","physics_correct","total_input_tokens","total_output_tokens","total_tokens"]),
    "original-qwen-gpqa-science-three-domain-grades-20261108": frozenset(["attempted","biology","chemistry","correct","model","model_inference_repeated_for_recovery","original_evaluator","paid_model_api_calls","physics","revision"]),
    "qwen35-4b-quantized-gpqa-original-same-three-20261109": frozenset(["biology","candidate","candidate_correct","candidate_quant_sha256","candidate_revision","chemistry","model_promoted","original_evaluator","original_new_candidate_inference_executed","original_three_cases","paid_model_api_calls","paired_difference","physics","previous_model_rerun","prior_Qwen3_0_6B_correct"]),
    "qwen35-4b-original-gpqa-three-negative-20261108": frozenset(["automatic_promotion","biology_correct","candidate","candidate_attempted","candidate_correct","chemistry_correct","original_inspect_eval","original_llama_cpp_release","original_previous_qwen3_06b_attempted","original_previous_qwen3_06b_correct","paid_model_api_calls","physics_correct","prior_baseline_reexecuted","quant_revision","quant_sha256","same_question_ids_as_frozen_qwen3_06b"]),
    "original-react-three-native-failure-mode-review-20261108": frozenset(["HumanEval_0","HumanEval_1","HumanEval_2","native_tool_calls","native_tool_responses","new_model_calls","new_scoring_runs","original_attempted","original_direct_correct","original_model","original_react_correct"]),
    "original-inspect-no-submit-new-humaneval3-verified-20261109": frozenset(["actual_tool_calls","actual_tool_responses","attempted","correct","final_answer_nonempty","literal_tool_marker_in_final_answer","model","model_sha","official_agent","original_scorer","original_task","paid_model_api_calls","previous_HumanEval_0_1_2_not_rerun","previous_submit_mode_paired_on_this_problem"]),
    "original-swebench-django11790-scorer-incompat-and-agent-loop-20261109": frozenset(["AGI_demonstrated","failing_scorer","fixed_swebench_for_future","independent_grader_completed","installed_broken_swebench","model","observed_model_calls","observed_tool_responses","official_score","original_repo","python_calls","repeat_model_inference_after_failure","repeated_bash_command","repeated_identical_bash_calls","repository_edits_observed","source_issue_id","turn_limit_exceeded","valid_model_patch_observed"]),
    "one-time-nov-2026-prospective-archive-backup-main-configuration": frozenset(["NOAA_backup_utc","NOAA_original_utc","USGS_backup_utc","USGS_original_utc","audit_dates_unchanged","duplicate_proposal_guard","frozen_before_utc","model_inference_executed_by_this_change","original_heldout_observations_viewed","research_memory_precommitted_files_exist_yet","scientific_results_verified"]),
    "frozen-monthly-synthetic-model-job-retirement-main-20261109": frozenset(["daily_public_source_radar_unchanged","dollar_savings_measured","iterative_hypotheses_monthly_cron_removed","main_branch_source_change_trigger_preserved","manual_dispatch_preserved","model_challenge_monthly_cron_removed","prospective_NOAA_USGS_unchanged"]),
    "noaa-nov2026-preissuance-observation-source-clarification-20261109": frozenset(["AGI_demonstrated","CI_result","CI_total_unit_tests","UTC_hourly_sample","actual_original_product","frozen_source_metadata","future_measurements_accessed","independent_scientific_result","model_weights_modified","new_scientific_forecast_issued","original_live_NOAA_API_development_data_verification","original_test_days","paid_API_spending","protocol_and_frozen_forecast_method_unchanged","quality","reason","response_max_bytes","six_minute_original_NOAA_observed_values"]),
    "usgs-nov2026-preissuance-datetime-interval-source-correction-20261109": frozenset(["AGI_demonstrated","CI_status","CI_unit_tests","corrected_query_key","future_observations_accessed","live_USGS_source_verified","original_bug","original_precommitted_models_and_forecast_method_unchanged","original_source_and_sites_unchanged","paid_API_spending","protocol_json_byte_identical","returned_observation_property_unchanged","scientific_forecasts_issued"]),
}



def _count(value, maximum=100000):
    """Only bounded nonnegative integer counts, never booleans or estimates."""
    return type(value) is int and 0 <= value <= maximum


def _bounded_historical_metric(value, depth=0):
    """Schema-bounded original observation. Not a measured benchmark grade."""
    if depth > 4:
        return False
    if value is None or type(value) is bool:
        return True
    if type(value) in (int,float):
        return math.isfinite(value) and abs(value) <= 10**15
    if isinstance(value,str):
        return len(value) <= 1200
    if isinstance(value,list):
        return len(value) <= 50 and all(_bounded_historical_metric(v,depth+1) for v in value)
    if isinstance(value,dict):
        return len(value) <= 40 and all(
            isinstance(k,str) and 1 <= len(k) <= 100 and _bounded_historical_metric(v,depth+1)
            for k,v in value.items()
        )
    return False


def _validate_result(score, evidence_id=None):
    """Accept only actual scored results or the separately labeled diagnostics.

    The continuity ledger stores an append-only mixture of real independent
    scores and observational diagnostics. A diagnostic must not be mistaken
    for the verified answer-accuracy ratio it investigated.
    """
    if not isinstance(score, dict):
        raise ValueError("Non-object evidence measurement")
    if evidence_id in HISTORICAL_RESULT_FIELDS:
        # Preserve exact archived structure; never pretend an observational
        # report is an independently scored benchmark.
        fields = HISTORICAL_RESULT_FIELDS[evidence_id]
        if set(score) != fields or not _bounded_historical_metric(score):
            raise ValueError("Unreviewed historical result fields")
        if "correct" in score or "attempted" in score:
            if (not _count(score.get("correct"))
                or not _count(score.get("attempted"))
                or score["correct"] > score["attempted"]):
                raise ValueError("Invalid historical independent grade")
        if "actual_tool_calls" in score and "actual_tool_responses" in score:
            if (not _count(score["actual_tool_calls"])
                or not _count(score["actual_tool_responses"])
                or score["actual_tool_responses"] > score["actual_tool_calls"]):
                raise ValueError("Historical tool responses exceed calls")
        if ("correct" in score and "attempted" in score
            and all(k in score for k in ("biology","chemistry","physics"))
            and all(isinstance(score[k],dict)
                    and set(score[k]) == {"correct","attempted"}
                    for k in ("biology","chemistry","physics"))
        ):
            if (any(not _count(score[k].get("correct"))
                    or not _count(score[k].get("attempted"))
                    or score[k]["correct"] > score[k]["attempted"]
                    for k in ("biology","chemistry","physics"))
                or sum(score[k]["correct"] for k in ("biology","chemistry","physics")) != score.get("correct")
                or sum(score[k]["attempted"] for k in ("biology","chemistry","physics")) != score.get("attempted")):
                raise ValueError("Historical science domain grades do not reconcile")
        for key in (
            "JEPA_trained","real_world_causality_verified","real_digital_twin_verified",
            "operational_digital_twin_verified","model_promoted","automatic_promotion",
            "scientific_results_verified","independent_scientific_result",
            "AGI_demonstrated","future_observations_accessed",
            "new_scientific_forecast_issued","scientific_forecasts_issued",
        ):
            if key in score and score[key] is not False:
                raise ValueError("Historical record falsely upgrades evidence")
        return
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
        # Preserve two specifically identified lower-confidence source classes.
        # An owner's screenshot is not externally verified. A vendor's official
        # pricing page is a primary reference, not an original Plenum run.
        owner_screenshot = (
            identifier == "computer-browser-gcp-project-created-20261107"
            and row.get("status") == "user_screenshot_confirmed"
            and link is None
            and isinstance(row.get("notes"), str)
            and 20 <= len(row["notes"]) <= 2500
        )
        official_pricing = (
            identifier == "computer-browser-google-cloud-free-tier-capacity-20261107"
            and row.get("status") == "official-pricing-verified"
            and link == "https://cloud.google.com/run/pricing"
        )
        ordinary_source = (
            isinstance(link, str) and len(link) <= 500 and link.startswith(TRUSTED)
        )
        if (not isinstance(identifier,str) or not identifier.isascii()
            or not 1<=len(identifier)<=MAX_ID_CHARS or identifier in seen
            or not (ordinary_source or owner_screenshot or official_pricing)):
            raise ValueError("Duplicate evidence or unreviewed source")
        seen.add(identifier)
        score=row.get("result")
        if score is not None:
            _validate_result(score, identifier)
        if row.get("AGI_demonstrated") is not False:
            raise ValueError("Experiment cannot imply AGI")
    goals=value.get("next_actions")
    if not isinstance(goals,list) or not 1<=len(goals)<=12:
        raise ValueError("Missing ordered, bounded next actions")
    # Original research-memory priorities are zero-based; older fixtures
    # were one-based. Permit either contiguous series, not gaps or duplicates.
    start = goals[0].get("priority") if isinstance(goals[0],dict) else None
    if type(start) is not int or start not in (0,1):
        raise ValueError("Invalid priority origin")
    for i,row in enumerate(goals,start):
        if (not isinstance(row,dict)
            or row.get("priority")!=i
            or not isinstance(row.get("action"),str)
            or not 8<=len(row["action"])<=MAX_ACTION_CHARS):
            raise ValueError("Unprioritized or ambiguous next action")
    decisions=value.get("decisions")
    if not isinstance(decisions,list) or not decisions or len(decisions)>MAX_DECISIONS:
        raise ValueError("Missing decisions and outcomes")
    for d in decisions:
        if (not isinstance(d,dict)
            or not isinstance(d.get("decision"),str)
            or not 4<=len(d["decision"])<=400
            or not isinstance(d.get("reason"),str)
            or not 4<=len(d["reason"])<=MAX_DECISION_REASON_CHARS):
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
        elif "baseline_correct" in measurement:
            ratio=(" (diagnostic baseline "+
                   str(measurement["baseline_correct"])+"/"+
                   str(measurement["baseline_attempted"])+
                   "; "+str(measurement["outputs_at_128_token_cap"])+
                   " at token cap)")
        else:
            ratio=" (historical structured observation; not an independently scored benchmark)"
        caution = (" [founder screenshot; not independently source-verified]"
                   if item.get("status") == "user_screenshot_confirmed" else "")
        lines.append("  - "+item["id"]+": "+item["status"]+ratio+caution)
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
