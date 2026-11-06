"""Parametric CAD geometry-contract tests, with no installed CAD engine needed."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from plenum_ai.cad_studio import validate_panel,parametric_panel,create_design

class CADTests(unittest.TestCase):
    def test_original_scad_is_parameterized(self):
        content=parametric_panel(180,110,6,5)
        self.assertIn("cube([width, height, thickness]",content)
        self.assertEqual(content.count("cylinder(d="),8)
        self.assertIn("width = 180.0000",content)
        self.assertNotIn("import(",content)

    def test_geometry_invalid_dimensions_rejected(self):
        for values in ((40,100,6,5),(180,40,6,5),(180,110,0,5),
                       (180,110,6,30), (True,110,6,5)):
            with self.subTest(values=values):
                with self.assertRaises(ValueError):
                    validate_panel(*values)

    def test_files_are_editable_and_unverified_until_mesh_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            result=create_design(tmp,180,110,6,5,render=False)
            self.assertTrue(Path(result["source_scad"]).is_file())
            self.assertIsNone(result["stl_mesh"])
            self.assertFalse(result["mesh_export_verified"])
            self.assertFalse(result["structural_strength_or_safety_validated"])
            self.assertTrue(result["human_review_required_before_manufacture"])

    def test_render_calls_only_approved_exporter(self):
        with tempfile.TemporaryDirectory() as tmp:
            def fake_export(args,**kwargs):
                self.assertEqual(args[0],"openscad")
                self.assertEqual(args[1],"-o")
                Path(args[2]).write_bytes(b"x"*2000)
            with patch("plenum_ai.cad_studio.subprocess.run",
                       side_effect=fake_export) as run:
                result=create_design(tmp,render=True)
            self.assertTrue(run.called)
            self.assertTrue(result["mesh_export_verified"])
            self.assertFalse(result["professional_engineering_approval"])

if __name__=="__main__":
    unittest.main()
