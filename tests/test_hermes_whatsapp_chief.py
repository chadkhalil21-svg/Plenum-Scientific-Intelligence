"""One new integration: official Hermes profile routes for all existing Plenum specialists."""
import importlib.util
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / "integrations" / "hermes" / "prepare_whatsapp_chief.py"
spec = importlib.util.spec_from_file_location("plenum_whatsapp_chief", MOD)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class WhatsAppChiefRoutingContract(unittest.TestCase):
    def test_exact_original_nine_roles_and_chief_as_only_supervisor(self):
        roles = mod.read_roles()
        self.assertEqual(len(roles), 10)
        self.assertEqual(set(roles), mod.EXPECTED)
        yaml = mod.render_chief_routes(roles)
        self.assertIn("backend: profile_routes", yaml)
        self.assertIn("max_concurrent_children: 2", yaml)
        self.assertIn("max_spawn_depth: 1", yaml)
        self.assertIn("orchestrator_enabled: false", yaml)
        self.assertEqual(yaml.count("- name: "), 9)
        self.assertNotIn("- name: chief", yaml)
        for role in mod.EXPECTED - {"chief"}:
            self.assertIn("- name: " + role + "\n", yaml)
        self.assertNotIn("secret_key:", yaml)
        self.assertNotIn("WHATSAPP_ENABLED=true", yaml)
        self.assertNotIn("group_policy: open", yaml)
        self.assertNotIn("auto_start_gateway: true", yaml)

    def test_roster_drift_refused_instead_of_adding_agents(self):
        roles = mod.read_roles()
        roles.pop("support")
        with self.assertRaises(ValueError):
            mod.render_chief_routes(roles)
        with tempfile.TemporaryDirectory() as tmp:
            original = json.loads(mod.ROSTER.read_text())
            original["roles"].append(dict(original["roles"][2]))
            target = Path(tmp) / "roster.json"
            target.write_text(json.dumps(original))
            with self.assertRaises(ValueError):
                mod.read_roles(target)
            original["roles"].pop()
            original["defaults"]["private_app_access"] = True
            target.write_text(json.dumps(original))
            with self.assertRaises(PermissionError):
                mod.read_roles(target)

    def test_safe_private_snippet_does_not_overwrite_config(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "chief-routing.yaml"
            mod.safe_write(path, mod.render_chief_routes())
            self.assertEqual(path.read_text().count("- name: "), 9)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            with self.assertRaises(FileExistsError):
                mod.safe_write(path, "bad overwrite")
            self.assertIn("backend: profile_routes", path.read_text())
            missing = Path(root) / "missing" / "x.yaml"
            with self.assertRaises(ValueError):
                mod.safe_write(missing, "untrusted")
            symlink = Path(root) / "linked.yaml"
            symlink.symlink_to(path)
            with self.assertRaises(FileExistsError):
                mod.safe_write(symlink, "bad")

    def test_offline_tool_never_attempts_platform_or_external_calls(self):
        text = MOD.read_text()
        self.assertNotIn("requests.post(", text)
        self.assertNotIn("subprocess.run(", text)
        self.assertNotIn("WHATSAPP_CLOUD_ACCESS_TOKEN=", text)
        self.assertNotIn("PLENUM_GITHUB_PUBLIC_ISSUES_TOKEN=", text)
        self.assertNotIn("gcloud run deploy", text)


if __name__ == "__main__":
    unittest.main()
