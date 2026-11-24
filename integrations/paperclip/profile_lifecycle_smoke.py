"""Offline regressions for UUID isolation and distinct work products."""
import copy
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4
from lifecycle import mission_dir, owner_company
from profile_execution import chief_receipt, division_receipts
from typed_scope_smoke import BUDGET
from mission_scope import PROFILE_DIVISIONS

class Tests(unittest.TestCase):
    def test_persistent_ids_and_isolation(self):
        c,a,b=map(str,(uuid4(),uuid4(),uuid4()))
        with tempfile.TemporaryDirectory() as t,patch.dict(os.environ,{"PLENUM_PERSISTENT_BOARD":"confirmed","PLENUM_PAPERCLIP_COMPANY_UUID":c}):
            p,q=mission_dir(t,c,a),mission_dir(t,c,b)
            p.mkdir(parents=True);q.mkdir()
            (p/"qualification.json").write_text("old")
            (q/"qualification.json").write_text("new")
            self.assertEqual((p/"qualification.json").read_text(),"old")
            self.assertEqual(owner_company(lambda _: [{"id":c}]),c)
            with self.assertRaises(ValueError):owner_company(lambda _: [])
            with self.assertRaises(ValueError):mission_dir(t,c,"../wrong")
    def test_profile_outputs(self):
        scope=copy.deepcopy(BUDGET)
        plan={"parent":str(uuid4()),"order":["intelligence","research","engineering","commercial","verification"],
              "tasks":{r:str(uuid4()) for r in ("intelligence","research","engineering","commercial","verification")}}
        chief=chief_receipt(scope,plan)
        self.assertEqual(len(chief["output"]["ordered_assignments"]),5)
        brief={"objective":"Budget review","recommendation":"Review current sources","limitations":["Synthetic inputs only"]}
        commercial=division_receipts("commercial",scope,{},brief,Path("."))
        self.assertEqual(set(commercial),{"operations","creative","marketing","support"})
        self.assertEqual(len({r["output_sha256"] for r in commercial.values()}),4)
        self.assertFalse(commercial["support"]["output"]["sent"])
        changed=division_receipts("commercial",scope,{},dict(brief,recommendation="Defer"),Path("."))
        self.assertNotEqual(changed["creative"]["output_sha256"],commercial["creative"]["output_sha256"])
        self.assertEqual(len(PROFILE_DIVISIONS),11)
if __name__=="__main__":unittest.main(verbosity=2)
