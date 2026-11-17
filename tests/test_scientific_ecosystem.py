"""The complete screenshot resource inventory is discoverable without execution."""
import unittest
from plenum_ai.tool_registry import TOOLS, PARALLEL_TOOLS, approve_request, get_registry

class ScreenshotResourceTests(unittest.TestCase):
    def test_every_pictured_science_engine_has_an_explicit_entry(self):
        names = (
            "lean4.proofs", "diffdock.docking", "openmm.dynamics",
            "pyscf.chemistry", "pymatgen.materials", "su2.cfd",
            "pybamm.battery", "nasa.exoplanets", "tooluniverse.biomed",
            "nasa.gmat", "nasa.aviary", "openmdao.cooling",
            "kdense.skills", "biomni.biomed", "karpathy.autoresearch",
            "sakana.scientist", "materialsproject.api",
            "arxiv.metadata", "osti.metadata", "federated.metadata",
        )
        for name in names:
            with self.subTest(name=name):
                self.assertIn(name, TOOLS)
                self.assertTrue(TOOLS[name].origin.startswith("https://"))

    def test_planned_or_credential_gated_tools_not_executable(self):
        blocked = (
            "lean4.proofs","diffdock.docking","openmm.dynamics",
            "pyscf.chemistry","pymatgen.materials","su2.cfd",
            "tooluniverse.biomed","materialsproject.api",
            "karpathy.autoresearch","sakana.scientist","biomni.biomed",
        )
        for name in blocked:
            self.assertNotIn(name, PARALLEL_TOOLS)
            with self.assertRaises(ValueError):
                approve_request([name])
        report = get_registry()
        self.assertFalse(report["all_external_execution_approved"])
        self.assertLessEqual(report["parallel_limit_per_batch"],5)

    def test_requested_scientist_tools_cannot_enter_parallel_worker_gate(self):
        keys = ("sakana.scientist", "sakana.scientist_v3", "harvard.autoscientists",
                "futurehouse.robin", "mit.scienceclaw", "fermilink.scientist",
                "denario.scientist", "evoscientist.scientist")
        for key in keys:
            with self.subTest(key=key):
                self.assertIn(key, TOOLS)
                self.assertNotIn(key, PARALLEL_TOOLS)
                with self.assertRaises(ValueError):
                    approve_request([key])

if __name__=="__main__":
    unittest.main()
