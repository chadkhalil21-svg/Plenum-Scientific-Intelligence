"""Minimal no-model checks only for Plenum's new optional private memory boundary."""
import os
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from plenum_ai.optional_memory_engines import (
    MEMORY_MCP_NPM, mcp_memory_client_entry, private_storage_root, installed_versions,
)


class OptionalMemoryEnginesTests(TestCase):
    def test_no_unsolicited_public_memory(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(RuntimeError):
                private_storage_root()

    def test_public_ci_rejected(self):
        with patch.dict(os.environ, {
            "PLENUM_PRIVATE_MEMORY_DIR": "/opt/plenum/private-memory",
            "GITHUB_ACTIONS": "true",
        }, clear=True):
            with self.assertRaises(RuntimeError):
                private_storage_root()

    def test_owner_private_mcp_config(self):
        with patch.dict(os.environ, {
            "PLENUM_PRIVATE_MEMORY_DIR": "/opt/plenum/private-memory",
        }, clear=True):
            config = mcp_memory_client_entry()
        self.assertEqual(config["env"]["MEMORY_FILE_PATH"],
                         "/opt/plenum/private-memory/mcp-knowledge-graph.jsonl")
        self.assertIn(MEMORY_MCP_NPM, config["args"])
        self.assertTrue(Path(config["env"]["MEMORY_FILE_PATH"]).is_absolute())

    def test_no_installed_package_claim_without_metadata(self):
        statuses = installed_versions()
        self.assertIn("mem0", statuses)
        self.assertIn("graphiti", statuses)
