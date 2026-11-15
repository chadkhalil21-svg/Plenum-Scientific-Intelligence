"""Test the real Plenum agent adapter's repair controller without an LLM.

We mock ONLY the expensive upstream model and file-editor transport; the
production Plenum execute() loop, syntax checks and fail-closed outcome run.
"""
import os
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

from plenum_ai import openhands_coding_agent as coder


class _FakeConversation:
    runs = 0
    messages = []
    ever_valid = True

    def __init__(self, agent, workspace, **kwargs):
        self.workspace = Path(workspace)
        self.limits = kwargs
        type(self).runs = 0
        type(self).messages = []

    def send_message(self, message):
        type(self).messages.append(message)

    def run(self):
        type(self).runs += 1
        if type(self).runs == 2 and type(self).ever_valid:
            content = 'def double(value):\n    return value * 2\n'
        else:
            content = 'def double(value):\n    "unterminated\n'
        (self.workspace / 'proposal.py').write_text(content)


class OpenHandsFeedbackContract(unittest.TestCase):
    def _sdk_patches(self):
        sdk = types.ModuleType('openhands.sdk')
        sdk.LLM = lambda **kwargs: kwargs
        sdk.Agent = lambda **kwargs: kwargs
        sdk.Tool = lambda **kwargs: kwargs
        sdk.Conversation = _FakeConversation
        tool = types.ModuleType('openhands.tools.file_editor')
        tool.FileEditorTool = type('FakeFileEditor', (), {'name': 'FileEditorTool'})
        return patch.dict(sys.modules, {
            'openhands': types.ModuleType('openhands'),
            'openhands.sdk': sdk,
            'openhands.tools': types.ModuleType('openhands.tools'),
            'openhands.tools.file_editor': tool,
        })

    def test_actual_adapter_asks_for_one_repair_and_revalidates(self):
        _FakeConversation.ever_valid = True
        with (self._sdk_patches(),
              patch.object(coder.importlib.metadata, 'version', return_value='1.60.1'),
              patch.dict(os.environ, {'PLENUM_EPHEMERAL_RUNNER': 'confirmed',
                                      'PLENUM_OPENHANDS_MODEL': 'fake/local',
                                      'PLENUM_OPENHANDS_BASE_URL': 'http://127.0.0.1:11434'})):
            result = coder.execute()
        self.assertEqual(_FakeConversation.runs, 2)
        self.assertEqual(result['repair_passes'], 1)
        self.assertTrue(result['candidate_syntax_valid'])
        self.assertTrue(result['human_review_required'])
        self.assertFalse(result['generated_code_executed'])
        self.assertFalse(result['production_written'])
        self.assertEqual(len(_FakeConversation.messages), 2)
        self.assertIn('SyntaxError', _FakeConversation.messages[1])

    def test_actual_adapter_refuses_two_invalid_attempts(self):
        _FakeConversation.ever_valid = False
        with (self._sdk_patches(),
              patch.object(coder.importlib.metadata, 'version', return_value='1.60.1'),
              patch.dict(os.environ, {'PLENUM_EPHEMERAL_RUNNER': 'confirmed',
                                      'PLENUM_OPENHANDS_MODEL': 'fake/local',
                                      'PLENUM_OPENHANDS_BASE_URL': 'http://127.0.0.1:11434'})):
            with self.assertRaisesRegex(RuntimeError, 'after one bounded agent repair'):
                coder.execute()
        self.assertEqual(_FakeConversation.runs, 2)


    def test_owner_issue_scopes_exact_public_source_and_review_only(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as directory:
            original = Path.cwd()
            try:
                os.chdir(directory)
                p = Path("src/plenum_ai/public_module.py")
                p.parent.mkdir(parents=True)
                p.write_text("def value():\n    return 1\n")
                evt = {"action": "opened",
                       "repository": {"full_name": coder.REPO},
                       "issue": {"user": {"login": coder.OWNER}, "number": 703,
                                 "title": coder.REPAIR_TITLE,
                                 "body": (coder.REPAIR_MARKER
                                          + "\nfile: src/plenum_ai/public_module.py"
                                          + "\nobjective: Improve a public helper while retaining its return contract")}}
                result = coder.parse_owner_repair_event(evt)
                self.assertEqual(result["source_file"], p.as_posix())
                self.assertFalse(result["auto_merge"])
                self.assertFalse(result["paid_api_authorized"])
                evt["issue"]["user"]["login"] = "untrusted-author"
                with self.assertRaises(PermissionError):
                    coder.parse_owner_repair_event(evt)
                evt["issue"]["user"]["login"] = coder.OWNER
                evt["issue"]["body"] = evt["issue"]["body"].replace(
                    "src/plenum_ai/public_module.py", "../secret.py")
                with self.assertRaises(PermissionError):
                    coder.parse_owner_repair_event(evt)
            finally:
                os.chdir(original)

    def test_real_repair_loop_exports_one_reviewable_diff_not_source_write(self):
        import hashlib
        import tempfile
        _FakeConversation.ever_valid = True
        with tempfile.TemporaryDirectory() as directory:
            original = Path.cwd()
            try:
                os.chdir(directory)
                p = Path("src/plenum_ai/public_module.py")
                p.parent.mkdir(parents=True)
                before = "def original_value():\n    return 42\n"
                p.write_text(before)
                with (self._sdk_patches(),
                      patch.object(coder.importlib.metadata, 'version', return_value='1.60.1'),
                      patch.dict(os.environ, {'PLENUM_EPHEMERAL_RUNNER': 'confirmed',
                                              'PLENUM_OPENHANDS_MODEL': 'fake/local',
                                              'PLENUM_OPENHANDS_BASE_URL': 'http://127.0.0.1:11434'})):
                    result = coder.execute(
                        "Improve a public helper with a clear documented return type",
                        source_file=p.as_posix(),
                        candidate_out="reports/openhands-review/issue-703.patch")
                self.assertEqual(p.read_text(), before)
                self.assertEqual(result["status"], "PROPOSAL_AWAITING_REVIEW")
                self.assertEqual(result["repair_passes"], 1)
                self.assertTrue(result["candidate_persisted"])
                self.assertFalse(result["production_written"])
                artifact = Path(result["candidate_artifact"])
                self.assertTrue(artifact.is_file())
                diff = artifact.read_text()
                self.assertIn("--- a/src/plenum_ai/public_module.py", diff)
                self.assertIn("+++ b/src/plenum_ai/public_module.py", diff)
                self.assertEqual(result["candidate_artifact_sha256"],
                                 hashlib.sha256(artifact.read_bytes()).hexdigest())
                with self.assertRaises(PermissionError):
                    coder._review_output_path(artifact.as_posix(), source_file=p.as_posix())
            finally:
                os.chdir(original)



if __name__ == '__main__':
    unittest.main()
