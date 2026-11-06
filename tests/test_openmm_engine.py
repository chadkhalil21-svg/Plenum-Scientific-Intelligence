"""OpenMM integration checks; unit-only tests run without extra dependencies."""
import unittest
from plenum_ai.openmm_engine import harmonic_energy, reference_diatomic

class MolecularDynamicsTests(unittest.TestCase):
    def test_analytic_bond_energy(self):
        self.assertAlmostEqual(harmonic_energy(1000.0,0.4,0.35),1.25,places=9)
        self.assertEqual(harmonic_energy(1000,0.35,0.35),0)

    def test_invalid_parameters_refused(self):
        for params in [(0,0.4,0.35),(-2,0.4,0.35),
                       (1000,float("nan"),0.35),(1000,0.4,0)]:
            with self.assertRaises(ValueError):
                harmonic_energy(*params)

    def test_bounded_steps(self):
        for step in (0,251,-1,1.5):
            with self.assertRaises(ValueError):
                reference_diatomic(step)

if __name__=="__main__":
    unittest.main()
