"""Independent regression cases for the original bounded Blender geometry validator."""
import itertools
import unittest

from plenum_ai.blender_concept_render import vector


class BlenderVectorRegression(unittest.TestCase):
    def test_rejects_invalid_values_in_every_coordinate(self):
        for lo, hi in ((-3, 3), (0.08, 2), (0, 1)):
            invalid = (10**1000, -10**1000, float("nan"), float("inf"),
                       -float("inf"), True, False, None, "1", lo - 1, hi + 1)
            for index, value in itertools.product(range(3), invalid):
                coordinates = [lo] * 3
                coordinates[index] = value
                with self.subTest(bounds=(lo, hi), index=index, value_type=type(value)):
                    with self.assertRaises(ValueError):
                        vector(coordinates, lo, hi)

    def test_accepts_boundary_and_mixed_numeric_tuples(self):
        for lo, hi in ((-3, 3), (0.08, 2), (0, 1)):
            self.assertEqual(vector([lo, hi, lo], lo, hi), (lo, hi, lo))
        self.assertEqual(vector([0, 1.5, -2], -3, 3), (0, 1.5, -2))

    def test_rejects_wrong_shape(self):
        for invalid in (None, (), [0], [0, 0, 0, 0], (0, 0, 0)):
            with self.assertRaises(ValueError):
                vector(invalid, -3, 3)


if __name__ == "__main__":
    unittest.main()
