"""Regression for recovery from checksum-valid malformed memory records."""
import hashlib
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from plenum_ai.memory import canonical, make_record, recall, save, verify


class MemoryRecallRecoveryTests(unittest.TestCase):
    def test_malformed_source_does_not_prevent_healthy_recall(self):
        healthy = make_record({"question": "orbit survey", "source_status": "offline"}, {})
        payload = {key: value for key, value in healthy.items() if key not in ("id", "sha256")}
        payload["sources"] = [{"id": "legacy-source"}]
        digest = hashlib.sha256(canonical(payload).encode("utf-8")).hexdigest()
        malformed = dict(payload, id=digest[:24], sha256=digest)
        with TemporaryDirectory() as directory:
            save(healthy, directory)
            Path(directory, malformed["id"] + ".json").write_text(json.dumps(malformed), encoding="utf-8")
            self.assertEqual([record["id"] for record in recall(directory, "orbit")], [healthy["id"]])
            with self.assertRaises(ValueError):
                verify(malformed)
            with self.assertRaises(ValueError):
                save(malformed, directory)

