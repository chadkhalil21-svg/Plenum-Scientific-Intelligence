import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
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

    def test_exact_original_cloud_receipt_authorizes_only_one_local_recovery(self):
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
                if not hasattr(coding, 'reserve_local_fallback'):
                    self.fail('No authorized same-job local fallback after cloud quota failure')
                for key, wrong in [('source_sha256', 'bad'), ('origin_issue_number', 124),
                                   ('origin_run_id', '9999'), ('origin_run_attempt', '2'),
                                   ('candidate_persisted', True), ('failure_category', 'PERMISSION_DENIED')]:
                    file.write_text(json.dumps({**report, key: wrong}))
                    self.assertFalse(coding.reserve_local_fallback(event, run_id='1234', run_attempt='1'), key)
                file.write_text(original)
                self.assertFalse(coding.reserve_local_fallback(event, run_id='1234', run_attempt='2'))
                candidate = Path('reports/openhands-review/issue-123.patch')
                candidate.parent.mkdir()
                candidate.write_text('already persisted')
                self.assertFalse(coding.reserve_local_fallback(event, run_id='1234', run_attempt='1'))
                candidate.unlink()
                self.assertTrue(coding.reserve_local_fallback(event, run_id='1234', run_attempt='1'))
                self.assertEqual(Path('reports/openhands-cloud-failure.json').read_text(), original)
                self.assertFalse(coding.reserve_local_fallback(event, run_id='1234', run_attempt='1'))
                archive = Path('reports/openhands-cloud-failure.json')
                archive.write_text(json.dumps(report, indent=2))  # Same fields, different digest.
                with self.assertRaises(PermissionError):
                    coding.consume_local_fallback(event, run_id='1234', run_attempt='1')
                archive.write_text(original)
                consumed = coding.consume_local_fallback(event, run_id='1234', run_attempt='1')
                self.assertEqual(consumed['cloud_attempt_status'], 'BLOCKED_ORIGINAL_DAILY_FREE_AI_CAP')
                self.assertTrue(consumed['local_fallback_attempted'])
                with self.assertRaises(PermissionError):
                    coding.consume_local_fallback(event, run_id='1234', run_attempt='1')
            finally:
                os.chdir(previous)

