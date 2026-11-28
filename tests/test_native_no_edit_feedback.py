"""Offline behavioral checks: bounded native correction, not inference evidence."""
import os
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch
from plenum_ai import openhands_coding_agent as a


class NativeNoEditFeedback(unittest.TestCase):
    def run_simulated(self, *, edit_second=False, gemini=False, other=False):
        calls, messages = [], []
        original = b"x = 1\n"
        class Conversation:
            def __init__(self, **kw):
                self.path = Path(kw["workspace"]) / "proposal.py"
            def send_message(self, message):
                messages.append(message)
            def run(self):
                calls.append(1)
                if edit_second and len(calls) == 2:
                    self.path.write_bytes(b"x = 2\n")
        sdk = types.ModuleType("openhands.sdk")
        sdk.Conversation = Conversation
        sdk.Agent = sdk.LLM = sdk.Tool = lambda **kw: None
        env = {"PLENUM_EPHEMERAL_RUNNER":"confirmed",
               "PLENUM_OPENHANDS_MODEL":"other" if other else "openai/glm-4.7-flash",
               "PLENUM_OPENHANDS_BASE_URL":a.ORIGINAL_FREE_CODING_ENDPOINT,
               "PLENUM_OPENHANDS_API_KEY":"mock",
               "PLENUM_GEMINI_API_KEY":"mock",
               "PLENUM_GEMINI_FREE_PROJECT_APPROVAL":a.GEMINI_FREE_APPROVAL}
        with patch.dict(os.environ, env, clear=True), patch.dict(sys.modules, {"openhands.sdk":sdk}), \
             patch.object(a, "plan", return_value={}), patch.object(a, "gemini_plan", return_value={}), \
             patch.object(a, "_public_source", return_value=(original,"mock")), \
             patch.object(a, "_review_output_path", return_value=None), \
             patch.object(a, "_register_proposal_editor", return_value="FileEditorTool"), \
             patch.object(a.importlib.metadata, "version", return_value=a.PINNED_VERSION):
            if edit_second and not gemini and not other:
                result = a.execute("Repair public source", source_file="src/plenum_ai/example.py")
                self.assertTrue(result["model_run_completed"])
                self.assertEqual(result["repair_passes"], 1)
            else:
                with self.assertRaises(a.NoReviewableProposalError):
                    a.execute("Repair public source", source_file="src/plenum_ai/example.py",
                              candidate_out="mock" if gemini else None, gemini_recovery=gemini)
        return calls, messages

    def test_cloud_no_edit_gets_one_existing_correction(self):
        calls, messages = self.run_simulated(edit_second=True)
        self.assertEqual(len(calls), 2)
        self.assertIn("byte-identical", messages[1])

    def test_cloud_repeated_no_edit_stops(self):
        calls, messages = self.run_simulated()
        self.assertEqual((len(calls), len(messages)), (2, 2))

    def test_gemini_and_other_routes_unchanged(self):
        for kwargs in ({"gemini":True}, {"other":True}):
            with self.subTest(kwargs=kwargs):
                calls, messages = self.run_simulated(**kwargs)
                self.assertEqual((len(calls), len(messages)), (1, 1))
