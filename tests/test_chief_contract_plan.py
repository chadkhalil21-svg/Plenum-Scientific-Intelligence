"""Observable contract selection, data dependencies and no-repeat recovery."""
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch
from plenum_ai import chief_contract_plan as m


def event(objective='Review NOAA 8724580 and DOI 10.1103/PhysRevLett.116.061102 for public metadata quality'):
    return {'action':'opened','repository':{'full_name':'chadkhalil21-svg/Plenum-Scientific-Intelligence'},'issue':{'number':101,'title':'[Plenum Chief] public mission','user':{'login':'chadkhalil21-svg'},'body':m.MAGIC+'\nobjective: '+objective}}


def plan(scope):
    steps=[]
    if scope['station_ids']:
        steps.extend([{'tool':'noaa_metadata'}, {'tool':'station_validation','input_from':'noaa_metadata'}])
    if scope['dois']:
        steps.extend([{'tool':'crossref_metadata'}, {'tool':'bibliography_readback','input_from':'crossref_metadata'}])
    if scope.get('cooling'):
        steps.extend([{'tool':'cooling_solution'}, {'tool':'cooling_readback','input_from':'cooling_solution'}])
    return {'steps':steps}


class ContractPlanTests(TestCase):
    def test_original_mission_intake_accepts_unseen_combinations_without_literal_goal_gate(self):
        from plenum_ai.chief_team_mission import preflight
        for objective, expected in [('Review DOI 10.5555/12345678 for bibliography quality', ['crossref_metadata','bibliography_readback']), ('Inspect NOAA 8724580 coordinates for malformed records', ['noaa_metadata','station_validation'])]:
            with self.subTest(objective=objective):
                p=preflight(event(objective))
                self.assertTrue(p['planned_contract_mission'])
                self.assertEqual(p['expected_team'],expected)
                self.assertFalse(p['model_called'])
        bad=event();bad['issue']['user']['login']='intruder'
        with self.assertRaises(PermissionError): m.parse_contract_mission(bad)

    def test_unknown_missing_duplicate_or_reversed_contracts_fail_before_tools(self):
        scope=m.parse_contract_mission(event())['scope']
        good=plan(scope)
        for steps in ([{'tool':'shell'}],good['steps']+good['steps'][:1],list(reversed(good['steps'])),good['steps'][:-1]):
            with self.subTest(steps=steps), self.assertRaises(ValueError):
                m.validate_plan({'steps':steps},scope)
        with self.assertRaises(ValueError): m.validate_plan({**good,'url':'https://evil.test'},scope)

    def test_real_noaa_validator_and_separate_bibliography_readback_then_resume(self):
        calls=[]
        def noaa(station):
            calls.append(('noaa',station))
            return json.dumps({'stations':[{'id':station,'name':'Gauge','lat':25,'lng':-80}]}).encode()
        def crossref(doi,**kwargs):
            calls.append(('crossref',doi))
            return {'doi':doi,'title':'Public deposited scholarly metadata','year':2020,'publisher':'Publisher','source':'Crossref member-deposited metadata via HTTPS','retrieval_kind':'public_read_only'}
        with tempfile.TemporaryDirectory() as d, patch.object(m,'fetch_noaa_metadata',side_effect=noaa), patch.object(m,'read_crossref',side_effect=crossref):
            root=Path(d)
            first=m.execute_contract_mission(event(),output_dir=root,planner=plan)
            self.assertTrue(first['bounded_contracts_verified'])
            self.assertFalse(first['founder_objective_verified'])
            self.assertEqual(first['new_worker_invocations'],4)
            self.assertEqual(first['contract_results']['station_validation']['total_rows'],1)
            second=m.execute_contract_mission(event(),output_dir=root,planner=lambda _:self.fail('replanned'))
            self.assertEqual(second['new_worker_invocations'],0)
            self.assertEqual(second['reused_prior_verified_workers'],4)
            self.assertEqual(len(calls),3)
            source=root/'workers/noaa_metadata/result.json'
            source.write_text('{}')
            with self.assertRaises(ValueError): m.execute_contract_mission(event(),output_dir=root)

    def test_failed_readback_resumes_without_duplicate_source_or_validation(self):
        def noaa(station):
            return json.dumps({'stations':[{'id':station,'name':'Gauge','lat':25,'lng':-80}]}).encode()
        record={'doi':'10.1103/physrevlett.116.061102','title':'Public deposited scholarly metadata','year':2020,'publisher':'Publisher'}
        with tempfile.TemporaryDirectory() as d, patch.object(m,'fetch_noaa_metadata',side_effect=noaa), patch.object(m,'read_crossref',side_effect=[record,RuntimeError('temporary')]):
            with self.assertRaises(RuntimeError): m.execute_contract_mission(event(),output_dir=Path(d),planner=plan)
            with patch.object(m,'fetch_noaa_metadata',side_effect=AssertionError('source repeated')), patch.object(m,'read_crossref',return_value=record):
                resumed=m.execute_contract_mission(event(),output_dir=Path(d))
            self.assertEqual(resumed['new_worker_invocations'],1)
            self.assertEqual(resumed['reused_prior_verified_workers'],3)
            self.assertTrue(resumed['bounded_contracts_verified'])

    def test_original_native_retry_accepts_actual_contract_failure_and_rejects_tamper(self):
        from plenum_ai.chief_retry_gate import inspect_retry
        from plenum_ai.chief_team_mission import execute
        original=event()
        record={'doi':'10.1103/physrevlett.116.061102','title':'Public deposited scholarly metadata','year':2020,'publisher':'Publisher'}
        run={'workflow_run':{'id':987,'name':'Plenum Chief | Founder Model-Directed Specialist Command','event':'issues','status':'completed','conclusion':'failure','run_attempt':1,'actor':{'login':'chadkhalil21-svg'},'repository':original['repository']}}
        with tempfile.TemporaryDirectory() as d, patch.object(m,'model_plan',side_effect=lambda objective,scope:plan(scope)), patch.object(m,'fetch_noaa_metadata',side_effect=lambda station:json.dumps({'stations':[{'id':station,'name':'Gauge','lat':25,'lng':-80}]}).encode()), patch.object(m,'read_crossref',side_effect=[record,RuntimeError('temporary')]):
            root=Path(d)
            failed=execute(original,output_dir=root)
            self.assertEqual(failed['status'],'BLOCKED_CONTRACT_EXECUTION')
            (root/'chief-result-101.json').write_text(json.dumps(failed))
            issue={**original['issue'],'state':'open'}
            decision=inspect_retry(run,root,issue)
            self.assertEqual(decision['status'],'ELIGIBLE_NATIVE_RETRY_ONCE')
            self.assertEqual(decision['saved_verified_workers'],3)
            cp=root/'chief-checkpoint-101.json'
            saved=json.loads(cp.read_text())
            saved['results']['bibliography_readback']['attempt']=2
            cp.write_text(json.dumps(saved))
            self.assertNotEqual(inspect_retry(run,root,issue)['status'],'ELIGIBLE_NATIVE_RETRY_ONCE')

    def test_new_parameterized_cooling_contract_uses_solver_and_independent_formula(self):
        objective='Estimate cooling initial 345 K ambient 292 K rate 0.07 time 18'
        with tempfile.TemporaryDirectory() as d:
            r=m.execute_contract_mission(event(objective),output_dir=Path(d),planner=plan)
            self.assertTrue(r['bounded_contracts_verified'])
            self.assertEqual(r['new_worker_invocations'],2)
            self.assertAlmostEqual(r['contract_results']['cooling_solution']['observed_kelvin'],307.0336634044878,places=7)
            self.assertLess(r['contract_results']['cooling_readback']['absolute_error_kelvin'],1e-6)
            self.assertFalse(r['founder_objective_verified'])

    def test_scholarly_publisher_noun_allowed_without_authorizing_publish_actions(self):
        objective='Review DOI 10.1038/nature14539 and 10.1126/science.1102896 deposited title year and publisher'
        scope=m.parse_contract_mission(event(objective))['scope']
        self.assertEqual(scope['dois'],['10.1038/nature14539','10.1126/science.1102896'])
        for verb in ('publish','publishes','published','publishing','republish'):
            with self.subTest(verb=verb), self.assertRaises(PermissionError):
                m.parse_contract_mission(event(verb+' DOI 10.1038/nature14539 publisher metadata'))

    def test_no_identifier_invention_or_model_endpoint_expansion(self):
        for objective in ('Inspect public records with no identifier', 'Inspect DOI 10.1/bad for metadata quality', 'Inspect NOAA 8724580 and http internal metadata'):
            with self.subTest(objective=objective), self.assertRaises((ValueError,PermissionError)):
                m.parse_contract_mission(event(objective))
        with patch.dict('os.environ',{},clear=True), self.assertRaises(PermissionError):
            m.model_plan('Public metadata review',{'station_ids':['8724580'],'dois':[]})

    def test_first_readonly_contract_failure_can_resume_once_without_sibling(self):
        from plenum_ai.chief_retry_gate import inspect_retry
        from plenum_ai.chief_team_mission import execute
        original=event()
        run={'workflow_run':{'id':987,'name':'Plenum Chief | Founder Model-Directed Specialist Command','event':'issues','status':'completed','conclusion':'failure','run_attempt':1,'actor':{'login':'chadkhalil21-svg'},'repository':original['repository']}}
        issue={**original['issue'],'state':'open'}
        record={'doi':'10.1103/physrevlett.116.061102','title':'Public metadata','year':2020,'publisher':'Publisher'}
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            with patch.object(m,'fetch_noaa_metadata',side_effect=RuntimeError('temporary')):
                failed=execute(original,output_dir=root)
            self.assertEqual(failed['status'],'BLOCKED_CONTRACT_EXECUTION')
            (root/'chief-result-101.json').write_text(json.dumps(failed))
            verdict=inspect_retry(run,root,issue)
            self.assertEqual(verdict['status'],'ELIGIBLE_NATIVE_RETRY_ONCE')
            self.assertEqual(verdict['saved_verified_workers'],0)
            with patch.object(m,'fetch_noaa_metadata',return_value=json.dumps({'stations':[{'id':'8724580','name':'Gauge','lat':25,'lng':-80}]}).encode()), patch.object(m,'read_crossref',return_value=record):
                resumed=m.execute_contract_mission(original,output_dir=root)
            self.assertTrue(resumed['bounded_contracts_verified'])
            self.assertEqual(resumed['new_worker_invocations'],4)
            self.assertNotEqual(inspect_retry(run,root,issue)['status'],'ELIGIBLE_NATIVE_RETRY_ONCE')

