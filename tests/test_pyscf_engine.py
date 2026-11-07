import importlib.util
import unittest
from plenum_ai.pyscf_engine import run_h2_reference


class PySCFEngineTests(unittest.TestCase):
    @unittest.skipUnless(importlib.util.find_spec("pyscf") is not None,
                         "Optional upstream PySCF installed only in isolated chemistry job")
    def test_real_pyscf_h2_reference_and_stretch_control(self):
        r=run_h2_reference()
        self.assertEqual(r["engine_version"],"2.15.0")
        self.assertLess(r["absolute_numerical_error_hartree"],1e-4)
        self.assertGreater(r["total_energies_hartree"][1],r["total_energies_hartree"][0])
        self.assertFalse(r["real_experimental_chemistry_verified"])
        self.assertFalse(r["AGI_demonstrated"])


if __name__=="__main__":
    unittest.main()
