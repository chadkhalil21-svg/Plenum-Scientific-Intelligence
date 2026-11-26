import copy
import unittest
from unittest.mock import patch
from plenum_ai import accepted_engineering_promotion as p
from plenum_ai.engineering_event_controller import REPO, OWNER, REGISTERED

class PromotionTests(unittest.TestCase):
    def setUp(self):
        self.main = "a"*40
        self.head = "b"*40
        self.pr = {"number":p.PR,"state":"open","draft":False,"user":{"login":OWNER},
                   "head":{"ref":REGISTERED[p.PR][0],"sha":self.head,"repo":{"full_name":REPO}},
                   "base":{"ref":"main","sha":self.main,"repo":{"full_name":REPO}}}
        self.comp = {"merge_base_commit":{"sha":self.main},"files":[
            {"filename":name,"sha":sha,"status":"added"} for name,sha in p.FILES.items()]}
        self.runs = [{"id":i+1,"name":name,"head_sha":self.head,"event":"pull_request",
                      "status":"completed","conclusion":"success","head_repository":{"full_name":REPO}}
                     for i,name in enumerate(p.CHECKS)]
        self.evidence={"id":p.ACCEPTANCE_RUN,"head_sha":p.ACCEPTANCE_HEAD,"conclusion":"success",
                       "event":"issues","run_attempt":1,"repository":{"full_name":REPO}}
        self.artifacts=[{"id":p.ARTIFACT,"digest":p.DIGEST,"expired":False}]
        self.jobs=[{"name":name,"run_id":p.ACCEPTANCE_RUN,"conclusion":"success"} for name in
                   ("observe-and-recover","repair-whisper","verify-whisper-repair")]
    def check(self):
        return p.accepted(self.pr,self.main,self.comp,self.runs,self.evidence,self.artifacts,self.jobs)
    def test_exact_acceptance(self):
        self.assertTrue(self.check())
    def test_reject_draft_and_fork(self):
        self.pr["draft"]=True
        self.assertFalse(self.check())
        self.pr["draft"]=False
        self.pr["head"]["repo"]["full_name"]="other/repo"
        self.assertFalse(self.check())
    def test_reject_changed_or_extra_source(self):
        self.comp["files"][0]["sha"]="c"*40
        self.assertFalse(self.check())
    def test_reject_stale_base(self):
        self.comp["merge_base_commit"]["sha"]="c"*40
        self.assertFalse(self.check())
    def test_reject_newer_failure(self):
        row=copy.deepcopy(self.runs[0])
        row.update(id=99,conclusion="failure")
        self.runs.append(row)
        self.assertFalse(self.check())
    def test_reject_wrong_receipt(self):
        self.artifacts[0]["digest"]="sha256:invalid"
        self.assertFalse(self.check())
    def test_reject_missing_independent_verifier(self):
        self.jobs.pop()
        self.assertFalse(self.check())
    def test_no_merge_on_changed_snapshot(self):
        with patch.object(p,"snapshot",side_effect=[(self.head,self.main),None]), patch.object(p,"request") as req:
            with self.assertRaises(RuntimeError):
                p.promote()
            req.assert_not_called()
    def test_only_expected_head_merge(self):
        with patch.object(p,"snapshot",return_value=(self.head,self.main)), patch.object(p,"request",return_value={"merged":True,"sha":"c"*40}) as req:
            p.promote()
            req.assert_called_once_with("/pulls/928/merge","PUT",{"sha":self.head,"merge_method":"merge"})
