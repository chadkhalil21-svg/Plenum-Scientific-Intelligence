import copy,json,tempfile,unittest
from pathlib import Path
from uuid import uuid4
from unittest.mock import Mock
import model_plan as mp
from model_plan_smoke import valid_plan
from mission_scope import validate_scope
from objective_mission import independent,goals,inputs,evaluate,SOURCE,TOOLS
from objective_replan import failure_chain,validate_replan
from checkpoint_store import execute_once,SpecialistExhausted,DomainBlocked

SCOPE={"kind":"public_objective","objective":"Compare delivery briefs and synthetic sample spread","dois":["10.1145/3442188.3445922"],"inputs":{"documents":["red red green","green blue"],"samples":[-3,2,9,12]},"operations":["shared_terms","term_frequency","mean","median","range"]}
class Tests(unittest.TestCase):
    def test_composable_objective_and_three_tools(self):
        self.assertEqual(validate_scope(SCOPE),SCOPE)
        expected=independent(inputs(SCOPE))
        for tool in TOOLS:self.assertEqual(evaluate(SOURCE,inputs(SCOPE),tool),expected)
        self.assertEqual(expected["results"]["shared_terms"],["green"])
        for bad in (dict(SCOPE,operations=["shell"]),dict(SCOPE,inputs={"documents":["x","y"]}),dict(SCOPE,url="https://example.org")):
            with self.assertRaises(ValueError):validate_scope(bad)
    def test_route_tool_scope(self):
        choice=valid_plan();choice["step_3"]["tool"]="sqlite"
        self.assertEqual(mp.validate_choice(choice,TOOLS),mp.ORDER)
        with self.assertRaises(ValueError):mp.validate_choice(choice)
        choice["step_3"]["tool"]="shell"
        with self.assertRaises(ValueError):mp.validate_choice(choice,TOOLS)
    def test_exhausted_or_domain_blocker_only(self):
        c,i=str(uuid4()),str(uuid4())
        for error,count in ((TimeoutError("transient"),2),(DomainBlocked("unavailable"),1),(PermissionError("security"),0),(ValueError("integrity"),0)):
            with tempfile.TemporaryDirectory() as tmp:
                d=Path(tmp);producer=Mock(side_effect=error)
                with self.assertRaises(RuntimeError):execute_once(d,c,"engineering",i,producer)
                if count:self.assertEqual(len(failure_chain(d,c,i)["failure_sha256"]),count)
                else:
                    with self.assertRaises(ValueError):failure_chain(d,c,i)
    def test_replan_goal_and_failure_binding(self):
        ctx={"goals_sha256":mp.digest(goals(SCOPE)),"alternatives":["collections","stream"],"failure_sha256":["a"*64,"b"*64]}
        choice={"tool":"collections"}
        row={"context":ctx,"replan_issue":str(uuid4()),"model":mp.MODEL,"model_digest":mp.MODEL_DIGEST+"a"*52,"choice":choice,"choice_sha256":mp.digest(choice),"eval_count":12,"prompt_eval_count":200,"elapsed_seconds":1.5,"paid_inference":False}
        self.assertEqual(validate_replan(row,ctx,goals=goals(SCOPE)),row)
        for changed in (dict(row,paid_inference=True),dict(row,choice={"tool":"sqlite"}),dict(row,context={**ctx,"failure_sha256":[]})):
            with self.assertRaises(ValueError):validate_replan(changed,ctx,goals=goals(SCOPE))
        with self.assertRaises(ValueError):validate_replan(row,ctx,goals=dict(goals(SCOPE),B="different goal"))
if __name__=="__main__":unittest.main(verbosity=2)
