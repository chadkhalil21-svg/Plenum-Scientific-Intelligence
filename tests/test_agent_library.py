"""PINNED repo tree and dormant persona fetch contract."""
import hashlib
from unittest import TestCase

from plenum_ai.agent_library import load_index, fetch_role, PREFIX, load_sources, suggest_sources


class AgentCatalogContract(TestCase):
    def test_current_agent_library_count_and_immutable_upstream(self):
        idx=load_index()
        self.assertEqual(len(idx["profiles"]),283)
        self.assertEqual(len({x["division"] for x in idx["profiles"]}),18)
        self.assertTrue(all(x["status"]=="catalogued_idle" for x in idx["profiles"]))
        self.assertEqual(idx["source"]["license"],"MIT")
        self.assertEqual(idx["run_state"],"none_installed_or_running_by_this_index")

    def test_openmontage_skills_are_separate_from_agent_roles(self):
        from pathlib import Path
        import json
        repo=Path(__file__).resolve().parents[1]
        index=json.loads((repo/"integrations/agent-catalog/openmontage.index.json").read_text())
        self.assertEqual(index["count"],1106)
        self.assertEqual(len(index["files"]),1106)
        self.assertEqual(index["skill_entrypoints"],141)
        self.assertEqual(index["source"]["license"],"AGPL-3.0")
        self.assertEqual(len(index["source"]["commit"]),40)
        self.assertTrue(all(x["status"]=="catalogued_uninstalled" for x in index["files"]))


    def test_full_free_upstream_catalogue_is_indexed_not_installed(self):
        entries=load_sources()["entries"]
        self.assertGreaterEqual(len(entries),27)
        self.assertEqual(len({e["repository"] for e in entries}),len(entries))
        ids={e["id"] for e in entries}
        for expected in (
            "agency-agents","agency-agents-app","browser-use","openmontage",
            "agentmemory","graft","elephant-goldfish-model","qwen-agentworld",
            "kilocode","openhands-sdk","langgraph","ollama","llama-cpp",
            "freecad","su2","openmdao","openmm","pybamm","rdkit","kicad",
            "monai","blender","ffmpeg"
        ):
            self.assertIn(expected,ids)
        self.assertTrue(all(e["default_execution"]=="never_install_automatically"
                            for e in entries))

    def test_deterministic_read_only_domain_selection(self):
        for query,expected in (
            ("aerodynamics cfd","su2"),
            ("battery electrochemistry","pybamm"),
            ("medical imaging","monai"),
            ("mechanical cad","freecad"),
            ("memory retrieval","agentmemory"),
        ):
            with self.subTest(query=query):
                selections=suggest_sources(query,limit=10)
                self.assertIn(expected,[x["id"] for x in selections])
                self.assertTrue(all(x["model_calls"]==0 and
                                    x["activation"]=="SOURCE_REFERENCE_ONLY_NOT_INSTALLED" and
                                    not x["additional_paid_services_enabled"]
                                    for x in selections))
        self.assertEqual(suggest_sources("unmatched gibberish kangaroo"),[])
        with self.assertRaises(ValueError):
            suggest_sources("x"*181)
        with self.assertRaises(ValueError):
            suggest_sources("bounded public task",limit=500)

    def test_untrusted_source_and_auto_execution_are_rejected(self):
        import copy
        import json
        from pathlib import Path
        import tempfile
        original=load_sources()
        for changed in (
            {"repository":"../../arbitrary/path"},
            {"default_execution":"auto_install_and_execute"},
            {"license":123},
            {"tags":["wrong//path"]},
        ):
            d=copy.deepcopy(original)
            d["entries"][0].update(changed)
            with tempfile.TemporaryDirectory() as folder:
                p=Path(folder)/"sources.json"
                p.write_text(json.dumps(d))
                with self.assertRaises(PermissionError):
                    load_sources(p)

    def test_blob_verified_before_any_persona_used(self):
        idx=load_index()
        path=idx["profiles"][0]["path"]
        content=b"---\nname: isolated-reviewer\n---\nPublic review only."
        expected=hashlib.sha1(
            b"blob "+str(len(content)).encode()+b"\0"+content
        ).hexdigest()
        idx["profiles"][0]["blob_sha"]=expected
        calls=[]
        def trusted_transport(url):
            calls.append(url)
            return content
        output=fetch_role(path,index=idx,transport=trusted_transport)
        self.assertIn("Public review only",output)
        self.assertEqual(calls,[PREFIX+idx["source"]["commit"]+"/"+path])
        with self.assertRaises(PermissionError):
            fetch_role(path,index=idx,transport=lambda url:b"tampered prompt")
        with self.assertRaises(PermissionError):
            fetch_role("../../secret",index=idx,transport=trusted_transport)

    def test_reject_extra_unregistered_role_and_limit_text(self):
        idx=load_index()
        with self.assertRaises(PermissionError):
            fetch_role("fake/division.md",index=idx,transport=lambda u:b"text")
        with self.assertRaises(ValueError):
            fetch_role(idx["profiles"][0]["path"],index=idx,
                       transport=lambda u:b"x"*120001)
