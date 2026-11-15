import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

from plenum_ai import openhands_coding_agent as coding


class AiderLocalRouteTest(unittest.TestCase):
    def test_owner_explicit_local_route_keeps_review_only_and_emits_single_diff(self):
        with tempfile.TemporaryDirectory() as folder:
            previous = Path.cwd()
            os.chdir(folder)
            try:
                source = Path('src/plenum_ai/public_example.py')
                source.parent.mkdir(parents=True)
                source.write_text('def result():\n    return 1\n', encoding='utf-8')
                event = {'action': 'opened', 'repository': {'full_name': coding.REPO},
                         'issue': {'user': {'login': coding.OWNER}, 'number': 123,
                                   'title': coding.REPAIR_TITLE,
                                   'body': 'PLENUM_AIDER_LOCAL_PUBLIC_REPAIR_V1\nfile: src/plenum_ai/public_example.py\nobjective: Correct the public function to return two.'}}
                try:
                    approved = coding.parse_owner_repair_event(event)
                except ValueError:
                    self.fail('Explicit original-owner local coding route was rejected')
                self.assertEqual(approved['engine'], 'aider_local_ollama')
                self.assertFalse(approved['auto_merge'])
                self.assertFalse(approved['paid_api_authorized'])

                def isolated_model(command, **kwargs):
                    mount = next(s for s in command if s.startswith('type=bind,src='))
                    bound = Path(mount.split(',')[1].removeprefix('src='))
                    self.assertIn('--network=plenum-coding-isolated', command)
                    self.assertIn('--read-only', command)
                    self.assertEqual(command[command.index('--model') + 1], 'ollama_chat/qwen2.5-coder:7b')
                    # #755's local model could not emit Aider SEARCH/REPLACE syntax.
                    self.assertEqual(command[command.index('--edit-format') + 1], 'whole')
                    self.assertIn('--no-suggest-shell-commands', command)
                    self.assertIn('--no-auto-test', command)
                    self.assertNotIn(str(Path.cwd()), str(bound.parent))
                    self.assertNotIn('ACTION_TOKEN', kwargs['env'])
                    (bound / 'proposal.py').write_text('def result():\n    return 2\n', encoding='utf-8')

                with patch.dict(os.environ, {'PLENUM_EPHEMERAL_RUNNER': 'confirmed', 'ACTION_TOKEN': 'never-pass-this'}):
                    with patch('plenum_ai.openhands_coding_agent.subprocess.run', side_effect=isolated_model):
                        report = coding.execute_local(approved['task'], source_file=str(source),
                            candidate_out='reports/openhands-review/issue-123.patch')
                self.assertEqual(report['status'], 'PROPOSAL_AWAITING_REVIEW')
                self.assertEqual(report['upstream'], 'Aider-AI/aider')
                self.assertTrue(report['model_run_completed'])
                self.assertFalse(report['generated_code_executed'])
                candidate = Path(report['candidate_artifact']).read_bytes()
                self.assertEqual(candidate, b'--- a/src/plenum_ai/public_example.py\n+++ b/src/plenum_ai/public_example.py\n@@ -1,2 +1,2 @@\n def result():\n-    return 1\n+    return 2\n')
                self.assertEqual(report['candidate_artifact_sha256'], hashlib.sha256(candidate).hexdigest())
                self.assertEqual(source.read_text(), 'def result():\n    return 1\n')

                event['issue']['user']['login'] = 'untrusted'
                with self.assertRaises(PermissionError):
                    coding.parse_owner_repair_event(event)
            finally:
                os.chdir(previous)

    @patch.dict(os.environ, {'PLENUM_GEMINI_FREE_PROJECT_APPROVAL': 'owner-verified-default-gemini-project-free-2026-11-15'})
    def test_exact_original_cloud_receipt_authorizes_only_one_gemini_recovery(self):
        with tempfile.TemporaryDirectory() as folder:
            previous = Path.cwd()
            os.chdir(folder)
            try:
                source = Path('src/plenum_ai/public_example.py')
                source.parent.mkdir(parents=True)
                source.write_text('def result():\n    return 1\n', encoding='utf-8')
                event = {'action': 'opened', 'repository': {'full_name': coding.REPO},
                         'issue': {'user': {'login': coding.OWNER}, 'number': 123,
                                   'title': coding.REPAIR_TITLE,
                                   'body': 'PLENUM_OPENHANDS_PUBLIC_REPAIR_V1\nfile: src/plenum_ai/public_example.py\nobjective: Correct the public function to return two.'}}
                report = {'schema': 'plenum-openhands-coding-agent-v1',
                          'upstream': 'OpenHands/software-agent-sdk',
                          'status': 'BLOCKED_ORIGINAL_DAILY_FREE_AI_CAP',
                          'failure_category': 'LOCAL_DURABLE_OBJECT_DAILY_BUDGET',
                          'task': 'Correct the public function to return two.',
                          'source_file': str(source), 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                          'candidate_persisted': False, 'model_run_completed': False,
                          'generated_code_executed': False, 'production_written': False,
                          'external_accounts_changed': False, 'no_paid_fallback': True,
                          'retry_same_day_authorized': False,
                          'origin_issue_number': 123, 'origin_run_id': '1234', 'origin_run_attempt': '1'}
                file = Path('reports/openhands-agent-review.json')
                file.parent.mkdir()
                original = json.dumps(report)
                file.write_text(original)
                if not hasattr(coding, 'reserve_gemini_fallback'):
                    self.fail('No authorized same-job Gemini fallback after cloud quota failure')
                for key, wrong in [('source_sha256', 'bad'), ('origin_issue_number', 124),
                                   ('origin_run_id', '9999'), ('origin_run_attempt', '2'),
                                   ('candidate_persisted', True), ('failure_category', 'PERMISSION_DENIED')]:
                    file.write_text(json.dumps({**report, key: wrong}))
                    self.assertFalse(coding.reserve_gemini_fallback(event, run_id='1234', run_attempt='1'), key)
                file.write_text(original)
                self.assertFalse(coding.reserve_gemini_fallback(event, run_id='1234', run_attempt='2'))
                with patch.dict(os.environ, {'PLENUM_GEMINI_FREE_PROJECT_APPROVAL': 'uncertain'}):
                    self.assertFalse(coding.reserve_gemini_fallback(event, run_id='1234', run_attempt='1'))
                candidate = Path('reports/openhands-review/issue-123.patch')
                candidate.parent.mkdir()
                candidate.write_text('already persisted')
                self.assertFalse(coding.reserve_gemini_fallback(event, run_id='1234', run_attempt='1'))
                candidate.unlink()
                self.assertTrue(coding.reserve_gemini_fallback(event, run_id='1234', run_attempt='1'))
                self.assertEqual(Path('reports/openhands-cloud-failure.json').read_text(), original)
                self.assertFalse(coding.reserve_gemini_fallback(event, run_id='1234', run_attempt='1'))
                archive = Path('reports/openhands-cloud-failure.json')
                archive.write_text(json.dumps(report, indent=2))  # Same fields, different digest.
                with self.assertRaises(PermissionError):
                    coding.consume_gemini_fallback(event, run_id='1234', run_attempt='1')
                archive.write_text(original)
                consumed = coding.consume_gemini_fallback(event, run_id='1234', run_attempt='1')
                self.assertEqual(consumed['cloud_attempt_status'], 'BLOCKED_ORIGINAL_DAILY_FREE_AI_CAP')
                self.assertTrue(consumed['gemini_fallback_attempted'])
                self.assertEqual(consumed['fallback_engine'], 'gemini_free_openhands')
                with self.assertRaises(PermissionError):
                    coding.consume_gemini_fallback(event, run_id='1234', run_attempt='1')
            finally:
                os.chdir(previous)

    def test_gemini_uses_fixed_owner_approved_free_route_and_bounded_fileeditor(self):
        with tempfile.TemporaryDirectory() as folder:
            previous = Path.cwd()
            os.chdir(folder)
            try:
                source = Path('src/plenum_ai/public_example.py')
                source.parent.mkdir(parents=True)
                source.write_text('def result():\n    return 1\n', encoding='utf-8')
                args = {'source_file': str(source), 'candidate_out': 'reports/openhands-review/issue-123.patch',
                        'gemini_recovery': True}
                env = {'PLENUM_EPHEMERAL_RUNNER': 'confirmed', 'PLENUM_GEMINI_API_KEY': 'example-not-a-secret',
                       'PLENUM_OPENHANDS_API_KEY': 'never-send-cloud-key',
                       'PLENUM_OPENHANDS_MODEL': 'untrusted-other-model',
                       'PLENUM_OPENHANDS_BASE_URL': 'https://untrusted.example'}
                with patch.dict(os.environ, {**env, 'PLENUM_GEMINI_FREE_PROJECT_APPROVAL': 'uncertain'}):
                    try:
                        coding.execute('Correct the public function to return two.', **args)
                    except TypeError:
                        self.fail('Missing bounded Gemini provider route')
                    except PermissionError:
                        pass
                    else:
                        self.fail('Unverified Free project must be rejected before model invocation')

                observed = {'runs': 0}
                class FileEditorExecutor:
                    def __init__(self, *, workspace_root):
                        self.root = Path(workspace_root)
                    def __call__(self, action, conversation=None):
                        observed.setdefault('delegated', []).append(action.path)
                        return SimpleNamespace(is_error=False)
                class FileEditorTool:
                    def __init_subclass__(cls, **kwargs):
                        super().__init_subclass__(**kwargs)
                        cls.name = 'proposal_only_file_editor'
                    @classmethod
                    def create(cls, conv_state):
                        return [cls()]
                    def set_executor(self, executor):
                        self.executor = executor
                        return self
                class Conversation:
                    def __init__(self, **kwargs):
                        observed['conversation'] = kwargs
                        self.workspace = Path(kwargs['workspace'])
                    def send_message(self, message):
                        observed['message'] = message
                    def run(self):
                        observed['runs'] += 1
                        candidate = self.workspace / 'proposal.py'
                        editor = observed['registered'].create(SimpleNamespace(workspace=SimpleNamespace(working_dir=str(self.workspace))))[0].executor
                        for command in ('view', 'create', 'str_replace', 'insert', 'undo_edit'):
                            for path in ('/etc/passwd', str(self.workspace), str(self.workspace / '..' / 'proposal.py'), 'proposal.py'):
                                self_outer.assertTrue(editor(SimpleNamespace(command=command, path=path)).is_error)
                        self_outer.assertFalse(editor(SimpleNamespace(command='view', path=str(candidate))).is_error)
                        candidate.unlink()
                        candidate.symlink_to('/etc/passwd')
                        self_outer.assertTrue(editor(SimpleNamespace(command='view', path=str(candidate))).is_error)
                        candidate.unlink()
                        candidate.mkdir()
                        self_outer.assertTrue(editor(SimpleNamespace(command='view', path=str(candidate))).is_error)
                        candidate.rmdir()
                        self_outer.assertFalse(editor(SimpleNamespace(command='create', path=str(candidate))).is_error)
                        candidate.write_text('def result():\n    return 2\n', encoding='utf-8')
                def llm(**kwargs):
                    observed['llm'] = kwargs
                    return SimpleNamespace(**kwargs)
                sdk = ModuleType('openhands.sdk')
                sdk.Agent = lambda **kwargs: SimpleNamespace(**kwargs)
                sdk.LLM, sdk.Conversation = llm, Conversation
                sdk.Tool = lambda **kwargs: SimpleNamespace(**kwargs)
                editor = ModuleType('openhands.tools.file_editor')
                editor.FileEditorTool = FileEditorTool
                tool = ModuleType('openhands.sdk.tool')
                tool.register_tool = lambda name, factory: observed.update(registered=factory)
                impl = ModuleType('openhands.tools.file_editor.impl')
                impl.FileEditorExecutor = FileEditorExecutor
                definition = ModuleType('openhands.tools.file_editor.definition')
                definition.FileEditorObservation = SimpleNamespace(from_text=lambda **kwargs: SimpleNamespace(**kwargs))
                self_outer = self
                with patch.dict(os.environ, {**env, 'PLENUM_GEMINI_FREE_PROJECT_APPROVAL': 'owner-verified-default-gemini-project-free-2026-11-15'}), \
                     patch.dict(sys.modules, {m.__name__: m for m in (sdk, editor, tool, impl, definition)}), \
                     patch.object(coding.importlib.metadata, 'version', return_value='1.60.1'):
                    report = coding.execute('Correct the public function to return two.', **args)
                self.assertEqual(observed['runs'], 1)
                self.assertEqual(observed['conversation']['max_iteration_per_run'], 4)
                self.assertEqual([t.name for t in observed['conversation']['agent'].tools], ['proposal_only_file_editor'])
                self.assertEqual(len(observed['delegated']), 2)
                self.assertIn(observed['delegated'][0], observed['message'])
                options = observed['llm']
                self.assertEqual(options['model'], 'gemini/gemini-3.5-flash-lite')
                self.assertEqual(options['api_key'], env['PLENUM_GEMINI_API_KEY'])
                self.assertNotIn('base_url', options)
                self.assertEqual(options['num_retries'], 0)
                self.assertEqual(options['max_output_tokens'], 4096)
                self.assertFalse(options['caching_prompt'])
                self.assertFalse(options['log_completions'])
                self.assertEqual(report['engine'], 'gemini_free_openhands')
                self.assertTrue(report['candidate_persisted'])
                self.assertFalse(report['production_written'])
                self.assertNotIn(env['PLENUM_GEMINI_API_KEY'], str(report))
                self.assertTrue(Path(report['candidate_artifact']).is_file())
            finally:
                os.chdir(previous)


