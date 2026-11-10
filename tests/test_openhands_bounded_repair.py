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


if __name__ == '__main__':
    unittest.main()
