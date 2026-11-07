"""Kaggle free cloud notebook runtime-compatibility and approval guard."""
import json
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class KaggleTest(unittest.TestCase):
    def test_scratch_paths_and_manual_gate(self):
        p=ROOT/"notebooks/prometheus_kaggle_qwen36_27b.ipynb"
        j=json.loads(p.read_text())
        cs=["".join(c.get("source",[])) for c in j["cells"] if c["cell_type"]=="code"]
        code="\n".join(cs)
        self.assertIn("APPROVE_FREE_GPU_RUN = False",code)
        self.assertIn("if APPROVE_FREE_GPU_RUN:",code)
        self.assertIn("scratch = [(p, shutil.disk_usage(p).free) for p in candidates if p.is_dir()]",code)
        self.assertIn('Path("/kaggle/working")',code)
        self.assertIn('Path("/tmp")',code)
        self.assertIn("if temp is None:",code)
        self.assertIn("psutil.virtual_memory().available",code)
        for cell in cs: compile(cell,str(p),"exec")
if __name__=="__main__": unittest.main()
