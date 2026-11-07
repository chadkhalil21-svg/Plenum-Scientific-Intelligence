"""Offline contract tests only. No credential, network, voice or model calls."""
import io
import json
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from plenum_ai import voice_livekit as voice


class VoiceIntegrationContract(unittest.TestCase):
    def test_preview_no_services_or_claims(self):
        doc = voice.preview()
        self.assertEqual(doc["package_pin"], "livekit-agents==1.8.9")
        self.assertFalse(doc["network_started"])
        self.assertFalse(doc["microphone_connected"])
        self.assertFalse(doc["AGI_demonstrated"])
        self.assertFalse(doc["consciousness_demonstrated"])
        self.assertTrue(doc["cloud_provider_cost_possible"])

    def test_no_approval_and_missing_credentials_fail_closed(self):
        with self.assertRaises(PermissionError):
            voice.approval_check({})
        with self.assertRaises(PermissionError):
            voice.approval_check({voice.APPROVAL_ENV: "yes"})
        with self.assertRaisesRegex(RuntimeError, "connection parameters"):
            voice.approval_check({voice.APPROVAL_ENV: "YES"})
        env = {voice.APPROVAL_ENV: "YES"}
        env.update({k: "test-only" for k in voice.REQUIRED_ENV})
        self.assertTrue(voice.approval_check(env))

    def test_default_command_does_not_import_sdk_or_run_server(self):
        buffer = io.StringIO()
        with patch.object(voice, "build_server", side_effect=AssertionError("SDK loaded")):
            with redirect_stdout(buffer):
                voice.main([])
        info = json.loads(buffer.getvalue())
        self.assertFalse(info["network_started"])
        self.assertFalse(info["model_inference_executed"])

    def test_live_command_checks_approval_before_any_import(self):
        with patch.dict("os.environ", {voice.APPROVAL_ENV: ""}, clear=True):
            with patch.object(voice, "build_server", side_effect=AssertionError("SDK loaded")):
                with self.assertRaises(PermissionError):
                    voice.main(["--serve"])

    def test_instructions_are_honest_and_bound_tools(self):
        self.assertIn("authorized user", voice.INSTRUCTIONS)
        self.assertIn("Do not assert consciousness", voice.INSTRUCTIONS)
        self.assertIn("No external tool, transaction", voice.INSTRUCTIONS)


if __name__ == "__main__":
    unittest.main()
