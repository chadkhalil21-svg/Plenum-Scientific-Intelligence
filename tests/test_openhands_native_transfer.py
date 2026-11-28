"""Native OpenHands context contract for one quarantined public skill."""
import importlib.util
import unittest
from unittest.mock import patch
from plenum_ai import openhands_coding_agent as agent

SDK_AVAILABLE = importlib.util.find_spec("openhands") is not None

class NativeTransferTests(unittest.TestCase):
    def test_unrelated_task_does_not_load_sdk_or_skill(self):
        self.assertEqual(agent.native_learned_context("Other public objective", None, "irrelevant"), (None, {}))

    def test_trial_cannot_use_different_source_or_changed_source(self):
        with self.assertRaises(PermissionError):
            agent.native_learned_context(agent.NATIVE_TRANSFER_TASK, "src/plenum_ai/world_horizon.py", "irrelevant")
        with patch.object(agent, "_public_source", return_value=(b"", "changed")):
            with self.assertRaises(PermissionError):
                agent.native_learned_context(agent.NATIVE_TRANSFER_TASK, agent.NATIVE_TRANSFER_SOURCE, "irrelevant")

    def test_current_repaired_source_cannot_reauthorize_historical_trial(self):
        _, current = agent._public_source(agent.NATIVE_TRANSFER_SOURCE)
        self.assertNotEqual(current, agent.NATIVE_TRANSFER_SOURCE_SHA)
        with self.assertRaises(PermissionError):
            agent.native_learned_context(agent.NATIVE_TRANSFER_TASK,
                agent.NATIVE_TRANSFER_SOURCE, "openai/glm-4.7-flash")

    @unittest.skipUnless(SDK_AVAILABLE, "Optional pinned OpenHands SDK")
    def test_native_sdk_renders_exact_quarantined_skill(self):
        # Rendering is a historical, offline SDK contract, not authorization
        # to run the old objective against the subsequently repaired source.
        with patch.object(agent, "_public_source", return_value=(b"", agent.NATIVE_TRANSFER_SOURCE_SHA)):
            context, receipt = agent.native_learned_context(agent.NATIVE_TRANSFER_TASK,
                agent.NATIVE_TRANSFER_SOURCE, "openai/glm-4.7-flash")
        from openhands.sdk import AgentContext
        self.assertIsInstance(context, AgentContext)
        self.assertEqual(len(context.skills), 1)
        self.assertFalse(context.skills[0].is_agentskills_format)
        self.assertIsNone(context.skills[0].trigger)
        self.assertFalse(context.skills[0].mcp_tools)
        self.assertFalse(context.load_user_skills or context.load_public_skills or
                         context.load_project_skills or context.load_memory)
        self.assertFalse(context.secrets)
        rendered = context.get_system_message_suffix(llm_model="openai/glm-4.7-flash")
        self.assertIn("Reject any unexpected final URL", rendered)
        self.assertIn("historical 1287 test count is not current", rendered)
        self.assertEqual(receipt["native_transfer_skill_sha256"], agent.NATIVE_TRANSFER_SKILL_SHA)
        self.assertTrue(receipt["native_transfer_context_rendered"])
        self.assertFalse(receipt["native_transfer_verified"])
        self.assertFalse(receipt["native_transfer_production_admitted"])

    def test_global_trial_is_exact_and_does_not_change_historical_scope(self):
        self.assertEqual(agent.TASK_ACCEPTANCE[(agent.GLOBAL_TRANSFER_SOURCE, agent.GLOBAL_TRANSFER_TASK)],
                         "global_literature_boundary_transfer.py")
        with self.assertRaises(PermissionError):
            agent.native_learned_context(agent.GLOBAL_TRANSFER_TASK, agent.NATIVE_TRANSFER_SOURCE, "irrelevant")
        with patch.object(agent, "_public_source", return_value=(b"changed", "changed")):
            with self.assertRaises(PermissionError):
                agent.native_learned_context(agent.GLOBAL_TRANSFER_TASK, agent.GLOBAL_TRANSFER_SOURCE, "irrelevant")

    @unittest.skipUnless(SDK_AVAILABLE, "Optional pinned OpenHands SDK")
    def test_global_trial_native_context_for_existing_gemini_fallback(self):
        from hashlib import sha1
        raw, source_sha = agent._public_source(agent.GLOBAL_TRANSFER_SOURCE)
        # Keep this historical rendering contract testable after a later source repair.
        with patch.object(agent, "GLOBAL_TRANSFER_SOURCE_BLOB",
                          sha1(("blob %d" % len(raw)).encode() + b"\0" + raw).hexdigest()):
            context, receipt = agent.native_learned_context(agent.GLOBAL_TRANSFER_TASK,
                agent.GLOBAL_TRANSFER_SOURCE, agent.GEMINI_MODEL)
        self.assertEqual(len(context.skills), 1)
        self.assertEqual(receipt["native_transfer_objective"], agent.GLOBAL_TRANSFER_TASK)
        self.assertEqual(receipt["native_transfer_source_sha256"], source_sha)
        self.assertFalse(receipt["native_transfer_production_admitted"])
        self.assertIn("Reject any unexpected final URL",
                      context.get_system_message_suffix(llm_model=agent.GEMINI_MODEL))

if __name__ == "__main__":
    unittest.main()
