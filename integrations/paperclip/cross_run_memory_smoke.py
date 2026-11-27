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
    def test_distinct_predecessor_metadata_and_memory_pin(self):
        prior={**PRIOR,"run_id":"123456","commit":"a"*40}
        pin={**c.source_pin(),"run_id":"123456","artifact_id":123,
             "commit":"a"*40,"head_sha":"b"*40,"ref":"refs/pull/42/merge",
             "memory_sha256":hashlib.sha256(encoded(prior)).hexdigest()}
        run={**RUN,"id":123456,"head_sha":"b"*40}
        art={**ART,"id":123,"workflow_run":{"id":123456}}
        c.validate_pinned_source(run,art,pin)
        self.assertEqual(c.validate_pinned_memory(prior,pin,"999","c"*40),prior)
        for bad in (dict(pin,artifact_id=True),dict(pin,ref="refs/heads/main"),
                    dict(pin,stage="commercial"),dict(pin,memory_sha256="bad")):
            with self.assertRaises(ValueError):c.validate_pin(bad)
        for bad in (dict(run,conclusion="failure"),dict(run,path="other.yml")):
            with self.assertRaises(ValueError):c.validate_pinned_source(bad,art,pin)
        with self.assertRaises(ValueError):c.validate_pinned_source(run,dict(art,expired=True),pin)
        with self.assertRaises(ValueError):c.validate_pinned_memory(prior,pin,"123456","c"*40)
        with self.assertRaises(ValueError):c.validate_pinned_memory(dict(prior,paid_inference=True),pin,"999","c"*40)
        with self.assertRaises(ValueError):c.validate_pinned_memory(dict(prior,qualification_sha256="d"*64),pin,"999","c"*40)

    def test_live_engineering_predecessor_requires_exact_owner_origin(self):
        pin={**c.source_pin(),"ref":"refs/heads/main","commit":"a"*40,"head_sha":"a"*40}
        run={**RUN,"head_sha":"a"*40,"head_branch":"main","event":"issues",
             "path":".github/workflows/paperclip-cross-run.yml","head_repository":{"full_name":c.REPO},
             "actor":{"login":"chadkhalil21-svg"},"run_attempt":1}
        self.assertEqual(c.validate_pin(pin),pin)
        c.validate_pinned_source(run,ART,pin)
        for bad in (dict(run,actor={"login":"other"}),dict(run,run_attempt=2),
                    dict(run,run_attempt=True),dict(run,head_branch="other"),
                    dict(run,event="workflow_dispatch"),dict(run,path=".github/workflows/paperclip-multidisciplinary.yml"),
                    dict(run,head_repository={"full_name":"other/repo"})):
            with self.assertRaises(ValueError):c.validate_pinned_source(bad,ART,pin)
        for bad in (dict(pin,head_sha="b"*40),dict(pin,stage="science")):
            with self.assertRaises(ValueError):c.validate_pin(bad)

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
class AuthorizedContinuationTests(unittest.TestCase):
    def test_request_reservation_scope_and_archive(self):
        import io, zipfile
        import cross_run_authorized as a
        raw_memory=encoded(PRIOR)
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,"w") as z:
            z.writestr("memory.json",raw_memory)
        raw=stream.getvalue()
        pin={**c.source_pin(),"zip_sha256":hashlib.sha256(raw).hexdigest()}
        req={"source":pin,"parameters":{"tariff_cents_kwh":70,"labor_cents_module_day":200,
             "revenue_cents_day":3500,"capital_cents_module":62000},"dois":["10.3390/w15020243"]}
        event={"action":"opened","repository":{"full_name":a.REPO},"sender":{"login":a.OWNER},
               "issue":{"number":42,"title":a.TITLE,"state":"open","user":{"login":a.OWNER},
                        "body":a.MAGIC+"\n"+encoded(req).decode()}}
        self.assertEqual(a.parse_request(event),(42,"commercial",req))
        self.assertEqual(a.archive_memory(raw,pin),raw_memory)
        scope=a.build_scope(req,PRIOR,"999","a"*40)
        self.assertEqual(a.check_scope(event,scope,"999","a"*40),("commercial",scope))
        comments=[]
        def reader(url,token,*,body=None):
            if body is not None:
                comments.append({"body":body["body"],"user":{"login":"github-actions[bot]"}})
                return {"html_url":"https://github.com/example/receipt","user":{"login":"github-actions[bot]"}}
            if url.endswith("/comments?per_page=100"):
                return comments
            return {**event["issue"],"comments":len(comments)}
        self.assertEqual(a.reserve(event,"test","999",reader=reader),("commercial",req))
        with self.assertRaises(PermissionError):a.reserve(event,"test","1000",reader=reader)
        with self.assertRaises(PermissionError):a.parse_request({**event,"sender":{"login":"other"}})
        with self.assertRaises(ValueError):a.archive_memory(raw+b"x",pin)
        changed=copy.deepcopy(scope)
        changed["inputs"]["pipeline"]["parameters"]["tariff_cents_kwh"]=71
        with self.assertRaises(ValueError):a.check_scope(event,changed,"999","a"*40)

if __name__=="__main__":unittest.main(verbosity=2)
