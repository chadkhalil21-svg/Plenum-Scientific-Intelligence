"""Offline exact owner routing regression, not proof of live model success."""
import unittest
from pathlib import Path
from plenum_ai import openhands_coding_agent as coding

class ProviderNormalizationRecoveryRoute(unittest.TestCase):
    def test_registered_scope_and_correction_path(self):
        source, task = next(k for k, v in coding.TASK_ACCEPTANCE.items()
                            if v == "federated_provider_doi_normalization.py")
        original = Path(source).read_bytes()
        event = {"action":"opened","repository":{"full_name":coding.REPO},
                 "issue":{"user":{"login":coding.OWNER},"number":1,
                          "title":coding.REPAIR_TITLE,
                          "body":f"{coding.LOCAL_REPAIR_MARKER}\nfile: {source}\nobjective: {task}"}}
        self.assertEqual(coding.parse_owner_repair_event(event)["task"],task)
        self.assertEqual(coding.local_edit_requests(task,original),[task])
        prefix, body, suffix = coding.local_function_scope(task,original)
        self.assertTrue(body.startswith(b"def _normalize("))
        self.assertEqual(prefix+body+suffix,original)
        self.assertNotIn(b"def _get_provider(",body)
        plan = coding.local_plan(task,source_file=source)
        self.assertEqual(plan["local_model"],coding.STRUCTURED_EDIT_MODEL)
        self.assertEqual(plan["authorized_function_edits"],1)
        self.assertFalse(plan["paid_api_authorized"])
        self.assertEqual(coding.STRUCTURED_RECOVERY_TASKS[(source,task)],
                         "federated_provider_doi_normalization.py")
        for name in ("_get_provider","__init__"):
            with self.assertRaises(ValueError):
                coding.local_edit_requests(f"Repair function {name}. Preserve behavior.",original)
