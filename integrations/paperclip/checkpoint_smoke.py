"""Exercise actual checkpoint code on a real filesystem; inject provider failures."""
import argparse
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock
from uuid import uuid4
from checkpoint_store import execute_once, exclusive

BASE = None


class CheckpointTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=BASE)
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)
        self.cid = str(uuid4())
        self.task = str(uuid4())

    def invoke(self, provider, task=None):
        return execute_once(self.path, self.cid, "intelligence", task or self.task, provider)

    def test_receipt_reused_without_provider_calls(self):
        first = Mock(return_value={"source": "bounded fixture", "value": 1})
        receipt = self.invoke(first)
        first.assert_called_once()
        second = Mock(side_effect=AssertionError("Must not call provider twice"))
        self.assertEqual(self.invoke(second), receipt)
        second.assert_not_called()
        self.assertFalse((self.path / "intelligence.attempt-2").exists())
        print("RECEIPT REUSE PASS provider_calls=1 replay_calls=0", flush=True)

    def test_two_transient_failures_stop_and_future_wakes_do_not_call(self):
        provider = Mock(side_effect=TimeoutError("injected transport timeout"))
        with self.assertRaisesRegex(RuntimeError, "Terminal specialist failure"):
            self.invoke(provider)
        self.assertEqual(provider.call_count, 2)
        with self.assertRaises(RuntimeError):
            self.invoke(provider)
        self.assertEqual(provider.call_count, 2)
        self.assertFalse((self.path / "intelligence.json").exists())
        self.assertFalse((self.path / "intelligence.attempt-3").exists())
        print("TWO FAILURES STOP PASS provider_calls=2 third_calls=0", flush=True)

    def test_one_transient_recovery_then_reuse(self):
        provider = Mock(side_effect=[TimeoutError("injected"), {"ok": True}])
        first = self.invoke(provider)
        self.assertEqual(provider.call_count, 2)
        self.assertEqual(self.invoke(provider), first)
        self.assertEqual(provider.call_count, 2)
        print("TRANSIENT RECOVERY PASS provider_calls=2 replay_calls=0", flush=True)

    def test_crash_reservation_is_consumed(self):
        exclusive(self.path / "intelligence.attempt-1", {"company": self.cid,
            "role": "intelligence", "issue": self.task, "attempt": 1})
        provider = Mock(return_value={"ok": True})
        self.invoke(provider)
        provider.assert_called_once()
        self.assertTrue((self.path / "intelligence.attempt-2").exists())
        print("CRASH RESERVATION PASS prior_attempt_not_replayed", flush=True)

    def test_nontransient_and_tamper_fail_closed(self):
        provider = Mock(side_effect=ValueError("invalid input"))
        with self.assertRaises(RuntimeError):
            self.invoke(provider)
        with self.assertRaises(RuntimeError):
            self.invoke(provider)
        provider.assert_called_once()
        self.assertFalse((self.path / "intelligence.attempt-2").exists())
        other = str(uuid4())
        with self.assertRaises(ValueError):
            self.invoke(provider, other)
        provider.assert_called_once()
        print("INVALID SCOPE PASS no_retry_or_cross_task_reuse", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path)
    args = parser.parse_args()
    BASE = args.root
    if BASE:
        BASE.mkdir(parents=True, exist_ok=True, mode=0o700)
        print("CHECKPOINT TEST ROOT", BASE, flush=True)
    unittest.main(argv=[__file__], verbosity=2)
