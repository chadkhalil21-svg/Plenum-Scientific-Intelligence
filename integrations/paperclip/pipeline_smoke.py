"""Offline regression of composable dependency and memory boundaries."""
import unittest,tempfile
from pathlib import Path
from copy import deepcopy
from pipeline_memory import build_scope
from pipeline_contract import independent,digest,EXPORTS,validate_memory
from pipeline_program import analyze
from model_plan import validate_operations,classification_request
from objective_mission import planning_kwargs,goals,simulation_input
from mission_scope import digest as scope_digest

RUN="12345";COMMIT="a"*40
def memory(scope,result):
    p=scope["inputs"]["pipeline"];return {"schema":"plenum-public-pipeline-memory-v1","stage":p["stage"],"run_id":RUN,"commit":COMMIT,
        "scope_sha256":scope_digest(scope),"qualification_sha256":"b"*64,"previous_sha256":digest(p["prior"]) if p["prior"] else None,
        "outcomes":result["results"],"fresh_runner_independent_acceptance":True,"verified_divisions":5,"verified_profile_work_products":11,
        "provider_calls_replayed":0,"model_calls_replayed":0,"paid_inference":False}

class Tests(unittest.TestCase):
    def test_three_domain_dependencies_and_memory(self):
        prior=None
        for stage,expected in (("science",{"paired_removed_mass":300,"removal_efficiency":0.75,"worst_pair_efficiency":0.7}),
                               ("engineering",{"effective_capacity":280,"module_count":4,"energy_requirement":2400}),
                               ("commercial",{"daily_operating_cost":660,"daily_margin":1840,"payback_days":109})):
            scope=build_scope(stage,prior,RUN,COMMIT)
            policy=planning_kwargs(scope)["operation_policy"]
            chosen=validate_operations({op:op in EXPORTS[stage] for op in policy["allowed"]},policy)
            request=classification_request(goals(scope),policy["required_groups"][0])
            self.assertNotIn(scope["operation_commitment"],str(request))
            data={**scope["inputs"],"operations":chosen}
            result=analyze(data,"collections")
            self.assertEqual(result,independent(data))
            self.assertEqual({k:v["numerator"]/v["denominator"] for k,v in result["results"].items()},expected)
            self.assertEqual(analyze(simulation_input(data),"collections"),independent(simulation_input(data)))
            prior=memory(scope,result)
            validate_memory(prior,stage)
        self.assertEqual(prior["outcomes"]["payback_days"],{"numerator":109,"denominator":1})

    def test_fail_closed(self):
        scope=build_scope("science",None,RUN,COMMIT)
        data={**scope["inputs"],"operations":["removal_efficiency"]}
        for fn in (lambda:analyze(data,"collections"),lambda:independent(data)):
            with self.assertRaises(ValueError):fn()
        policy=planning_kwargs(scope)["operation_policy"]
        with self.assertRaises(ValueError):validate_operations({op:op=="removal_efficiency" for op in policy["allowed"]},policy)
        result=analyze({**scope["inputs"],"operations":sorted(EXPORTS["science"])},"collections")
        prior=memory(scope,result)
        for change in ({"run_id":"67890"},{"commit":"c"*40},{"provider_calls_replayed":1},{"paid_inference":True},{"verified_divisions":4},{"outcomes":{}}):
            with self.assertRaises(ValueError):build_scope("engineering",{**prior,**change},RUN,COMMIT)
        with self.assertRaises(ValueError):build_scope("commercial",prior,RUN,COMMIT)
        with self.assertRaises(ValueError):build_scope("science",prior,RUN,COMMIT)

if __name__=="__main__":unittest.main(verbosity=2)
