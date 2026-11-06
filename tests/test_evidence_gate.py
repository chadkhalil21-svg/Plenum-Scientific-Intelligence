"""Development-only gating tests: no future information or hidden tuning."""
from datetime import datetime, timedelta, timezone
from math import sin, pi
from urllib.parse import urlsplit, parse_qs
import io
import json
import unittest

from plenum_ai.evidence_gate import (
    FRESH_TEST_DAYS, ORDER, PERIODS, evidence_guard, query,
    propose_gated, independent_audit
)


class Stream(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, *args): self.close()


def source_rows(cutoff, test):
    first = cutoff-timedelta(days=16)
    rows=[]
    for h in range((17 if test else 16)*24):
        t=first+timedelta(hours=h)
        elapsed=(t-datetime(2026,1,1,tzinfo=timezone.utc)).total_seconds()/3600
        y = 1.2 + sum(
            w*sin(2*pi*elapsed/p+phase) for p,w,phase in zip(
                PERIODS["four_constituents"],(.9,.2,.15,.1),(.3,.5,.7,.9)
            ))
        rows.append({"t":t.strftime("%Y-%m-%d %H:%M"),"v":f"{y:.10f}"})
    return rows


class PolicyGateTests(unittest.TestCase):
    def setUp(self):
        self.requests=[]

    def opener(self, req, timeout=25):
        p=parse_qs(urlsplit(req.full_url).query)
        end=p["end_date"][0]
        day=next(day for day in FRESH_TEST_DAYS if
                 end in (day.replace("-",""),(
                     datetime.strptime(day,"%Y-%m-%d")-timedelta(days=1)
                 ).strftime("%Y%m%d")))
        cutoff=datetime.strptime(day,"%Y-%m-%d").replace(tzinfo=timezone.utc)
        reveal=end==cutoff.strftime("%Y%m%d")
        self.requests.append((p["station"][0],day,reveal))
        self.assertEqual(p["product"][0],"hourly_height")
        return Stream(json.dumps({"data":source_rows(cutoff,reveal)}).encode())

    def test_policy_uses_development_data_not_llm_confidence(self):
        scores={"persistence_24h":.17,"m2_only":.11,"m2_s2":.13,
                "four_constituents":.10}
        result=evidence_guard(scores,"persistence_24h")
        self.assertEqual(result["selected_for_blind_test"],"four_constituents")
        self.assertFalse(result["suggestion_accepted"])
        self.assertTrue(result["original_model_selection_override"])
        self.assertFalse(result["guard_used_final_test_labels"])

    def test_invalid_scores_refused(self):
        with self.assertRaises(ValueError):
            evidence_guard({"persistence_24h":1.}, "persistence_24h")
        with self.assertRaises(ValueError):
            evidence_guard({k:float("nan") for k in ORDER},"m2_only")

    def test_first_job_never_requests_heldout_day(self):
        p=propose_gated(lambda prompt:"A",opener=self.opener)
        self.assertEqual(len(self.requests),4)
        self.assertTrue(all(not reveal for _,_,reveal in self.requests))
        self.assertTrue(all(not c["development"]["test_data_seen"]
                            for c in p["proposals"]))
        self.assertTrue(all(c["gate"]["selected_for_blind_test"]=="four_constituents"
                            for c in p["proposals"]))
        self.assertFalse(p["production_code_or_model_modified"])

    def test_second_job_evaluates_all_cases_independently(self):
        p=propose_gated(lambda prompt:"A",opener=self.opener)
        report=independent_audit(p,opener=self.opener)
        self.assertEqual(report["trials"],4)
        self.assertEqual(report["guard_wins_against_persistence"],4)
        self.assertEqual(report["guard_wins_against_qwen_suggestion"],4)
        self.assertEqual(report["qwen_suggestion_overridden"],4)
        self.assertEqual(len(self.requests),12) # first 4 + audit train-only 4 + final 4
        self.assertEqual(sum(reveal for _,_,reveal in self.requests),4)
        self.assertFalse(report["deployment_authorized"])
        self.assertFalse(report["generalizable_AI_improvement_demonstrated"])

    def test_tampered_guard_rejected_before_fetching_test(self):
        p=propose_gated(lambda prompt:"A",opener=self.opener)
        p["proposals"][0]["gate"]["selected_for_blind_test"]="persistence_24h"
        with self.assertRaises(ValueError):
            independent_audit(p,opener=self.opener)
        self.assertEqual(sum(reveal for _,_,reveal in self.requests),0)

    def test_dates_pinned_and_unapproved_data_rejected(self):
        self.assertEqual(FRESH_TEST_DAYS,("2025-01-17","2025-11-17"))
        self.assertIn("end_date=20250116",query("8443970","2025-01-17"))
        self.assertIn("end_date=20250117",query("8443970","2025-01-17",True))
        with self.assertRaises(ValueError):
            query("8443970","2026-01-17",True)


if __name__=="__main__":
    unittest.main()
