"""Structural-only check: cloud experiment notebook must not silently run paid workloads."""
import json
import unittest
from pathlib import Path

class FreeCloudNotebookTests(unittest.TestCase):
    def test_notebook_valid_python_and_explicit_opt_in(self):
        path = Path(__file__).resolve().parents[1] / "notebooks" / "prometheus_kaggle_qwen36_27b.ipynb"
        notebook = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(notebook["nbformat"], 4)
        code = ["".join(x["source"]) for x in notebook["cells"] if x["cell_type"] == "code"]
        self.assertEqual(len(code), 3)
        for i, cell in enumerate(code):
            compile(cell, str(path) + ":" + str(i), "exec")
        self.assertIn("APPROVE_FREE_GPU_RUN = False", code[1])
        self.assertIn("if APPROVE_FREE_GPU_RUN:", code[2])
        self.assertIn('"AGI_demonstrated": False', code[2])
        self.assertIn('LLAMA_CPP_TAG = "b12143"', code[1])
        self.assertIn('"paid_api_calls": 0', code[2])
        self.assertNotIn("OPENAI_API_KEY", "".join(code))
        self.assertNotIn("ANTHROPIC_API_KEY", "".join(code))

if __name__ == "__main__":
    unittest.main()
