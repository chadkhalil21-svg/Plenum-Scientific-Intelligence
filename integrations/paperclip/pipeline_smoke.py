"""New pipeline exact computation, plan commitment and tamper regressions."""
import copy,json,unittest
from pipeline_fixtures import KINDS,scope
from objective_mission import independent,planning_kwargs
from objective_program import analyze,TOOLS
from model_plan import classification_request,validate_operations,semantic_evidence
from sequential_mission import goal_texts
from mission_scope import validate_scope,profile_routes

EXPECTED={"scientific":{"relative_reduction":{"numerator":3,"denominator":10}},
          "engineering":{"reserve_fraction":{"numerator":1,"denominator":5}},
          "commercial":{"break_even_units":{"numerator":80,"denominator":1},"operating_profit":{"numerator":900,"denominator":1}}}
class Tests(unittest.TestCase):
    def test_all_domains(self):
        for kind in KINDS:
            s=scope(kind);self.assertEqual(validate_scope(s),s)
            self.assertEqual(len(profile_routes(s)),11)
            policy=planning_kwargs(s)["operation_policy"];group=policy["required_groups"][0]
            chosen={k:k in EXPECTED[kind] for k in group}
            operations=validate_operations(chosen,policy)
            request=classification_request(goal_texts(s),group)
            self.assertNotIn(s["operation_commitment"],json.dumps(request))
            self.assertTrue(all(semantic_evidence(s["objective"],group)[k] for k in operations))
            data={**s["inputs"],"operations":operations};expected=independent(data)
            self.assertEqual(expected["results"],EXPECTED[kind]);self.assertGreaterEqual(len(expected["pipeline"]["steps"]),3)
            for tool in TOOLS:self.assertEqual(analyze(data,tool),expected)
            bad=copy.deepcopy(s);bad["inputs"]["url"]="https://example.org"
            with self.assertRaises(ValueError):validate_scope(bad)
            with self.assertRaises(ValueError):validate_operations({k:False for k in group},policy)
            print(kind,expected,flush=True)
if __name__=="__main__":unittest.main(verbosity=2)
