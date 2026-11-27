"""Prospective NOAA proposal parser acceptance; frozen before model execution."""
import json
import unittest
from plenum_ai import noaa_revision_agent as agent


class NestedResponseAcceptance(unittest.TestCase):
    def test_bounded_text_can_exceed_json_parser_recursion_limit(self):
        for depth in (1500, 2200):
            for raw in ("[" * depth + "0" + "]" * depth,
                        '{"alpha":' + "[" * depth + "0" + "]" * depth + "}"):
                self.assertLess(len(raw), 5500)
                for response in (raw, chr(96)*3 + "json\n" + raw + "\n" + chr(96)*3):
                    with self.subTest(depth=depth, length=len(response)):
                        self.assertEqual(agent.parse_candidate(response),
                            {"status": "invalid_json", "candidate": None})

    def test_existing_valid_invalid_and_schema_gates_preserved(self):
        proposal = {"alpha": 0.5, "gain": 1.0,
                    "hypothesis": "Public numerical forecast may improve accuracy.",
                    "falsifier": "Reject when independent forecast error rises."}
        raw = json.dumps(proposal)
        self.assertEqual(agent.parse_candidate(raw)["status"], "valid")
        self.assertEqual(agent.parse_candidate("[]")["status"], "invalid_schema")
        self.assertEqual(agent.parse_candidate(raw[:-1] + ', "alpha": 0.6}')["status"], "invalid_json")
        self.assertEqual(agent.parse_candidate(json.dumps(dict(proposal, alpha=True)))["status"], "invalid_parameters")
        self.assertEqual(agent.parse_candidate("[" * 5501)["status"], "invalid_response")
