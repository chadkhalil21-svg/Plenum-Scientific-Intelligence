"""Cross-run source, scope, digest and independent result regressions."""
import copy,hashlib,tempfile,unittest
from pathlib import Path
from checkpoint_store import encoded
from pipeline_contract import independent,EXPORTS
from pipeline_program import analyze
import cross_run_memory as c

PRIOR={"commit":"16738e2e366e9078701a1209adbc73209684231d","fresh_runner_independent_acceptance":True,"model_calls_replayed":0,"outcomes":{"effective_capacity":{"denominator":1,"numerator":280},"energy_requirement":{"denominator":1,"numerator":2400},"module_count":{"denominator":1,"numerator":4}},"paid_inference":False,"previous_sha256":"91fc58c99ba9ae26cc48a415511b0284ff5c34b33cda7c2da1ed55947ff82d44","provider_calls_replayed":0,"qualification_sha256":"12d3930fc9ba5765d014ba3ffabe6477addbde3b56581f77ce1ed676be5c5698","run_id":"45549381583","schema":"plenum-public-pipeline-memory-v1","scope_sha256":"ede95bea78c423830960d88b2982d6861932d0f25f84f3330a0d5b57df72cc4a","stage":"engineering","verified_divisions":5,"verified_profile_work_products":11}
RUN={"id":int(c.SOURCE_RUN),"status":"completed","conclusion":"success","event":"pull_request","head_sha":c.SOURCE_HEAD,"path":".github/workflows/paperclip-multidisciplinary.yml","repository":{"full_name":c.REPO}}
ART={"id":c.SOURCE_ARTIFACT,"name":"paperclip-pipeline-memory-engineering","expired":False,"digest":"sha256:"+c.SOURCE_ZIP,"workflow_run":{"id":int(c.SOURCE_RUN)}}
class Tests(unittest.TestCase):
    def test_source_identity(self):
        c.validate_source(RUN,ART)
        for bad in (dict(RUN,conclusion="failure"),dict(RUN,head_sha="b"*40),dict(RUN,id=123),dict(RUN,repository={"full_name":"other/repo"})):
            with self.assertRaises(ValueError):c.validate_source(bad,ART)
        for bad in (dict(ART,expired=True),dict(ART,digest="sha256:"+"b"*64),dict(ART,id=123),dict(ART,workflow_run={"id":123})):
            with self.assertRaises(ValueError):c.validate_source(RUN,bad)
    def test_actual_prior_and_new_cases(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"memory.json";p.write_bytes(encoded(PRIOR))
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),c.SOURCE_MEMORY)
            for case,expected in (("pr",{"daily_operating_cost":820,"daily_margin":1980,"payback_days":112}),("live",{"daily_operating_cost":944,"daily_margin":2256,"payback_days":107})):
                scope=c.prepare(p,"999","a"*40,case)
                self.assertEqual(scope["inputs"]["pipeline"]["prior"],PRIOR)
                data={**scope["inputs"],"operations":sorted(EXPORTS["commercial"])}
                result=analyze(data,"collections")
                self.assertEqual(result,independent(data))
                self.assertEqual(result["results"],{k:{"numerator":v,"denominator":1} for k,v in expected.items()})
            with self.assertRaises(ValueError):c.prepare(p,c.SOURCE_RUN,"a"*40,"pr")
            with self.assertRaises(ValueError):c.prepare(p,"999","a"*40,"other")
            for change in ({"run_id":"999"},{"commit":"b"*40},{"paid_inference":True},{"model_calls_replayed":1},{"qualification_sha256":"b"*64}):
                with self.assertRaises(ValueError):c.build_scope({**PRIOR,**change},"999","a"*40,"pr")
            p.write_bytes(encoded(PRIOR)+b"\n")
            with self.assertRaises(ValueError):c.prepare(p,"999","a"*40,"pr")
if __name__=="__main__":unittest.main(verbosity=2)
