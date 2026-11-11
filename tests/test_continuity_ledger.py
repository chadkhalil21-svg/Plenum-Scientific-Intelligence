"""Check strategic resume state remains evidence-linked and nonconfidential."""
import copy
import json
import tempfile
from pathlib import Path
import unittest
from plenum_ai import continuity_ledger as ledger


def fixture():
    return {
      "schema":ledger.SCHEMA,"last_reviewed_utc":"2026-11-07T03:00:00Z",
      "mission":"Develop independently evaluated general-purpose scientific intelligence while preserving continuity.",
      "confidential_documents_copied":False,
      "AGI_achieved":False,
      "automatic_model_promotion":False,
      "evidence":[{"id":"agi-lab-first-audit","status":"measured_failure",
                   "url":ledger.TRUSTED+"actions/runs/42331449321",
                   "result":{"correct":0,"attempted":6},
                   "AGI_demonstrated":False}],
      "next_actions":[{"priority":1,"action":"Adopt trusted standard benchmark under controlled conditions"}],
      "decisions":[{"decision":"Keep outcome ledger","reason":"Verify progress across sessions"}]
    }


class PublicStrategicContinuityTests(unittest.TestCase):
    def test_valid_immutable_scientific_claims(self):
        s=ledger.validate(fixture())
        text=ledger.brief(s)
        self.assertIn("Verified AGI: NO",text)
        self.assertIn("0/6",text)
        self.assertIn("This file is a checkpoint",text)

    def test_missing_or_changed_evidence_is_rejected(self):
        tests=[("AGI_achieved",True),("confidential_documents_copied",True),
               ("automatic_model_promotion",True)]
        for field,value in tests:
            altered=fixture();altered[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):
                ledger.validate(altered)
        wrong=fixture();wrong["evidence"][0]["result"]["correct"]=7
        with self.assertRaises(ValueError):
            ledger.validate(wrong)
        wrong=fixture();wrong["evidence"][0]["AGI_demonstrated"]=True
        with self.assertRaises(ValueError):
            ledger.validate(wrong)

    def test_live_research_memory_status_and_four_domain_scores(self):
        state=fixture()
        state["evidence"].append({
            "id":"inspect-four-domain-96-20261107",
            "status":"verified_foundation",
            "url":ledger.TRUSTED+"actions/runs/42341668858",
            "result":{
                "correct":35,"attempted":96,
                "by_family":{
                    "arc_challenge":{"correct":14,"attempted":24},
                    "gsm8k":{"correct":6,"attempted":24},
                    "hellaswag":{"correct":10,"attempted":24},
                    "mmlu_0_shot":{"correct":5,"attempted":24},
                },
            },
            "AGI_demonstrated":False,
        })
        state["evidence"].append({
            "id":"gsm8k-output-cap-diagnostic-20261107",
            "status":"verified_diagnostic",
            "url":ledger.TRUSTED+"actions/runs/42341668858",
            "result":{
                "baseline_correct":6,
                "baseline_attempted":24,
                "outputs_at_128_token_cap":10,
                "correct_among_at_cap":0,
            },
            "AGI_demonstrated":False,
        })
        state["evidence"].append({
            "id":"gsm8k-256-token-release-20261107",
            "status":"running_unverified",
            "url":ledger.TRUSTED+"actions/runs/42342997198",
            "AGI_demonstrated":False,
        })
        state["evidence"].append({
            "id":"inspect-call-correction-20261107",
            "status":"correction_merged_for_future_runs",
            "url":ledger.TRUSTED+"pull/31",
            "AGI_demonstrated":False,
        })
        checked=ledger.validate(state)
        brief=ledger.brief(checked)
        self.assertIn("35/96",brief)
        self.assertIn("diagnostic baseline 6/24; 10 at token cap",brief)
        self.assertIn("Verified AGI: NO",brief)

    def test_domain_mismatch_and_bad_diagnostics_are_rejected(self):
        state=fixture()
        e=state["evidence"][0]
        e["result"]={"correct":2,"attempted":3,
                     "by_family":{"science":{"correct":1,"attempted":3}}}
        with self.assertRaisesRegex(ValueError,"reconcile"):
            ledger.validate(state)
        e["result"]={
            "baseline_correct":6,"baseline_attempted":24,
            "outputs_at_128_token_cap":10,"correct_among_at_cap":11,
        }
        with self.assertRaisesRegex(ValueError,"contradict"):
            ledger.validate(state)
        e["result"]["correct_among_at_cap"]=True
        with self.assertRaisesRegex(ValueError,"noninteger"):
            ledger.validate(state)

    def test_paired_coding_regression_from_live_public_state(self):
        state=fixture()
        state["evidence"].append({
            "id":"inspect-react-three-matched-original-coding-20261107",
            "status":"measured_regression",
            "url":ledger.TRUSTED+"actions/runs/42350599820",
            "result":{
                "attempted":3,"one_shot_correct":2,"react_correct":1,
                "delta_correct":-1,"repairs":0,"regressions":1,
                "actual_tool_calls":11,"actual_tool_responses":11,
            },
            "AGI_demonstrated":False,
        })
        self.assertIn("tool-using 1/3",ledger.brief(ledger.validate(state)))
        bad=copy.deepcopy(state)
        bad["evidence"][-1]["result"]["repairs"]=1
        with self.assertRaisesRegex(ValueError,"regression"):
            ledger.validate(bad)
        bad=copy.deepcopy(state)
        bad["evidence"][-1]["result"]["actual_tool_responses"]=12
        with self.assertRaisesRegex(ValueError,"regression"):
            ledger.validate(bad)

    def test_larger_real_priority_text_remains_bounded(self):
        state=fixture()
        state["next_actions"][0]["action"]="Review provenance and host prerequisites. "+"a"*548
        self.assertEqual(ledger.validate(state)["AGI_achieved"],False)
        state["next_actions"][0]["action"]="a"*(ledger.MAX_ACTION_CHARS+1)
        with self.assertRaises(ValueError):
            ledger.validate(state)

    def test_ledger_capacity_scales_with_evidence_not_unbounded(self):
        state=fixture()
        for n in range(1,99):
            state["evidence"].append({
                "id":"evidence-item-"+str(n),
                "status":"planned",
                "url":ledger.TRUSTED+"issues/"+str(n),
                "AGI_demonstrated":False,
            })
        self.assertEqual(len(ledger.validate(state)["evidence"]),99)
        state["evidence"] *= 2
        with self.assertRaises(ValueError):
            ledger.validate(state)

    def test_non_github_and_duplicate_evidence_are_rejected(self):
        wrong=fixture();wrong["evidence"][0]["url"]="https://example.com/not-verifiable"
        with self.assertRaises(ValueError):
            ledger.validate(wrong)
        wrong=fixture();wrong["evidence"]*=2
        with self.assertRaises(ValueError):
            ledger.validate(wrong)

    def test_next_actions_must_be_prioritized_and_written(self):
        wrong=fixture();wrong["next_actions"][0]["priority"]=9
        with self.assertRaises(ValueError):
            ledger.validate(wrong)
        wrong=fixture();wrong["decisions"]=[]
        with self.assertRaises(ValueError):
            ledger.validate(wrong)

    def test_no_local_private_file_or_oversized_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            f=Path(tmp)/"state.json"
            f.write_text(json.dumps(fixture()))
            self.assertEqual(ledger.load(f)["schema"],ledger.SCHEMA)
            f.write_text("a"*(ledger.MAX_BYTES+1))
            with self.assertRaises(ValueError):
                ledger.load(f)

    def test_invalid_schema_and_timestamp_rejected(self):
        wrong=fixture();wrong["schema"]="agi-verified"
        with self.assertRaises(ValueError):
            ledger.validate(wrong)
        wrong=fixture();wrong["last_reviewed_utc"]="2026-11-07"
        with self.assertRaises(ValueError):
            ledger.validate(wrong)


    def test_original_historical_status_is_recognized_without_upgrading_confidence(self):
        state=fixture()
        original=state["evidence"][0]
        for status in ("verified_blocker", "verified_narrow_authenticated_public_demo",
                       "independently_scored_new_model_no_improvement",
                       "source_documented_and_adapter_contract_tests_verified_not_real_source_or_science_yet"):
            with self.subTest(status=status):
                original["status"]=status
                checked=ledger.validate(state)
                self.assertEqual(checked["evidence"][0]["status"],status)
                self.assertFalse(checked["AGI_achieved"])
        original["status"]="invented_success_of_agi"
        with self.assertRaisesRegex(ValueError,"Invalid evidence status"):
            ledger.validate(state)

    def test_original_screenshot_and_exact_official_pricing_are_not_github_runs(self):
        state=fixture()
        item=state["evidence"][0]
        item.update({"id":"computer-browser-gcp-project-created-20261107",
                     "status":"user_screenshot_confirmed",
                     "notes":"Founder-provided screenshot of the public browser project; no independent external proof."})
        item.pop("url")
        validated=ledger.validate(state)
        self.assertIn("not independently source-verified",ledger.brief(validated))
        invalid=copy.deepcopy(state)
        invalid["evidence"][0]["notes"]=""
        with self.assertRaises(ValueError):
            ledger.validate(invalid)
        state["evidence"][0].update({
            "id":"computer-browser-google-cloud-free-tier-capacity-20261107",
            "status":"official-pricing-verified",
            "url":"https://cloud.google.com/run/pricing"})
        self.assertEqual(ledger.validate(state)["evidence"][0]["status"],"official-pricing-verified")
        state["evidence"][0]["url"]="https://example.com/not-official"
        with self.assertRaises(ValueError):
            ledger.validate(state)

    def test_source_exception_cannot_apply_to_untethered_other_record(self):
        state=fixture()
        item=state["evidence"][0]
        item["status"]="official-pricing-verified"
        item["url"]="https://cloud.google.com/run/pricing"
        with self.assertRaises(ValueError):
            ledger.validate(state)
        item["status"]="user_screenshot_confirmed"
        item.pop("url")
        item["notes"]="A different fabricated item must never be permitted to skip source checks."
        with self.assertRaises(ValueError):
            ledger.validate(state)

if __name__=="__main__":
    unittest.main()
