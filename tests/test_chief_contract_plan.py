"""Observable contract selection, data dependencies and no-repeat recovery."""
import json
import tempfile
from pathlib import Path
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
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run = lambda: m.execute_contract_mission(event(self.objective), output_dir=root)
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
