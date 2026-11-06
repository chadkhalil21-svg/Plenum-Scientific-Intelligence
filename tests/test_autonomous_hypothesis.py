"""Independent blind-proposal and final-day evaluation tests, no model downloads."""
from datetime import datetime, timedelta, timezone
from math import pi, sin
from urllib.parse import urlsplit, parse_qs
import io
import json
import unittest

from plenum_ai.autonomous_hypothesis import (
    CUTOFF_DATES, ORDER, LETTERS, PERIODS, STATIONS, api_query,
    development_scores, make_proposals, audit_proposals, selection_prompt,
)
from plenum_ai.noaa_empirical import parse_observations


class Stream(io.BytesIO):
    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.close()


def fixture(cutoff, end_day):
    """Synthetic four-harmonic ground truth; not presented as NOAA measurements."""
    origin = cutoff - timedelta(days=16)
    hours = 17 * 24 if end_day else 16 * 24
    out = []
    for hour in range(hours):
        t = origin + timedelta(hours=hour)
        h = (t - datetime(2026, 1, 1, tzinfo=timezone.utc)).total_seconds() / 3600
        value = 1.4 + sum(
            weight * sin(2*pi*h/period + phase)
            for period, weight, phase in zip(
                PERIODS["four_constituents"],
                (0.85, 0.16, 0.13, 0.11),
                (0.2, 1.0, 0.6, 0.9),
            )
        )
        out.append({"t": t.strftime("%Y-%m-%d %H:%M"), "v": f"{value:.10f}"})
    return out


class BlindHypothesisTests(unittest.TestCase):
    def setUp(self):
        self.requests = []
        self.choice_prompts = []

    def opener(self, request, timeout=25):
        self.assertEqual(timeout, 25)
        query = parse_qs(urlsplit(request.full_url).query)
        self.assertEqual(query["product"][0], "hourly_height")
        station = query["station"][0]
        self.assertIn(station, STATIONS)
        end_date = query["end_date"][0]
        day = next(d for d in CUTOFF_DATES
                   if end_date in (d.replace("-", ""), (
                       datetime.strptime(d, "%Y-%m-%d") - timedelta(days=1)
                   ).strftime("%Y%m%d")))
        cutoff = datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        reveal = end_date == cutoff.strftime("%Y%m%d")
        self.requests.append((station, day, reveal))
        return Stream(json.dumps({"data": fixture(cutoff, reveal)}).encode())

    def choose(self, prompt):
        self.choice_prompts.append(prompt)
        self.assertNotIn("actual test water level", prompt)
        self.assertIn("development mean absolute error", prompt)
        self.assertIn("Choose one letter only", prompt)
        return "D"

    def test_proposer_cannot_download_heldout_measurements(self):
        proposal = make_proposals(self.choose, opener=self.opener)
        self.assertEqual(len(self.requests), 4)
        self.assertTrue(all(not item[2] for item in self.requests))
        self.assertEqual(len(self.choice_prompts), 4)
        self.assertTrue(all(x["development"]["selected"] == "four_constituents"
                            for x in proposal["proposals"]))
        self.assertTrue(all(not x["development"]["holdout_measurements_seen"]
                            for x in proposal["proposals"]))
        self.assertFalse(proposal["agent_accessed_test_measurements"])
        self.assertFalse(proposal["production_model_changed"])

    def test_blind_proposal_then_separate_independent_audit(self):
        proposals = make_proposals(self.choose, opener=self.opener)
        audit = audit_proposals(proposals, opener=self.opener)
        self.assertEqual(len(self.requests), 8)
        self.assertEqual(sum(bool(x[2]) for x in self.requests), 4)
        self.assertEqual(audit["trials"], 4)
        self.assertEqual(audit["won_against_persistence"], 4)
        self.assertEqual(audit["won_against_fixed_reference"], 0)
        self.assertTrue(all(x["test_hours"] == 24 for x in audit["cases"]))
        self.assertFalse(audit["AI_found_generalizable_improvement"])
        self.assertFalse(audit["eligible_for_automatic_deployment"])

    def test_invalid_choices_rejected_without_substitution(self):
        with self.assertRaises(ValueError):
            make_proposals(lambda prompt: "UNKNOWN", opener=self.opener)

    def test_invalid_manifest_rejected_before_final_observations(self):
        p = make_proposals(self.choose, opener=self.opener)
        p["proposals"].pop()
        with self.assertRaises(ValueError):
            audit_proposals(p, opener=self.opener)

    def test_selecting_baseline_is_valid_negative_outcome(self):
        p = make_proposals(lambda prompt: "A", opener=self.opener)
        r = audit_proposals(p, opener=self.opener)
        self.assertEqual(r["won_against_persistence"], 0)
        self.assertEqual(r["won_against_fixed_reference"], 0)

    def test_precommitted_dates_and_approved_sources(self):
        self.assertEqual(CUTOFF_DATES, ("2026-01-17", "2026-04-17"))
        self.assertIn("end_date=20260116", api_query("8443970", "2026-01-17"))
        self.assertIn("end_date=20260117", api_query("8443970", "2026-01-17", True))
        with self.assertRaises(ValueError):
            api_query("000000", "2026-01-17", True)
        with self.assertRaises(ValueError):
            api_query("8443970", "2025-06-17", True)


if __name__ == "__main__":
    unittest.main()