class ContractRecoveryEvidenceTests(TestCase):
    objective = "Check cooling initial 370 K ambient 287 K rate 0.12 time 9 and verify the final temperature"

    def test_failed_solver_recovers_with_distinct_method_and_restart_reuses_verified_pair(self):
        import math

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def run():
                return m.execute_contract_mission(event(self.objective), output_dir=root)

            with patch("scipy.integrate.solve_ivp", side_effect=RuntimeError("fixture: solver unavailable")) as primary:
                report = run()
            primary.assert_called_once()
            self.assertTrue(report["independent_verified"])
            solution = report["contract_results"]["cooling_solution"]
            self.assertEqual(solution["method"], "expm")
            self.assertAlmostEqual(solution["observed_kelvin"], 287 + 83 * math.exp(-1.08), places=6)
            checkpoint = json.loads((root / "chief-checkpoint-101.json").read_text())["results"]
            readback = json.loads((root / "workers/cooling_readback/result.json").read_text())
            self.assertEqual(readback["input_sha256"], checkpoint["cooling_solution"]["sha256"])
            with patch.object(m, "run_contract", side_effect=AssertionError("duplicated work")):
                resumed = run()
            self.assertTrue(resumed["independent_verified"])
            self.assertEqual(resumed["new_worker_invocations"], 0)
            self.assertEqual(resumed["reused_prior_verified_workers"], 2)

    def test_valid_file_hash_cannot_substitute_for_correct_producer_binding(self):
        from plenum_ai.mission_checkpoint import artifact_digest

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            m.execute_contract_mission(event(self.objective), output_dir=root)
            name = "workers/cooling_readback/result.json"
            path = root / name
            readback = json.loads(path.read_text())
            readback["input_sha256"] = "0" * 64
            path.write_text(json.dumps(readback, sort_keys=True))
            checkpoint = root / "chief-checkpoint-101.json"
            state = json.loads(checkpoint.read_text())
            state["results"]["cooling_readback"]["sha256"] = artifact_digest(root, name)
            checkpoint.write_text(json.dumps(state))
            with self.assertRaises(ValueError):
                m.execute_contract_mission(event(self.objective), output_dir=root)

    def test_unsuccessful_integrator_result_uses_alternative_solver(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch("scipy.integrate.solve_ivp", return_value=SimpleNamespace(success=False)):
                result = m.execute_contract_mission(event(self.objective), output_dir=Path(directory))
            self.assertEqual(result["contract_results"]["cooling_solution"]["method"], "expm")
            self.assertTrue(result["bounded_contracts_verified"])


    def test_false_success_recovers_before_persisting_invalid_producer(self):
        import numpy as np
        for value in (float("nan"), float("inf"), 999.0):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                with patch("scipy.integrate.solve_ivp", return_value=SimpleNamespace(
                        success=True, y=np.array([[370.0, value]]))) as primary:
                    result = m.execute_contract_mission(event(self.objective), output_dir=root)
                primary.assert_called_once()
                self.assertTrue(result["bounded_contracts_verified"])
                self.assertEqual(result["new_worker_invocations"], 3)
                producer = json.loads((root / "workers/cooling_solution/result.json").read_text())
                self.assertEqual(producer["result"]["method"], "expm")
                self.assertEqual(producer["recovery"]["reason"], "CoolingQualityFailure")
                checkpoint = json.loads((root / "chief-checkpoint-101.json").read_text())["results"]
                self.assertEqual(checkpoint["cooling_solution"]["attempt"], 2)
                self.assertTrue(checkpoint["cooling_solution"]["verified"])

    def test_both_invalid_producers_exhaust_budget_and_leave_no_accepted_artifact(self):
        import numpy as np
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch("scipy.integrate.solve_ivp", return_value=SimpleNamespace(
                    success=True, y=np.array([[370.0, 999.0]]))) as primary, patch.object(
                    m, "cooling_matrix_solution", return_value={"observed_kelvin": 0.0}) as alternate:
                with self.assertRaises(m.CoolingQualityFailure):
                    m.execute_contract_mission(event(self.objective), output_dir=root)
            primary.assert_called_once()
            alternate.assert_called_once()
            self.assertFalse((root / "workers/cooling_solution/result.json").exists())
            self.assertFalse((root / "workers/cooling_readback/result.json").exists())
            saved = json.loads((root / "chief-checkpoint-101.json").read_text())["results"]
            self.assertEqual(saved["cooling_solution"]["attempt"], 2)
            self.assertFalse(saved["cooling_solution"]["verified"])
            with patch.object(m, "run_contract", side_effect=AssertionError("third attempt")):
                with self.assertRaisesRegex(ValueError, "Two-attempt ceiling"):
                    m.execute_contract_mission(event(self.objective), output_dir=root)


class GoalGraphAcceptanceTests(TestCase):
    def test_approved_graph_orders_multiple_dependencies_and_refuses_cycles_or_expansion(self):
        from plenum_ai.chief_team_mission import validate_specialist_graph
        approved = {
            "research": {"specialist":"research-specialist", "depends_on":[], "acceptance":"source_identity"},
            "science": {"specialist":"scientific-specialist", "depends_on":[], "acceptance":"numeric_result"},
            "review": {"specialist":"verification-specialist", "depends_on":["research","science"], "acceptance":"both_results"},
        }
        nodes = [{"id":name, **approved[name]} for name in ("review","research","science")]
        self.assertEqual([x["id"] for x in validate_specialist_graph(nodes, approved)],
                         ["research","science","review"])
        invalid = [
            [{**nodes[0], "acceptance":"always_pass"}, *nodes[1:]],
            [{**nodes[0], "depends_on":["research"]}, *nodes[1:]],
            [{**nodes[0], "specialist":"unknown"}, *nodes[1:]],
            nodes[:-1],
            [nodes[0],nodes[1],nodes[1]],
        ]
        for proposed in invalid:
            with self.subTest(proposed=proposed), self.assertRaises(ValueError):
                validate_specialist_graph(proposed, approved)
        cycle = {**approved, "research":{**approved["research"], "depends_on":["review"]}}
        with self.assertRaisesRegex(ValueError, "Cyclic"):
            validate_specialist_graph([{"id":name, **value} for name,value in cycle.items()], cycle)

    def test_wrong_doi_never_becomes_accepted_producer_and_resume_uses_correct_source(self):
        objective = "Review DOI 10.1038/nature14539 deposited title year and publisher"
        good = {"doi":"10.1038/nature14539","title":"Public metadata","year":2015,"publisher":"Publisher"}
        bad = {**good,"doi":"10.1038/wrong"}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(m,"read_crossref",return_value=bad) as provider:
                with self.assertRaisesRegex(ValueError,"trusted acceptance criterion"):
                    m.execute_contract_mission(event(objective),output_dir=root)
            provider.assert_called_once()
            saved = json.loads((root/"chief-checkpoint-101.json").read_text())["results"]
            self.assertFalse(saved["crossref_metadata"]["verified"])
            self.assertFalse((root/"workers/crossref_metadata/result.json").exists())
            self.assertNotIn("bibliography_readback",saved)
            with patch.object(m,"read_crossref",return_value=good):
                report = m.execute_contract_mission(event(objective),output_dir=root)
            self.assertTrue(report["bounded_contracts_verified"])
            self.assertEqual([node["id"] for node in report["goal_graph"]],
                             ["crossref_metadata","bibliography_readback"])
            self.assertEqual(report["goal_graph"][1]["depends_on"],["crossref_metadata"])
            receipt = json.loads((root/"workers/crossref_metadata/result.json").read_text())
            self.assertEqual(receipt["acceptance_criterion"],"exact_doi_and_required_metadata")

    def test_hash_matching_restored_artifact_cannot_replace_acceptance_criterion(self):
        from plenum_ai.mission_checkpoint import artifact_digest
        objective = "Estimate cooling initial 345 K ambient 292 K rate 0.07 time 18"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            m.execute_contract_mission(event(objective),output_dir=root)
            name = "workers/cooling_solution/result.json"
            path = root/name
            artifact = json.loads(path.read_text())
            artifact["acceptance_criterion"] = "always_pass"
            path.write_text(json.dumps(artifact))
            checkpoint = root/"chief-checkpoint-101.json"
            saved = json.loads(checkpoint.read_text())
            saved["results"]["cooling_solution"]["sha256"] = artifact_digest(root,name)
            checkpoint.write_text(json.dumps(saved))
            with patch.object(m,"run_contract",side_effect=AssertionError("duplicate dispatch")):
                with self.assertRaisesRegex(ValueError,"Stored acceptance criterion changed"):
                    m.execute_contract_mission(event(objective),output_dir=root)


class IntegratedEvidenceGoalTests(TestCase):
    objective = "Evidence report NOAA 9414290 and cooling initial 364 K ambient 289 K rate 0.08 time 17"

    def test_multi_input_report_is_a_complete_bounded_deliverable_and_resumes(self):
        def noaa(station):
            return json.dumps({"stations":[{"id":station,"name":"San Francisco","lat":37.8,"lng":-122.4}]}).encode()
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with patch.object(m,"fetch_noaa_metadata",side_effect=noaa) as fetch:
                report=m.execute_contract_mission(event(self.objective),output_dir=root)
            fetch.assert_called_once()
            self.assertTrue(report["founder_objective_verified"])
            self.assertFalse(report["new_general_agent_capability_claimed"])
            self.assertEqual(report["new_worker_invocations"],5)
            self.assertEqual(report["bounded_founder_goal_evidence"]["status"],"VERIFIED_FULL_BOUNDED_PUBLIC_OBJECTIVE")
            final=json.loads((root/"workers/evidence_report/result.json").read_text())
            self.assertEqual(set(final["input_digests"]),{"noaa_metadata","station_validation","cooling_solution","cooling_readback"})
            self.assertEqual(set(final["result"]["sections"]),{"stations","cooling"})
            self.assertEqual(final["result"]["sections"]["stations"]["records"][0]["id"],"9414290")
            self.assertLess(final["result"]["sections"]["cooling"]["readback"]["absolute_error_kelvin"],1e-6)
            with patch.object(m,"run_contract",side_effect=AssertionError("repeated work")):
                resumed=m.execute_contract_mission(event(self.objective),output_dir=root)
            self.assertTrue(resumed["founder_objective_verified"])
            self.assertEqual(resumed["new_worker_invocations"],0)
            self.assertEqual(resumed["reused_prior_verified_workers"],5)

    def test_report_tamper_with_rehashed_artifact_still_fails_acceptance(self):
        from plenum_ai.mission_checkpoint import artifact_digest
        objective="Evidence report DOI 10.1038/nature14539"
        record={"doi":"10.1038/nature14539","title":"Public bibliographic metadata","year":2015,"publisher":"Publisher"}
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with patch.object(m,"read_crossref",return_value=record):
                report=m.execute_contract_mission(event(objective),output_dir=root)
            self.assertTrue(report["founder_objective_verified"])
            rel="workers/evidence_report/result.json"
            path=root/rel
            artifact=json.loads(path.read_text())
            artifact["result"]["sections"]["bibliography"]["records"][0]["title"]="Invented finding"
            path.write_text(json.dumps(artifact))
            cp=root/"chief-checkpoint-101.json"
            saved=json.loads(cp.read_text())
            saved["results"]["evidence_report"]["sha256"]=artifact_digest(root,rel)
            cp.write_text(json.dumps(saved))
            with patch.object(m,"run_contract",side_effect=AssertionError("repeated work")):
                with self.assertRaisesRegex(ValueError,"trusted acceptance criterion"):
                    m.execute_contract_mission(event(objective),output_dir=root)

    def test_report_goal_refuses_unrecognized_or_repeated_requirements(self):
        for objective in ("Evidence report NOAA 9414290 and predict next hurricane",
                          "Evidence report NOAA 9414290 and NOAA 9447130",
                          "Evidence report DOI 10.1038/nature14539 and make a discovery"):
            with self.subTest(objective=objective), self.assertRaises(ValueError):
                m.parse_contract_mission(event(objective))


class CommercialEvidenceHandoffTests(TestCase):
    objective="Evidence report American Rider public health and cooling initial 352 K ambient 291 K rate 0.04 time 15"

    def test_actual_existing_monitor_integrates_mixed_availability_with_science(self):
        from plenum_ai import business_public_watch as watch
        calls=[]
        def probe(target):
            calls.append(target.name)
            if target.name=="platform":
                return False,"non_200_http",503
            return True,"verified_read",200
        original_run=watch.run
        def monitor():
            return original_run(probe_fn=probe,sleep_fn=lambda _:None)
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with patch.object(watch,"run",side_effect=monitor) as worker:
                report=m.execute_contract_mission(event(self.objective),output_dir=root)
            worker.assert_called_once()
            self.assertEqual(calls,["corporate","corporate","platform","platform","platform","public_server","public_server"])
            self.assertTrue(report["founder_objective_verified"])
            self.assertEqual(report["new_worker_invocations"],5)
            final=json.loads((root/"workers/evidence_report/result.json").read_text())
            self.assertEqual(set(final["input_digests"]),{"business_readback","business_review","cooling_solution","cooling_readback"})
            review=final["result"]["sections"]["business"]["review"]
            self.assertEqual(review["verified_endpoints"],2)
            self.assertEqual(review["unverified_endpoints"],1)
            self.assertFalse(review["commercial_readiness_verified"])
            self.assertFalse(review["all_endpoints_verified"])
            with patch.object(watch,"run",side_effect=AssertionError("repeated accepted observation")):
                recovered=m.execute_contract_mission(event(self.objective),output_dir=root)
            self.assertEqual(recovered["reused_prior_verified_workers"],5)
            self.assertTrue(recovered["founder_objective_verified"])

    def test_business_scope_does_not_accept_arbitrary_url_or_readiness_claim(self):
        for objective in ("Evidence report American Rider public health and assert launch readiness",
                          "Evidence report American Rider public health and American Rider public health",
                          "Evidence report https american Rider public health"):
            with self.subTest(objective=objective),self.assertRaises((ValueError,PermissionError)):
                m.parse_contract_mission(event(objective))

    def test_business_verifier_rejects_incomplete_and_unverified_green_claims(self):
        from plenum_ai import business_public_watch as watch
        good=watch.run(probe_fn=lambda _: (True,"verified_read",200),sleep_fn=lambda _:None)
        self.assertTrue(m.review_business_status(good)["all_endpoints_verified"])
        import copy
        for field,value in (("independent_gets",1),("attempts",1),("external_actions_executed",True)):
            bad=copy.deepcopy(good)
            bad["reports"][0][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):
                m.review_business_status(bad)
        with self.assertRaises(ValueError):
            m.review_business_status({**good,"asserts_commercial_readiness":True})


class DynamicPaperHandoffTests(TestCase):
    objective="Evidence report Survey public photonic computing papers and cooling initial 342 K ambient 290 K rate 0.05 time 14"

    def discovery(self):
        query="Survey public photonic computing papers"
        return {"schema":"plenum-public-horizon-snapshot-v1","topic":query,
                "category":"journals","independent_breakthrough_verified":False,
                "records":[{"source":"crossref_journals","category":"journals",
                    "title":"Photonic computation architectures","url":"https://doi.org/10.1000/one",
                    "independent_fact_check_complete":False},
                    {"source":"crossref_journals","category":"journals",
                    "title":"Photonic computing devices","url":"https://doi.org/10.1000/two",
                    "independent_fact_check_complete":False}]}

    def test_discovered_dois_flow_to_actual_readback_and_final_report(self):
        discovery=self.discovery()
        selected=frozenset({"10.1000/one","10.1000/two"})
        titles={r["url"].split("doi.org/")[1]:r["title"] for r in discovery["records"]}
        calls=[]
        def read(doi,*,approved_dois):
            self.assertEqual(approved_dois,selected)
            calls.append(doi)
            return {"doi":doi,"title":titles[doi],"year":2024,"publisher":"Public publisher"}
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with patch("plenum_ai.world_horizon.scan_horizon",return_value=discovery) as survey,patch.object(m,"read_crossref",side_effect=read):
                result=m.execute_contract_mission(event(self.objective),output_dir=root)
            survey.assert_called_once_with(discovery["topic"],category="journals",online=True)
            self.assertEqual(calls,["10.1000/one","10.1000/two"])
            self.assertTrue(result["founder_objective_verified"])
            self.assertEqual(result["new_worker_invocations"],5)
            final=json.loads((root/"workers/evidence_report/result.json").read_text())
            self.assertEqual(set(final["input_digests"]),{"paper_discovery","paper_readback","cooling_solution","cooling_readback"})
            receipt=json.loads((root/"workers/paper_readback/result.json").read_text())
            cp=json.loads((root/"chief-checkpoint-101.json").read_text())
            self.assertEqual(receipt["input_sha256"],cp["results"]["paper_discovery"]["sha256"])
            self.assertEqual(set(final["result"]["sections"]["papers"]["readback"]),selected)
            with patch.object(m,"run_contract",side_effect=AssertionError("repeated accepted work")):
                replay=m.execute_contract_mission(event(self.objective),output_dir=root)
            self.assertTrue(replay["founder_objective_verified"])
            self.assertEqual(replay["reused_prior_verified_workers"],5)

    def test_discovery_rejects_nonmatching_and_non_doi_input_before_readback(self):
        scope=m.parse_contract_mission(event(self.objective))["scope"]
        for field,value in (("url","https://example.org/"),("url","https://doi.org/10.1000/../bad?x=1"),
                            ("title","Unrelated vegetation survey")):
            bad=self.discovery()
            bad["records"][0][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):
                m.selected_paper_ids(scope,bad)
        with self.assertRaises(ValueError):
            m.parse_contract_mission(event("Evidence report Survey public photonic computing papers and predict a discovery"))



class IndependentContractReadbackTests(TestCase):
    def test_actual_artifact_readback_rejects_rehashed_wrong_dependency(self):
        from plenum_ai.ambient_quality_insights import verify_contract_mission_artifacts
        from plenum_ai.mission_checkpoint import artifact_digest
        objective="Evidence report cooling initial 350 K ambient 290 K rate 0.1 time 12"
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            result=m.execute_contract_mission(event(objective),output_dir=root)
            self.assertTrue(result["founder_objective_verified"])
            with patch.object(m,"run_contract",side_effect=AssertionError("replayed worker")):
                self.assertTrue(verify_contract_mission_artifacts(result,root))
            rel="workers/evidence_report/result.json"
            final=root/rel
            record=json.loads(final.read_text())
            record["input_digests"]["cooling_solution"]="0"*64
            final.write_text(json.dumps(record))
            cp=root/"chief-checkpoint-101.json"
            saved=json.loads(cp.read_text())
            saved["results"]["evidence_report"]["sha256"]=artifact_digest(root,rel)
            cp.write_text(json.dumps(saved))
            self.assertFalse(verify_contract_mission_artifacts(result,root))
            self.assertFalse(verify_contract_mission_artifacts({**result,"objective":objective+" and NOAA 8724580"},root))

