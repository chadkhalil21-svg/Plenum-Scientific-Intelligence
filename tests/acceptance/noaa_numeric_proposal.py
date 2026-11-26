"""Independent frozen acceptance for a real proposal-validator overflow.

These are synthetic parameters only. No held-out observations, model calls,
network or executable agent output other than the isolated candidate module.
"""
import json
import unittest
from plenum_ai.noaa_revision_agent import parse_candidate


def proposal(**changes):
    return json.dumps({
        "alpha": 0.4, "gain": 1.0,
        "hypothesis": "The reference forecasts improve development accuracy.",
        "falsifier": "Reject the claim when the measured error is higher.",
        **changes,
    })


class NumericProposalAcceptance(unittest.TestCase):
    def test_oversized_signed_integers_are_rejected_without_exception(self):
        for field in ("alpha", "gain"):
            for value in (10**309, -(10**309), 10**1000, -(10**1000)):
                raw = proposal(**{field: value})
                for response in (raw, "```json\n" + raw + "\n```"):
                    with self.subTest(field=field, digits=len(str(value))):
                        self.assertEqual(parse_candidate(response),
                                         {"status": "invalid_parameters", "candidate": None})

    def test_preserve_numeric_boundaries_and_existing_rejection_gates(self):
        for alpha, gain in ((0, 0.6), (1, 1.4), (0.25, 1)):
            with self.subTest(alpha=alpha, gain=gain):
                result = parse_candidate(proposal(alpha=alpha, gain=gain))
                self.assertEqual(result["status"], "valid")
                self.assertEqual(result["candidate"]["alpha"], float(alpha))
                self.assertEqual(result["candidate"]["gain"], float(gain))
        for changes in ({"alpha": True}, {"gain": False}, {"alpha": -0.1},
                        {"alpha": 1.1}, {"gain": 0.59}, {"gain": 1.41},
                        {"alpha": float("nan")}, {"gain": float("inf")},
                        {"gain": -float("inf")}, {"gain": "1"}):
            with self.subTest(changes=changes):
                self.assertEqual(parse_candidate(proposal(**changes)),
                                 {"status": "invalid_parameters", "candidate": None})
        raw = proposal()
        self.assertEqual(parse_candidate(raw[:-1] + ', "alpha": 0.5}'),
                         {"status": "invalid_json", "candidate": None})
        self.assertEqual(parse_candidate(proposal(hypothesis="short"))["status"],
                         "invalid_scientific_claim")
        self.assertEqual(parse_candidate(proposal(command="x"))["status"], "invalid_schema")
