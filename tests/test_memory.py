"""Offline tests: memory integrity, recall and independent synthetic benchmark audit."""
import copy
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from plenum_ai.memory import make_record, verify, save, recall
from plenum_ai.audit import independent_audit
from plenum_ai.evolve import default_benchmarks, evaluate_evolution
from plenum_ai.mission import run_mission


def fixture_record():
    case = default_benchmarks()
    result = evaluate_evolution(case)
    result["independent_audit"] = independent_audit(case, result)
    mission = {"question": "Photonic memory research", "source_status": "retrieved_metadata",
               "literature_and_hypotheses": {"papers": [{"id": "W1", "title": "Photonic memory simulation",
                    "url": "https://openalex.org/W1", "year": 2026}]},
               "numeric_benchmark_verified": True}
    return make_record(mission, result, "test-run", "test-sha")


class MemoryTests(unittest.TestCase):
    def test_integrity_and_recall(self):
        record = fixture_record()
        self.assertTrue(verify(record))
        with TemporaryDirectory() as directory:
            filename, added = save(record, directory)
            self.assertTrue(added)
            self.assertFalse(save(record, directory)[1])
            self.assertTrue(Path(filename).exists())
            self.assertEqual(recall(directory, "photonic memory")[0]["id"], record["id"])

    def test_modified_evidence_is_rejected(self):
        mutated = copy.deepcopy(fixture_record())
        mutated["question"] = "new claim"
        with self.assertRaises(ValueError):
            verify(mutated)

    def test_unreviewed_discovery_not_claimed(self):
        mutated = copy.deepcopy(fixture_record())
        mutated["scientific_discovery_verified"] = True
        with self.assertRaises(ValueError):
            verify(mutated)

    def test_prior_metadata_read_in_mission(self):
        record = fixture_record()
        with TemporaryDirectory() as directory:
            save(record, directory)
            result = run_mission("photonic memory", offline=True, memory_dir=directory)
            self.assertEqual(result["prior_memory_ids"], [record["id"]])
            self.assertTrue(any("from_public_memory" in item for item in result["literature_and_hypotheses"]["papers"]))
            self.assertFalse(result["verified_new_scientific_discovery"])

    def test_corrupt_record_ignored(self):
        with TemporaryDirectory() as directory:
            Path(directory, "bad.json").write_text('{"question":"fake"}')
            self.assertEqual(recall(directory, "fake"), [])


class ImprovementAuditTests(unittest.TestCase):
    def test_independent_metrics(self):
        data = default_benchmarks()
        report = evaluate_evolution(data)
        audit = independent_audit(data, report)
        self.assertTrue(audit["passed"])
        self.assertEqual(audit["holdout_n"], 12)

    def test_false_accuracy_is_rejected(self):
        data = default_benchmarks()
        result = evaluate_evolution(data)
        result["candidate"]["holdout_accuracy"] = 10
        self.assertFalse(independent_audit(data, result)["passed"])

    def test_overlapping_splits_are_rejected(self):
        data = copy.deepcopy(default_benchmarks())
        data["holdout"][0] = data["train"][0]
        self.assertFalse(independent_audit(data, evaluate_evolution(data))["passed"])


if __name__ == "__main__":
    unittest.main()
