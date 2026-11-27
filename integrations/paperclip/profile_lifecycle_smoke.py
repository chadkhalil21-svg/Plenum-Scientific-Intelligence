"""Offline regressions for UUID isolation and distinct work products."""
import copy
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4
from lifecycle import mission_dir, owner_company, persistent_adapter, validate_roster, bind_roster
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
    def test_roster_continuity_and_redaction(self):
        from division_adapter import SPECS
        c=str(uuid4())
        names={"minister":"Minister of Operations",**{k:v[0] for k,v in SPECS.items()}}
        ids={k:str(uuid4()) for k in names}
        rows=[{"id":ids[k],"name":name,"companyId":c,"adapterType":"process",
               "reportsTo":None if k=="minister" else ids["minister"],
               "adapterConfig":persistent_adapter(k),"budgetMonthlyCents":0,
               "runtimeConfig":{"heartbeat":{"enabled":False,"wakeOnAssignment":True,"maxConcurrentRuns":1}},
               "permissions":{"canCreateAgents":False,"canCreateSkills":False}} for k,name in names.items()]
        with tempfile.TemporaryDirectory() as tmp:
            # First seed and second readback from the same store; no env comparison.
            self.assertEqual(validate_roster(rows,c,SPECS),ids)
            self.assertEqual(validate_roster(rows,c,SPECS,require_extended_minister=True),ids)
            legacy=copy.deepcopy(rows);legacy[0]["adapterConfig"]["timeoutSec"]=150
            self.assertEqual(validate_roster(legacy,c,SPECS),ids)
            with self.assertRaises(ValueError):validate_roster(legacy,c,SPECS,require_extended_minister=True)
            first=bind_roster(tmp,c,ids)
            second=json_roundtrip(rows)
            self.assertEqual(bind_roster(tmp,c,validate_roster(second,c,SPECS)),first)
            # Pinned upstream redacts old plain env values into these objects.
            for change in (
                lambda r:r["adapterConfig"]["env"].update({"PLENUM_PERSISTENT_BOARD":{"type":"plain","value":"***REDACTED***"}}),
                lambda r:r["adapterConfig"].update({"args":["/plenum/integrations/paperclip/sequential_mission.py","minister"]}),
                lambda r:r["adapterConfig"].update({"command":"sh"}),
                lambda r:r.update({"budgetMonthlyCents":1}),
                lambda r:r["runtimeConfig"]["heartbeat"].update({"maxConcurrentRuns":2}),
                lambda r:r["permissions"].update({"canCreateAgents":True})):
                bad=copy.deepcopy(rows);change(bad[0])
                with self.assertRaises(ValueError):validate_roster(bad,c,SPECS)
            changed=copy.deepcopy(rows);changed[1]["id"]=str(uuid4())
            with self.assertRaises(ValueError):bind_roster(tmp,c,validate_roster(changed,c,SPECS))
        print("PERSISTENT ROSTER CONTINUITY PASS; redacted/changed adapters and substituted identity denied",flush=True)

def json_roundtrip(value):
    import json
    return json.loads(json.dumps(value))

if __name__=="__main__":unittest.main(verbosity=2)
