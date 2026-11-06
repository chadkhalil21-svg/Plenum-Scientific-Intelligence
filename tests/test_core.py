"""Offline checks for bounded research features."""
import io
import json
import unittest
from plenum_ai.evolve import default_benchmarks, evaluate_evolution, score
from plenum_ai.literature import paper_record, search_papers
from plenum_ai.physics import circular_orbit_speed
from plenum_ai.research import make_report


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.close()


class FoundationTests(unittest.TestCase):
    def test_orbital_speed(self):
        self.assertTrue(7600 < circular_orbit_speed(6771000) < 7800)

    def test_orbital_reject_invalid(self):
        with self.assertRaises(ValueError):
            circular_orbit_speed(-1)

    def test_normalize_source(self):
        paper = paper_record({"id": "W1", "title": "Example", "publication_year": 2026})
        self.assertEqual(paper["url"], "W1")

    def test_literature_stub(self):
        def fake_open(req, timeout):
            return FakeResponse(json.dumps({"results": [{"id": "W2", "title": "Test"}]}).encode())
        papers = search_papers("gravity", opener=fake_open)
        self.assertEqual(papers[0]["id"], "W2")

    def test_literature_bounded(self):
        with self.assertRaises(ValueError):
            search_papers("physics", limit=50)

    def test_report_avoids_discovery_claim(self):
        result = make_report("question", [{"id": "W1", "title": "A paper"}])
        self.assertFalse(result["verified_discovery"])

    def test_independent_critic_role(self):
        calls = []
        def fake_llm(prompt, model):
            calls.append(prompt)
            return "unverified"
        result = make_report("physics", [], model="local", generator=fake_llm)
        self.assertEqual(len(calls), 2)
        self.assertIn("Independent scientific critic", calls[1])
        self.assertFalse(result["verified_discovery"])

    def test_ranker(self):
        self.assertGreater(score("photonic memory", "photonic memory chip", 1),
                           score("photonic memory", "memory photonic chip", 1))

    def test_improvement_held_out(self):
        result = evaluate_evolution(default_benchmarks())
        self.assertTrue(result["accepted_for_proposal"])
        self.assertFalse(result["deployed"])
        self.assertGreater(result["candidate"]["holdout_accuracy"],
                           result["baseline"]["holdout_accuracy"])


if __name__ == "__main__":
    unittest.main()
