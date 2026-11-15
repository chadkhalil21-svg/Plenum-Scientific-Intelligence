"""Obvious authorized contract pairs execute without any model inference."""
import json
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
from plenum_ai import chief_contract_plan as m
from plenum_ai.chief_team_mission import preflight


def event(objective):
    return {'action':'opened','repository':{'full_name':'chadkhalil21-svg/Plenum-Scientific-Intelligence'},'issue':{'number':102,'title':'[Plenum Chief] public mission','user':{'login':'chadkhalil21-svg'},'body':m.MAGIC+'\nobjective: '+objective}}


class ObviousContractEfficiencyTests(TestCase):
    def test_single_pair_preflight_never_requests_model_dependencies_or_start(self):
        for objective in ('Review DOI 10.1038/nature14539 deposited title year and publisher', 'Inspect NOAA 8724580 station names and coordinates', 'Estimate cooling initial 358 K ambient 299 K rate 0.045 time 25'):
            with self.subTest(objective=objective):
                report=preflight(event(objective))
                self.assertTrue(report['planned_contract_mission'])
                self.assertFalse(report['planned_data_mission'])
                self.assertFalse(report['model_called'])
        report=preflight(event('Review NOAA 8724580 and DOI 10.1038/nature14539 metadata quality'))
        self.assertTrue(report['planned_data_mission'])

    def test_scholarly_pair_executes_actual_contracts_without_model_and_resumes(self):
        objective='Review DOI 10.1038/nature14539 deposited title year and publisher'
        record={'doi':'10.1038/nature14539','title':'Public deposited paper metadata','year':2015,'publisher':'Publisher'}
        calls=[]
        def read(doi,**kwargs):
            calls.append(doi)
            return record
        with tempfile.TemporaryDirectory() as d, patch.object(m,'model_plan',side_effect=AssertionError('unnecessary model')), patch.object(m,'read_crossref',side_effect=read):
            root=Path(d)
            result=m.execute_contract_mission(event(objective),output_dir=root)
            self.assertTrue(result['bounded_contracts_verified'])
            self.assertFalse(result['model_called'])
            self.assertFalse(result['chief_model_delegated'])
            self.assertEqual(result['dispatcher'],'original_chief_deterministic_public_contract_pair')
            self.assertEqual(result['inference_provenance']['provider'],'deterministic_contract_router')
            self.assertIsNone(result['inference_provenance']['model'])
            saved=json.loads((root/'chief-contract-plan-102.json').read_text())
            self.assertEqual(saved['inference']['provider'],'deterministic_contract_router')
            result=m.execute_contract_mission(event(objective),output_dir=root)
            self.assertEqual(result['new_worker_invocations'],0)
            self.assertEqual(len(calls),2)

    def test_actual_failed_noaa_doi_mission_recovers_without_model_or_repeated_tools(self):
        # Original #679's real local Qwen planner invented TWO cooling tools
        # when only NOAA and a DOI were authorized (run 43642394223).
        # Source/readback pairs are fully fixed by the original contract.
        objective='Inspect NOAA 8723214 and DOI 10.1029/2022JC018496 for Miami coastal station and bibliography metadata'
        task=event(objective)
        calls=[]
        def noaa(station):
            calls.append(('noaa',station))
            return json.dumps({'stations':[{'id':station,'name':'Miami gauge',
                                           'lat':25.8,'lng':-80.2}]}).encode()
        def crossref(doi,**kwargs):
            calls.append(('crossref',doi))
            return {'doi':doi,'title':'Public bibliography metadata',
                    'year':2022,'publisher':'Public Crossref member'}
        with (tempfile.TemporaryDirectory() as d,
              patch.object(m,'model_plan',side_effect=AssertionError('No model planner for fixed contracts')),
              patch.object(m,'fetch_noaa_metadata',side_effect=noaa),
              patch.object(m,'read_crossref',side_effect=crossref)):
            root=Path(d)
            first=m.execute_contract_mission(task,output_dir=root)
            self.assertTrue(first['bounded_contracts_verified'])
            self.assertFalse(first['model_called'])
            self.assertEqual(first['new_worker_invocations'],4)
            self.assertEqual(first['dispatcher'],'original_chief_deterministic_public_scope_contracts')
            self.assertEqual(first['inference_provenance']['provider'],'deterministic_contract_router')
            self.assertEqual(first['contract_results']['bibliography_readback']['records'],1)
            self.assertFalse(first['founder_objective_verified'])
            self.assertEqual(len(calls),3)
            second=m.execute_contract_mission(task,output_dir=root)
            self.assertEqual(second['new_worker_invocations'],0)
            self.assertEqual(second['reused_prior_verified_workers'],4)
            self.assertEqual(len(calls),3)
