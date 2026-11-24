"""Model plan gate and restart reuse regression, no live network."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4
import model_plan as mp


class PlanTests(unittest.TestCase):
    def test_scope_and_order(self):
        good={"steps":[{"goal":k,"division":mp.ROLE_MAP[k]} for k in ("A","D","B","C","E")]}
        self.assertEqual(mp.validate_choice(good),mp.ORDER)
        for bad in ({"steps":good["steps"][::-1]}, {"steps":good["steps"][:-1]},
                    {"steps":[{**good["steps"][0],"division":"shell"},*good["steps"][1:]]}):
            with self.assertRaises(ValueError):mp.validate_choice(bad)

    def test_one_call_and_restart_reuse(self):
        good={"steps":[{"goal":k,"division":mp.ROLE_MAP[k]} for k in ("A","D","B","C","E")]}
        tag={"models":[{"name":mp.MODEL,"digest":mp.MODEL_DIGEST+"a"*52}]}
        reply={"model":mp.MODEL,"done":True,"message":{"content":json.dumps(good)},"eval_count":105,"prompt_eval_count":311}
        cid,pid=str(uuid4()),str(uuid4())
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ,{"PLENUM_EPHEMERAL_RUNNER":"confirmed","PLENUM_PAPERCLIP_MODEL":"local"}):
            with patch.object(mp,"read_json",side_effect=[tag,reply]) as model:
                first=mp.model_plan(Path(tmp),cid,pid)
                self.assertEqual(model.call_count,2) # tags + exactly one chat
                self.assertEqual(model.call_args_list[1].args[0],"/api/chat")
            with patch.object(mp,"read_json",side_effect=AssertionError("no repeated inference")):
                self.assertEqual(mp.model_plan(Path(tmp),cid,pid),first)
                with self.assertRaises(ValueError):mp.model_plan(Path(tmp),cid,str(uuid4()))
        print("MODEL RECEIPT REUSE PASS one simulated chat, zero replay",flush=True)

    def test_rejected_plan_no_fallback(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ,{"PLENUM_EPHEMERAL_RUNNER":"confirmed","PLENUM_PAPERCLIP_MODEL":"local"}):
            tag={"models":[{"name":mp.MODEL,"digest":mp.MODEL_DIGEST+"a"*52}]}
            reply={"model":mp.MODEL,"done":True,"message":{"content":"{}"},"eval_count":1,"prompt_eval_count":10}
            with patch.object(mp,"read_json",side_effect=[tag,reply]) as model:
                with self.assertRaises(ValueError):mp.model_plan(Path(tmp),"company","parent")
                with self.assertRaises(FileExistsError):mp.model_plan(Path(tmp),"company","parent")
                self.assertEqual(model.call_count,2)
            self.assertFalse((Path(tmp)/"minister-model-plan.json").exists())
        print("REJECTED MODEL PLAN FAILS CLOSED no fallback or second inference",flush=True)


if __name__=="__main__":
    unittest.main(verbosity=2)
